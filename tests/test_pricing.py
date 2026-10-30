import unittest

from toktopus.core.benchmarks import (
    find_model_benchmark,
    get_benchmarks,
    get_benchmarks_last_updated,
)
from toktopus.core.pricing import calculate_costs, resolve_pricing_model


class TestPricingAndBenchmarks(unittest.TestCase):
    def test_calculate_costs(self):
        costs = calculate_costs(
            input_tokens=100_000,
            output_tokens=10_000,
            cache_read_tokens=500_000,
            model_key="gemini-3.8-flash",
            reasoning_tokens=5_000,
            cache_write_tokens=20_000,
            step_count=10,
            elapsed_sec=60.0
        )
        self.assertIn("cost_spent_usd", costs)
        self.assertIn("cost_saved_usd", costs)
        self.assertIn("cost_without_cache_usd", costs)
        self.assertIn("savings_percent", costs)
        self.assertIn("cost_per_step_usd", costs)
        self.assertIn("burn_rate_hourly_usd", costs)
        self.assertIn("projected_1k_steps_usd", costs)
        self.assertGreater(costs["cost_saved_usd"], 0)
        self.assertGreater(costs["savings_percent"], 0)
        self.assertGreater(costs["cost_per_step_usd"], 0)
        self.assertGreater(costs["burn_rate_hourly_usd"], 0)

    def test_resolve_pricing_model(self):
        self.assertEqual(resolve_pricing_model("Gemini 2.5 Pro", "antigravity"), "gemini-2-5-pro")
        self.assertEqual(resolve_pricing_model("Gemini 3.8 Flash (High)", "antigravity"), "gemini-3.8-flash")
        self.assertEqual(resolve_pricing_model("Claude 3.7 Sonnet Thinking", "claude"), "claude-3-7-sonnet")
        self.assertEqual(resolve_pricing_model("Claude 5.5 preview", "claude"), "claude-5-5")
        self.assertEqual(resolve_pricing_model("o3-mini-high", "codex"), "o3-mini")
        self.assertEqual(resolve_pricing_model("GPT 6.1 Coding", "codex"), "gpt-6-1")
        self.assertEqual(resolve_pricing_model("DeepSeek R1", "opencode"), "deepseek-r1")
        self.assertEqual(resolve_pricing_model("DeepSeek R4.1 Flash", "opencode"), "deepseek-r4-1-flash")
        self.assertEqual(resolve_pricing_model("Qwen 2.5 Coder 32B", "opencode"), "qwen-2-5-coder-32b")

        self.assertEqual(resolve_pricing_model("Random Model", "antigravity", override_key="claude-5-5"), "claude-5-5")

        self.assertEqual(resolve_pricing_model("", "claude"), "claude-3-7-sonnet")
        self.assertEqual(resolve_pricing_model("", "opencode"), "deepseek-r4-1-flash")

    def test_benchmarks_list(self):
        b = get_benchmarks()
        self.assertGreater(len(b), 3)
        self.assertGreater(b[0]["coding_elo"], b[-1]["coding_elo"])

    def test_find_benchmark(self):
        m = find_model_benchmark("claude-3-7-sonnet")
        self.assertIn("Claude", m["name"])

    def test_benchmarks_last_updated(self):
        dt_str = get_benchmarks_last_updated()
        self.assertIsInstance(dt_str, str)
        self.assertIn("2026", dt_str)

if __name__ == "__main__":
    unittest.main()
