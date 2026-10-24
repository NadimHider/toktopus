import unittest
from toktopus.core.pricing import calculate_costs
from toktopus.core.benchmarks import get_benchmarks, find_model_benchmark

class TestPricingAndBenchmarks(unittest.TestCase):
    def test_calculate_costs(self):
        costs = calculate_costs(input_tokens=100_000, output_tokens=10_000, cache_read_tokens=500_000, model_key="gemini-3.8-flash")
        self.assertIn("cost_spent_usd", costs)
        self.assertIn("cost_saved_usd", costs)
        self.assertGreater(costs["cost_saved_usd"], 0)

    def test_benchmarks_list(self):
        b = get_benchmarks()
        self.assertGreater(len(b), 3)
        self.assertGreater(b[0]["coding_elo"], b[-1]["coding_elo"])

    def test_find_benchmark(self):
        m = find_model_benchmark("claude-3-7-sonnet")
        self.assertIn("Claude", m["name"])

if __name__ == "__main__":
    unittest.main()
