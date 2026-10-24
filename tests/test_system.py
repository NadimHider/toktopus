import unittest
from toktopus.core.system import get_system_telemetry

class TestSystem(unittest.TestCase):
    def test_system_telemetry(self):
        sys_data = get_system_telemetry()
        self.assertIn("host_cpu_percent", sys_data)
        self.assertIn("host_ram_used_gb", sys_data)
        self.assertIn("host_ram_total_gb", sys_data)
        self.assertIn("ai_processes", sys_data)
        self.assertGreaterEqual(sys_data["host_ram_total_gb"], 1.0)

if __name__ == "__main__":
    unittest.main()
