import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from toktopus.adapters.opencode_current import read_current_schema
from toktopus.adapters.pi import PiAgentAdapter
from toktopus.core.collector import LocalCollector
from toktopus.core.history import HistoryStore, findings
from toktopus.core.native_events import read_native_events
from toktopus.core.trace_import import import_otlp


class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = HistoryStore(self.root / 'history.db')

    def test_repoll_updates_totals_without_adding_and_updates_event_status(self):
        telemetry = dict(session_id='s', model_name='m', total_tokens=10, recent_steps=[dict(index=1, type='TOOL_CALL', tools=['read'], status='OBSERVED')])
        self.store.record('claude', telemetry)
        telemetry['total_tokens'] = 15
        telemetry['recent_steps'][0]['status'] = 'ERROR'
        self.store.record('claude', telemetry)
        self.assertEqual(self.store.sessions()[0]['snapshot']['total_tokens'], 15)
        self.assertEqual(len(self.store.timeline('claude', 's')), 1)
        self.assertEqual(self.store.timeline('claude', 's')[0]['status'], 'ERROR')

    def test_privacy_allowlist_omits_content(self):
        self.store.record('codex', dict(session_id='s', prompt='PRIVATE', recent_steps=[dict(index=1, tools=['read'], arguments='PRIVATE', output='PRIVATE', status='ERROR')]))
        self.assertNotIn('PRIVATE', json.dumps(self.store.sessions()) + json.dumps(self.store.timeline('codex', 's')))

    def test_search_is_literal_and_parameterized(self):
        self.store.record('claude', dict(session_id='s', model_name='m'))
        self.assertEqual(len(self.store.sessions('claude')), 1)
        self.assertEqual(self.store.sessions("%' OR 1=1 --"), [])

    def test_retention_removes_orphaned_events(self):
        with patch('toktopus.core.history.MAX_SESSIONS', 1):
            self.store.record('claude', dict(session_id='a', recent_steps=[dict(index=1)]))
            self.store.record('claude', dict(session_id='b'))
        self.assertEqual(len(self.store.sessions()), 1)
        self.assertEqual(self.store.timeline('claude', 'a'), [])

    def test_failure_and_repeat_checks_are_evidence_based(self):
        events = [dict(tools=['read'], status='ERROR')] * 3
        failures, repeated = findings(events)
        self.assertEqual(failures, {'read': 3})
        self.assertEqual(repeated, ['read'])
        self.assertEqual(findings([dict(tools=['read'], status='OBSERVED')])[0], {})

    def test_pi_no_source_has_no_fake_activity(self):
        adapter = PiAgentAdapter()
        adapter.pi_dirs = [self.root / 'absent']
        result = adapter.get_session_telemetry()
        self.assertEqual(result['total_tokens'], 0)
        self.assertEqual(result['recent_steps'], [])
        self.assertEqual(result['recent_steps_tokens'], [])

    def test_native_claude_pairs_tool_failures_and_skips_bad_lines(self):
        path = self.root / 'claude.jsonl'
        rows = [dict(message=dict(content=[dict(type='tool_use', id='c', name='Read', input='PRIVATE')])), dict(message=dict(content=[dict(type='tool_result', tool_use_id='c', is_error=True, content='PRIVATE')]))]
        path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n{bad')
        events, skipped = read_native_events(path, 'claude')
        self.assertEqual(skipped, 1)
        self.assertEqual(events[0]['status'], 'ERROR')
        self.assertNotIn('PRIVATE', json.dumps(events))

    def test_codex_custom_tools_pair_with_exit_evidence(self):
        path = self.root / 'codex.jsonl'
        payloads = [dict(type='custom_tool_call', call_id='c', name='apply_patch'), dict(type='custom_tool_call_output', call_id='c', output='Process exited with code 1\nPRIVATE')]
        path.write_text('\n'.join(json.dumps(dict(type='response_item', payload=p)) for p in payloads))
        events, _ = read_native_events(path, 'codex')
        self.assertEqual(events[0]['status'], 'ERROR')
        self.assertNotIn('PRIVATE', json.dumps(events))

    def otlp(self, spans):
        path = self.root / 'trace.json'
        path.write_text(json.dumps(dict(resourceSpans=[dict(resource=dict(attributes=[dict(key='service.name', value=dict(stringValue='local'))]), scopeSpans=[dict(spans=spans)])])))
        return path

    def test_otlp_import_deduplicates_and_keeps_parent_duration(self):
        span = dict(traceId='trace', spanId='span', parentSpanId='parent', startTimeUnixNano='1000000000', endTimeUnixNano='3000000000', status=dict(code=2), attributes=[dict(key='gen_ai.prompt', value=dict(stringValue='PRIVATE'))])
        path = self.otlp([span])
        self.assertEqual(import_otlp(path, self.store), 1)
        import_otlp(path, self.store)
        events = self.store.timeline('otel:local', 'trace')
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['duration_sec'], 2)
        self.assertEqual(events[0]['parent_id'], 'parent')
        self.assertEqual(events[0]['status'], 'ERROR')
        self.assertNotIn('PRIVATE', json.dumps(events))
        self.assertIsNone(self.store.sessions()[0]['snapshot']['total_tokens'])

    def test_invalid_import_does_not_partially_write(self):
        path = self.otlp([dict(traceId='a', spanId='b'), dict(traceId='a')])
        with self.assertRaises(ValueError):
            import_otlp(path, self.store)
        self.assertEqual(self.store.sessions(), [])

    def test_import_rejects_negative_duration(self):
        with self.assertRaises(ValueError):
            import_otlp(self.otlp([dict(traceId='a', spanId='b', startTimeUnixNano='10', endTimeUnixNano='1')]), self.store)

    def test_malformed_otlp_shapes_fail_cleanly(self):
        path = self.root / 'bad.json'
        for resource in (None, [], {'resource': None}, {'scopeSpans': [None]}, {'scopeSpans': [{'spans': [None]}]}):
            path.write_text(json.dumps({'resourceSpans': [resource]}))
            with self.subTest(resource=resource), self.assertRaises(ValueError):
                import_otlp(path, self.store)

    def test_collector_caches_and_isolates_reader_failures(self):
        from unittest.mock import Mock
        good = Mock()
        good.get_session_telemetry.return_value = {'session_id': 'good'}
        bad = Mock()
        bad.get_session_telemetry.side_effect = OSError('unavailable')
        collector = LocalCollector()
        collector.adapters = {'claude': good, 'codex': bad}
        with patch('toktopus.core.collector.time.monotonic', return_value=10):
            collector.poll('claude')
            collector.poll('claude')
            self.assertEqual(collector.poll('codex')['data_status'], 'error')
        good.get_session_telemetry.assert_called_once()
        self.assertEqual(collector.poll('claude', force=True)['session_id'], 'good')

    def test_current_opencode_schema_reads_tools_and_usage_without_modifying_db(self):
        path = self.root / 'opencode.db'
        with closing(sqlite3.connect(path)) as db, db:
            db.executescript('CREATE TABLE session(id TEXT, title TEXT, time_created INT, time_updated INT); CREATE TABLE message(id TEXT, session_id TEXT, time_created INT, data TEXT); CREATE TABLE part(id TEXT, message_id TEXT, time_created INT, data TEXT);')
            db.execute('INSERT INTO session VALUES (?, ?, ?, ?)', ('s', 'task', 1000, 2000))
            db.execute('INSERT INTO message VALUES (?, ?, ?, ?)', ('m', 's', 1000, json.dumps(dict(role='assistant', modelID='test', tokens=dict(input=10, output=5, reasoning=2, cache=dict(read=4, write=1))))))
            db.execute('INSERT INTO part VALUES (?, ?, ?, ?)', ('p', 'm', 1500, json.dumps(dict(type='tool', tool='read', state=dict(status='error', input='PRIVATE', error='PRIVATE')))))
        before = path.read_bytes()
        result = read_current_schema(path)
        self.assertEqual(result['session_id'], 's')
        self.assertEqual(result['total_tokens'], 22)
        self.assertEqual(result['recent_steps'][0]['status'], 'ERROR')
        self.assertFalse(result['current_context_available'])
        self.assertNotIn('PRIVATE', json.dumps(result))
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(read_current_schema(path, 'missing')['data_status'], 'no-session')

    def test_live_navigation_health_diagnostics_history_and_quit(self):
        from contextlib import ExitStack
        from unittest.mock import Mock

        from rich.console import Console

        from toktopus import cli
        collector = Mock()
        collector.adapters = {}
        collector.poll.return_value = dict(session_id='s', model_name='Unknown', agent_name='Codex', total_tokens=0)
        collector.poll_detected.return_value = {'codex': collector.poll.return_value}
        output = Console(file=io.StringIO(), width=100, height=40)
        with ExitStack() as stack:
            stack.enter_context(patch.object(cli, 'console', output))
            stack.enter_context(patch.object(cli, 'load_config', return_value={'active_agent': 'codex'}))
            stack.enter_context(patch.object(cli, 'LocalCollector', return_value=collector))
            stack.enter_context(patch.object(cli, 'HistoryStore', return_value=self.store))
            stack.enter_context(patch.object(cli, 'get_system_telemetry', return_value={}))
            stack.enter_context(patch.object(cli, 'update_pet'))
            stack.enter_context(patch.object(cli, 'load_model_health', return_value={'rows': [], 'stale': True}))
            stack.enter_context(patch.object(cli, 'init_keyboard'))
            restore = stack.enter_context(patch.object(cli, 'restore_keyboard'))
            live = stack.enter_context(patch.object(cli, 'Live'))
            stack.enter_context(patch.object(cli, 'get_pressed_key', side_effect=['h', 'd', 'j', 'n', 'p', ']', '\r', 'n', 'p', 'j', 'q']))
            stack.enter_context(patch('sys.stdin.isatty', return_value=True))
            stack.enter_context(patch('sys.argv', ['toktopus']))
            cli.main()
        self.assertEqual(live.return_value.__enter__.return_value.update.call_count, 10)
        restore.assert_called_once()

    def test_export_marks_unavailable_and_avoids_codex_double_billing(self):
        from toktopus.cli import export_telemetry_snapshot
        from toktopus.core.pricing import calculate_costs
        path = self.root / 'snapshot.json'
        data = dict(session_id='s', input_tokens=100, cache_read_tokens=40, output_tokens=20, reasoning_tokens=5, current_context_available=False, tokens_per_sec_available=False, model_name='o3-mini')
        export_telemetry_snapshot(str(path), data, {}, 'codex', 'codex-pro', 'o3-mini')
        result = json.loads(path.read_text())
        self.assertIsNone(result['tokens']['current_context'])
        self.assertIsNone(result['tokens']['tokens_per_sec'])
        self.assertIsNone(result['account_limits']['tpm_remaining'])
        self.assertIsNone(result['billing']['actual_billed_usd'])
        expected = calculate_costs(input_tokens=60, output_tokens=15, cache_read_tokens=40, reasoning_tokens=5, model_key='o3-mini', step_count=1)
        self.assertEqual(result['billing']['cost_spent_usd'], expected['cost_spent_usd'])

    def test_history_pages_sort_by_source_activity_and_do_not_overlap(self):
        for number in range(9):
            self.store.record('claude', dict(session_id=f's{number}', last_modified=100 - number))
        first = self.store.sessions(limit=6)
        second = self.store.sessions(limit=6, offset=6)
        self.assertEqual([row['session_id'] for row in first], [f's{i}' for i in range(6)])
        self.assertEqual([row['session_id'] for row in second], ['s6', 's7', 's8'])

    def test_metadata_allowlist_rejects_nested_payloads_and_nonfinite_values(self):
        self.store.record('claude', dict(session_id='s', input_tokens={'prompt': 'PRIVATE'}, total_tokens=float('nan'), recent_steps=[dict(index=1, tools=[{'name': 'Read', 'input': 'PRIVATE'}, {'input': 'PRIVATE'}], duration_sec=float('inf'))]))
        history = json.dumps(self.store.sessions()) + json.dumps(self.store.timeline('claude', 's'))
        self.assertNotIn('PRIVATE', history)
        self.assertNotIn('NaN', history)
        self.assertNotIn('Infinity', history)
        self.assertEqual(self.store.timeline('claude', 's')[0]['tools'], ['Read'])

    def test_missing_otlp_counters_and_timestamps_stay_unavailable(self):
        import_otlp(self.otlp([dict(traceId='trace', spanId='span')]), self.store)
        event = self.store.timeline('otel:local', 'trace')[0]
        self.assertEqual(event['event_id'], 'span')
        for key in ('total_tokens', 'input_tokens', 'output_tokens', 'duration_sec', 'timestamp'):
            self.assertNotIn(key, event)

    def test_imported_timeline_orders_by_source_time_and_supports_older_pages(self):
        from rich.console import Console

        from toktopus.ui.history import render_timeline
        spans = [dict(traceId='t', spanId='late', startTimeUnixNano='3000000000', endTimeUnixNano='4000000000'), dict(traceId='t', spanId='early', startTimeUnixNano='1000000000', endTimeUnixNano='2000000000')]
        import_otlp(self.otlp(spans), self.store)
        self.assertEqual([event['event_id'] for event in self.store.timeline('otel:local', 't')], ['early', 'late'])
        output = io.StringIO()
        Console(file=output, width=180).print(render_timeline(self.store, 'otel:local', 't', limit=1, offset=1))
        self.assertIn('early', output.getvalue())
        self.assertNotIn('late', output.getvalue())

    def test_native_timestamp_applies_to_all_tools_in_a_record(self):
        path = self.root / 'timestamps.jsonl'
        path.write_text(json.dumps(dict(timestamp='2026-11-02T00:00:00Z', message=dict(content=[dict(type='tool_use', id='a', name='Read'), dict(type='tool_use', id='b', name='Read')]))))
        events, skipped = read_native_events(path, 'claude')
        self.assertEqual(skipped, 0)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['timestamp'], events[1]['timestamp'])

    def test_codex_explicit_missing_session_does_not_use_another_rollout(self):
        from toktopus.adapters import codex
        sessions = self.root / 'sessions'
        sessions.mkdir()
        (sessions / 'rollout-other.jsonl').write_text(json.dumps(dict(type='session_meta', payload=dict(id='other'))))
        with patch.object(codex, 'CODEX_DIR', self.root), patch.object(codex, 'get_system_telemetry', return_value={}):
            result = codex.CodexAdapter().get_session_telemetry('missing')
        self.assertEqual(result['session_id'], 'missing')
        self.assertEqual(result['data_status'], 'no-session')
        self.assertFalse(result['current_context_available'])


if __name__ == '__main__':
    unittest.main()
