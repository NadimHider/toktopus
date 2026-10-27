import unittest
import tempfile
import json
import sqlite3
import os
from pathlib import Path
from toktopus.adapters import ADAPTERS, get_adapter, auto_detect_active_agent
from toktopus.adapters.antigravity import AntigravityAdapter
from toktopus.adapters.claude import ClaudeCodeAdapter
from toktopus.adapters.opencode import OpenCodeAdapter
from toktopus.adapters.cursor import CursorAdapter
from toktopus.adapters.codex import CodexAdapter

class TestAdapters(unittest.TestCase):
    def test_all_adapters_registered(self):
        for name in ["antigravity", "claude", "opencode", "cursor", "codex"]:
            self.assertIn(name, ADAPTERS)
            adapter = get_adapter(name)
            self.assertIsNotNone(adapter)
            telemetry = adapter.get_session_telemetry()
            self.assertIn("agent_name", telemetry)
            self.assertIn("total_tokens", telemetry)
            self.assertIn("current_context_tokens", telemetry)
            self.assertIn("cache_efficiency", telemetry)
            self.assertIn("session_elapsed_sec", telemetry)

    def test_antigravity_detection(self):
        ag = get_adapter("antigravity")
        self.assertIsInstance(ag.is_detected(), bool)
        t = ag.get_session_telemetry()
        self.assertGreaterEqual(t["max_context_tokens"], 128_000)
        self.assertIn("current_context_tokens", t)

    def test_cross_session_cache_reset(self):
        ag = get_adapter("antigravity")
        t1 = ag.get_session_telemetry("session_alpha")
        self.assertEqual(t1["session_id"], "session_alpha")
        t2 = ag.get_session_telemetry("session_beta")
        self.assertEqual(t2["session_id"], "session_beta")

    def test_antigravity_partial_line_resilience(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ag = AntigravityAdapter()
            ag.ag_dir = Path(tmpdir)
            log_dir = Path(tmpdir) / "brain" / "test_session" / ".system_generated" / "logs"
            log_dir.mkdir(parents=True)
            transcript = log_dir / "transcript.jsonl"

            # Write one complete line and one incomplete line without newline
            with open(transcript, "w", encoding="utf-8") as f:
                f.write(json.dumps({"input_tokens": 500, "output_tokens": 100}) + "\n")
                f.write('{"input_tokens": 300, "out')  # Incomplete line

            t1 = ag.get_session_telemetry("test_session")
            self.assertEqual(t1["input_tokens"], 500)
            self.assertEqual(t1["output_tokens"], 100)

            # Now complete the second line
            with open(transcript, "a", encoding="utf-8") as f:
                f.write('put_tokens": 200}\n')

            # Force re-read
            ag._last_file_size = 0
            t2 = ag.get_session_telemetry("test_session")
            self.assertEqual(t2["input_tokens"], 800)
            self.assertEqual(t2["output_tokens"], 300)

    def test_claude_adapter_parses_jsonl(self):
        adapter = ClaudeCodeAdapter()
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_sess_dir = Path(tmpdir) / "sessions"
            fake_sess_dir.mkdir(parents=True)
            jsonl_file = fake_sess_dir / "test-session.jsonl"
            with open(jsonl_file, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "input_tokens": 1200,
                    "output_tokens": 400,
                    "cache_read_input_tokens": 8000,
                    "cache_creation_input_tokens": 1500,
                    "model": "claude-3-7-sonnet"
                }) + "\n")

            adapter._cached_files = [jsonl_file]
            adapter._last_scan_time = 9999999999.0  # bypass rescanning
            t = adapter.get_session_telemetry("test-session")
            self.assertEqual(t["input_tokens"], 1200)
            self.assertEqual(t["output_tokens"], 400)
            self.assertEqual(t["cache_read_tokens"], 8000)
            self.assertEqual(t["cache_creation_tokens"], 1500)
            self.assertEqual(t["total_tokens"], 1200 + 400 + 8000 + 1500)

    def test_opencode_telemetry_fields_and_reasoning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "opencode.db"
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE session_v2 (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    slug TEXT,
                    tokens_input INTEGER,
                    tokens_output INTEGER,
                    tokens_cache_read INTEGER,
                    tokens_reasoning INTEGER,
                    tokens_cache_write INTEGER,
                    cost REAL,
                    model TEXT,
                    time_created INTEGER,
                    time_updated INTEGER
                );
            """)
            cur.execute("""
                CREATE TABLE session_message (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    type TEXT,
                    seq INTEGER,
                    time_created INTEGER,
                    time_updated INTEGER,
                    data TEXT
                );
            """)
            cur.execute("""
                INSERT INTO session_v2 VALUES (
                    'ses_12345', 'Test Session', 'test-slug', 5000, 800, 20000, 1500, 200, 0.045,
                    '{"id": "deepseek-v4.1-flash", "providerID": "opencode"}', 1700000000000, 1700000100000
                );
            """)
            cur.execute("""
                INSERT INTO session_message VALUES (
                    'msg_1', 'ses_12345', 'step', 1, 1700000050000, 1700000050000,
                    '{"agents": ["test-agent"], "usage": {"total": 550}}'
                );
            """)
            conn.commit()
            conn.close()

            op = OpenCodeAdapter()
            op._db_path = db_path
            t = op.get_session_telemetry("ses_12345")
            self.assertEqual(t["input_tokens"], 5000)
            self.assertEqual(t["output_tokens"], 800)
            self.assertEqual(t["cache_read_tokens"], 20000)
            self.assertEqual(t["reasoning_tokens"], 1500)
            self.assertEqual(t["cache_write_tokens"], 200)
            self.assertAlmostEqual(t["session_cost"], 0.045)
            self.assertEqual(t["model_name"], "deepseek-v4.1-flash")
            self.assertEqual(len(t["recent_steps"]), 1)

    def test_codex_rollout_parsing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions" / "2026" / "10" / "27"
            sessions_dir.mkdir(parents=True)
            rollout_file = sessions_dir / "rollout-2026-10-27T08-00-00-test-codex-id.jsonl"
            with open(rollout_file, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "type": "session_meta",
                    "payload": {"session_id": "test-codex-id", "timestamp": "2026-10-27T08:00:00.000Z"}
                }) + "\n")
                f.write(json.dumps({
                    "type": "turn_context",
                    "payload": {"model": "gpt-6.1-sol"}
                }) + "\n")
                f.write(json.dumps({
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "model_context_window": 475000,
                            "total_token_usage": {
                                "input_tokens": 15000,
                                "cached_input_tokens": 12000,
                                "output_tokens": 350,
                                "reasoning_output_tokens": 40
                            },
                            "last_token_usage": {
                                "input_tokens": 5000,
                                "cached_input_tokens": 4000,
                                "output_tokens": 100
                            }
                        }
                    }
                }) + "\n")

            cod = CodexAdapter()
            from toktopus.adapters import codex as codex_mod
            orig_dir = codex_mod.CODEX_DIR
            codex_mod.CODEX_DIR = Path(tmpdir)
            try:
                t = cod.get_session_telemetry("test-codex-id")
                self.assertEqual(t["model_name"], "gpt-6.1-sol")
                self.assertEqual(t["max_context_tokens"], 475000)
                self.assertEqual(t["input_tokens"], 15000)
                self.assertEqual(t["cache_read_tokens"], 12000)
                self.assertEqual(t["output_tokens"], 350)
                self.assertEqual(t["reasoning_tokens"], 40)
            finally:
                codex_mod.CODEX_DIR = orig_dir

    def test_cursor_applied_model_parsing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vscdb = Path(tmpdir) / "state.vscdb"
            conn = sqlite3.connect(vscdb)
            cur = conn.cursor()
            cur.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT);")
            cur.execute("""
                INSERT INTO ItemTable VALUES (
                    'cursor/applicationOpenModelAppliedConfig',
                    '{"selectedModels": [{"modelId": "grok-4.7"}]}'
                );
            """)
            cur.execute("""
                INSERT INTO ItemTable VALUES (
                    'aiCodeTracking.dailyStats.2026-10-27',
                    '{"promptTokens": 10000, "completionTokens": 2000, "cachedTokens": 5000}'
                );
            """)
            conn.commit()
            conn.close()

            cur_adapter = CursorAdapter()
            cur_adapter._find_vscdb = lambda: vscdb
            t = cur_adapter.get_session_telemetry("cursor-workspace")
            self.assertEqual(t["model_name"], "grok-4.7 (Cursor)")
            self.assertEqual(t["input_tokens"], 10000)
            self.assertEqual(t["output_tokens"], 2000)
            self.assertEqual(t["cache_read_tokens"], 5000)

    def test_subagent_deduplication(self):
        ag = get_adapter("antigravity")
        t = ag.get_session_telemetry()
        subagents = t.get("active_subagents", [])
        names = [sa["name"] for sa in subagents]
        self.assertEqual(len(names), len(set(names)))

    def test_auto_detect_active_agent(self):
        agent = auto_detect_active_agent()
        self.assertIn(agent, ["antigravity", "claude", "opencode", "cursor", "codex"])

if __name__ == "__main__":
    unittest.main()
