import unittest
import tempfile
import json
import os
import toktopus
from toktopus.cli import export_telemetry_snapshot

class TestVersionAndExport(unittest.TestCase):
    def test_version_string(self):
        self.assertEqual(toktopus.__version__, "1.3.0")

    def test_export_telemetry_snapshot(self):
        sample_telemetry = {
            "agent_name": "Antigravity 2.0",
            "session_id": "test-session",
            "model_name": "Gemini 3.8 Flash",
            "is_active": True,
            "session_elapsed_sec": 120.0,
            "input_tokens": 1000,
            "output_tokens": 500,
            "cache_read_tokens": 2000,
            "current_context_tokens": 3000,
            "total_tokens": 3500,
            "cache_efficiency": 66.7,
            "tokens_per_step": 700,
            "tokens_per_sec": 120
        }
        sample_sys = {
            "host_cpu_percent": 15.0,
            "host_ram_used_gb": 8.0,
            "host_ram_total_gb": 32.0,
            "host_ram_percent": 25.0,
            "ai_processes": [],
            "gpu": None
        }

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            export_telemetry_snapshot(tmp_path, sample_telemetry, sample_sys, "antigravity", "google-ai-pro", "gemini-3.8-flash")
            self.assertTrue(os.path.exists(tmp_path))
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["version"], "1.3.0")
            self.assertEqual(data["agent"]["key"], "antigravity")
            self.assertEqual(data["tokens"]["input"], 1000)
            self.assertEqual(data["tokens"]["output"], 500)
            self.assertIn("reasoning", data["tokens"])
            self.assertIn("billing", data)
            self.assertIn("account_limits", data)
            self.assertIn("system", data)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
