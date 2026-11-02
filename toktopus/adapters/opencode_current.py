"""Read OpenCode's session/message/part schema without modifying its database."""
import json
import math
import sqlite3
import time
from contextlib import closing


def read_current_schema(path, session_id=None):
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'session', 'message', 'part'}.issubset(tables):
            return None
        if session_id:
            row = db.execute('SELECT id, title, time_created, time_updated FROM session WHERE id=?', (session_id,)).fetchone()
        else:
            row = db.execute('SELECT id, title, time_created, time_updated FROM session ORDER BY time_updated DESC LIMIT 1').fetchone()
        result = {'agent_name': 'OpenCode', 'session_id': session_id or 'no-session', 'model_name': 'Unknown', 'current_context_available': False, 'tokens_per_sec_available': False, 'input_tokens': 0, 'output_tokens': 0, 'cache_read_tokens': 0, 'cache_write_tokens': 0, 'reasoning_tokens': 0, 'total_tokens': 0, 'current_context_tokens': 0, 'recent_steps': [], 'recent_steps_tokens': [], 'is_active': False, 'data_status': 'no-session'}
        if not row:
            return result
        sid, title, created, updated = row
        result.update(session_id=sid, title=title, last_modified=updated / 1000, session_elapsed_sec=max(0, (updated - created) / 1000), is_active=time.time() - updated / 1000 < 180, data_status='observed')
        messages = db.execute('SELECT id, data FROM message WHERE session_id=? ORDER BY time_created, id LIMIT 10001', (sid,)).fetchall()
        if len(messages) > 10000:
            result.update(data_status='partial', diagnostic_error='Session exceeds 10000-message read limit; counts cover the first 10000 messages.')
        cost = 0.0
        for msg_id, raw in messages[:10000]:
            if raw is None or len(raw) > 2_000_000:
                result.update(data_status='partial', diagnostic_error='Some message metadata is missing or oversized.')
                continue
            try:
                message = json.loads(raw)
                if not isinstance(message, dict):
                    raise ValueError('Unsupported message')
                if message.get('role') == 'assistant':
                    tokens = message.get('tokens') or {}
                    cache = tokens.get('cache') or {}
                    counts = { 'input_tokens': int(tokens.get('input', 0)), 'output_tokens': int(tokens.get('output', 0)), 'reasoning_tokens': int(tokens.get('reasoning', 0)), 'cache_read_tokens': int(cache.get('read', 0)), 'cache_write_tokens': int(cache.get('write', 0)) }
                    if any(value < 0 for value in counts.values()):
                        raise ValueError('Negative token count')
                    for key, value in counts.items():
                        result[key] += value
                    result['model_name'] = message.get('modelID') or result['model_name']
                    reported_cost = float(message.get('cost') or 0)
                    if not math.isfinite(reported_cost) or reported_cost < 0:
                        raise ValueError('Invalid reported cost')
                    cost += reported_cost
                parts = db.execute('SELECT id, data FROM part WHERE message_id=? ORDER BY time_created, id LIMIT 1000', (msg_id,)).fetchall()
                for part_id, part_raw in parts:
                    if part_raw is None or len(part_raw) > 2_000_000:
                        continue
                    part = json.loads(part_raw)
                    if isinstance(part, dict) and part.get('type') == 'tool':
                        state = part.get('state') or {}
                        status = {'error': 'ERROR', 'completed': 'DONE'}.get(state.get('status'), 'OBSERVED')
                        result['recent_steps'].append({'event_id': str(part_id), 'type': 'TOOL_CALL', 'status': status, 'tools': [part.get('tool', 'tool')]})
            except (ValueError, TypeError, AttributeError):
                result.update(data_status='partial', diagnostic_error='Some message or tool metadata could not be parsed.')
        result['session_cost'] = cost
        prompt = result['input_tokens'] + result['cache_read_tokens'] + result['cache_write_tokens']
        result['cache_efficiency'] = 100 * result['cache_read_tokens'] / prompt if prompt else 0
        result['total_tokens'] = sum(result[key] for key in ('input_tokens', 'output_tokens', 'reasoning_tokens', 'cache_read_tokens', 'cache_write_tokens'))
        result['recent_steps'] = result['recent_steps'][-1000:]
        return result
