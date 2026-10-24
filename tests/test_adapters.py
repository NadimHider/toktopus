import unittest
from toktopus.adapters import ADAPTERS, get_adapter

class TestAdapters(unittest.TestCase):
    def test_all_adapters_registered(self):
        for name in ["antigravity", "claude", "opencode", "cursor"]:
            self.assertIn(name, ADAPTERS)
            adapter = get_adapter(name)
            self.assertIsNotNone(adapter)
            telemetry = adapter.get_session_telemetry()
            self.assertIn("agent_name", telemetry)
            self.assertIn("total_tokens", telemetry)
            self.assertIn("current_context_tokens", telemetry)
            self.assertIn("cache_efficiency", telemetry)

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

if __name__ == "__main__":
    unittest.main()
