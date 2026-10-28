import unittest
from toktopus.ui.charts import (
    braille_sparkline,
    context_gauge,
    stacked_token_ratio_bar,
    mini_cpu_gauge,
    relative_benchmark_bar,
    cache_efficiency_gauge,
    efficiency_status_badge,
    cache_split_bar,
    cache_trend_sparkline,
    cost_burn_bar,
    format_metric_number
)

class TestCharts(unittest.TestCase):
    def test_format_metric_number(self):
        self.assertEqual(format_metric_number(500), "500")
        self.assertEqual(format_metric_number(1500), "1.5K")
        self.assertEqual(format_metric_number(2_500_000), "2.5M")
        self.assertEqual(format_metric_number(1_200_000_000), "1.2B")
    def test_braille_sparkline(self):
        data = [10, 50, 100, 25, 80]
        spark = braille_sparkline(data, max_width=10)
        self.assertEqual(len(spark), len(data))
        self.assertTrue(any(c in spark for c in ["⡀", "⣀", "⠤", "⠶", "⠒", "⠊", "⠉", "⠑"]))

    def test_empty_sparkline(self):
        spark = braille_sparkline([], max_width=5)
        self.assertEqual(len(spark), 5)

    def test_context_gauge(self):
        gauge_low = context_gauge(20_000, 200_000, width=10)
        self.assertIn("10.0%", gauge_low)
        self.assertIn("#00ff88", gauge_low)

        gauge_high = context_gauge(180_000, 200_000, width=10)
        self.assertIn("90.0%", gauge_high)
        self.assertIn("#ff3366", gauge_high)

    def test_stacked_token_ratio_bar(self):
        bar = stacked_token_ratio_bar(8000, 1000, 1000, width=20)
        self.assertIn("#00ff88", bar)
        self.assertIn("#00f3ff", bar)
        self.assertIn("#b026ff", bar)

    def test_mini_cpu_gauge(self):
        gauge = mini_cpu_gauge(45.0, width=10)
        self.assertIn("#00ff88", gauge)

    def test_relative_benchmark_bar(self):
        bar = relative_benchmark_bar(1350, max_score=1400, width=10)
        self.assertIn("#00f3ff", bar)

    def test_cache_efficiency_gauge(self):
        gauge_optimal = cache_efficiency_gauge(92.5, width=15)
        self.assertIn("92.5%", gauge_optimal)
        self.assertIn("OPTIMAL", gauge_optimal)
        self.assertIn("#00ff88", gauge_optimal)

        gauge_cold = cache_efficiency_gauge(15.0, width=15)
        self.assertIn("15.0%", gauge_cold)
        self.assertIn("COLD", gauge_cold)
        self.assertIn("#ff3366", gauge_cold)

    def test_efficiency_status_badge(self):
        self.assertIn("ELITE CACHE", efficiency_status_badge(90.0))
        self.assertIn("OPTIMAL", efficiency_status_badge(70.0))
        self.assertIn("MODERATE", efficiency_status_badge(45.0))
        self.assertIn("COLD MISS", efficiency_status_badge(10.0))

    def test_cache_split_bar(self):
        bar = cache_split_bar(cached_tokens=80000, fresh_tokens=20000, width=20)
        self.assertIn("#00ff88", bar)
        self.assertIn("#00f3ff", bar)

    def test_cache_trend_sparkline(self):
        steps = [
            {"cache_tokens": 5000, "input_tokens": 5000},
            {"cache_tokens": 8000, "input_tokens": 2000},
            {"cache_tokens": 9000, "input_tokens": 1000}
        ]
        spark = cache_trend_sparkline(steps, max_width=10)
        self.assertEqual(len(spark), len(steps))

    def test_cost_burn_bar(self):
        bar = cost_burn_bar(cost_usd=2.50, max_budget_usd=10.0, width=10)
        self.assertIn("#00ff88", bar)

if __name__ == "__main__":
    unittest.main()
