import unittest
import tempfile
import json
import os
from pathlib import Path
from toktopus.adapters import ADAPTERS, get_adapter, auto_detect_active_agent
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

    def test_auto_detect_active_agent(self):
        agent = auto_detect_active_agent()
        self.assertIn(agent, ["antigravity", "claude", "opencode", "cursor", "codex"])

    def test_claude_adapter_parses_jsonl(self):
        adapter = ClaudeCodeAdapter()
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = adapter.get_active_session_id
            fake_sess_dir = Path(tmpdir) / "sessions"
            fake_sess_dir.mkdir(parents=True)
            jsonl_file = fake_sess_dir / "test-claude-session.jsonl"
            with open(jsonl_file, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "input_tokens": 1200,
                    "output_tokens": 400,
                    "cache_read_input_tokens": 8000,
                    "model": "claude-3-7-sonnet"
                }) + "\n")

            self.assertTrue(jsonl_file.exists())

    def test_subagent_deduplication(self):
        ag = get_adapter("antigravity")
        t = ag.get_session_telemetry()
        subagents = t.get("active_subagents", [])
        names = [sa["name"] for sa in subagents]
        self.assertEqual(len(names), len(set(names)))

    def test_opencode_telemetry_fields(self):
        op = OpenCodeAdapter()
        t = op.get_session_telemetry()
        self.assertEqual(t["agent_name"], "OpenCode v2 / Mini")
        self.assertIn("tokens_per_sec", t)
        self.assertIn("session_elapsed_sec", t)

    def test_cursor_telemetry_fields(self):
        cur = CursorAdapter()
        t = cur.get_session_telemetry()
        self.assertEqual(t["agent_name"], "Cursor Agent")
        self.assertIn("tokens_per_sec", t)
        self.assertIn("is_active", t)

    def test_codex_telemetry_fields(self):
        cod = CodexAdapter()
        t = cod.get_session_telemetry()
        self.assertEqual(t["agent_name"], "Codex / Copilot")
        self.assertIn("tokens_per_sec", t)
        self.assertIn("is_active", t)

if __name__ == "__main__":
    unittest.main()
