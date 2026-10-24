import unittest
from toktopus.ui.charts import (
    braille_sparkline,
    context_gauge,
    stacked_token_ratio_bar,
    mini_cpu_gauge,
    relative_benchmark_bar
)

class TestCharts(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
