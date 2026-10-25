import unittest
from toktopus.ui.layout import _format_duration, build_dashboard

class TestLayoutFeatures(unittest.TestCase):
    def test_format_duration(self):
        self.assertEqual(_format_duration(0), "")
        self.assertEqual(_format_duration(-10), "")
        self.assertEqual(_format_duration(45), "45s")
        self.assertEqual(_format_duration(125), "2m 5s")
        self.assertEqual(_format_duration(3665), "1h 1m")

    def test_dashboard_builds_without_error(self):
        telemetry = {
            "agent_name": "Antigravity 2.0",
            "session_id": "test-session",
            "model_name": "Gemini 3.8 Flash",
            "is_active": True,
            "session_elapsed_sec": 300.0,
            "current_context_tokens": 50000,
            "max_context_tokens": 2000000,
            "input_tokens": 10000,
            "output_tokens": 5000,
            "cache_read_tokens": 40000,
            "total_tokens": 55000,
            "cache_efficiency": 80.0,
            "tokens_per_step": 11000,
            "tokens_per_sec": 140,
            "recent_steps_tokens": [1000, 2000, 3000],
            "recent_steps": [],
            "active_subagents": []
        }
        sys_metrics = {
            "host_cpu_percent": 12.0,
            "host_ram_used_gb": 10.0,
            "host_ram_total_gb": 32.0,
            "host_ram_percent": 31.0,
            "ai_processes": [],
            "gpu": {"gpu_util_percent": 24.0, "vram_used_mb": 2048.0, "vram_total_mb": 8192.0, "gpu_name": "RTX 4070"}
        }
        layout = build_dashboard(telemetry, sys_metrics, "antigravity", "gemini-3.8-flash")
        self.assertIsNotNone(layout)

    def test_context_alert_in_dashboard(self):
        telemetry = {
            "agent_name": "Claude Code",
            "session_id": "heavy-session",
            "model_name": "Claude 3.7 Sonnet",
            "is_active": True,
            "session_elapsed_sec": 600.0,
            "current_context_tokens": 180000,
            "max_context_tokens": 200000,
            "input_tokens": 80000,
            "output_tokens": 10000,
            "cache_read_tokens": 100000,
            "total_tokens": 190000,
            "cache_efficiency": 55.0,
            "tokens_per_step": 20000,
            "tokens_per_sec": 80,
            "recent_steps_tokens": [5000, 15000],
            "recent_steps": [],
            "active_subagents": []
        }
        sys_metrics = {
            "host_cpu_percent": 5.0,
            "host_ram_used_gb": 4.0,
            "host_ram_total_gb": 16.0,
            "host_ram_percent": 25.0,
            "ai_processes": [],
            "gpu": None
        }
        # 180k / 200k = 90% (triggers >= 85% alert)
        layout = build_dashboard(telemetry, sys_metrics, "claude", "claude-3-7-sonnet", plan_tier_key="claude-pro")
        self.assertIsNotNone(layout)

if __name__ == "__main__":
    unittest.main()
