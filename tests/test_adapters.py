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
        self.assertTrue(ag.is_detected())
        t = ag.get_session_telemetry()
        self.assertGreaterEqual(t["max_context_tokens"], 128_000)
        self.assertIn("current_context_tokens", t)

if __name__ == "__main__":
    unittest.main()
