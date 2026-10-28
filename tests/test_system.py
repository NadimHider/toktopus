import unittest
from toktopus.core.system import get_system_telemetry, _scan_gpu_telemetry

class TestSystem(unittest.TestCase):
    def test_system_telemetry(self):
        sys_data = get_system_telemetry()
        self.assertIn("host_cpu_percent", sys_data)
        self.assertIn("host_ram_used_gb", sys_data)
        self.assertIn("host_ram_total_gb", sys_data)
        self.assertIn("ai_processes", sys_data)
        self.assertIn("gpu", sys_data)
        self.assertGreaterEqual(sys_data["host_ram_total_gb"], 1.0)

        # Extended telemetry fields
        self.assertIn("cpu_freq_mhz", sys_data)
        self.assertIn("cpu_cores_logical", sys_data)
        self.assertIn("cpu_cores_physical", sys_data)
        self.assertIn("swap_used_gb", sys_data)
        self.assertIn("swap_total_gb", sys_data)
        self.assertIn("swap_percent", sys_data)
        self.assertIn("disk_used_gb", sys_data)
        self.assertIn("disk_total_gb", sys_data)
        self.assertIn("disk_free_gb", sys_data)
        self.assertIn("disk_percent", sys_data)
        self.assertIn("net_sent_mb", sys_data)
        self.assertIn("net_recv_mb", sys_data)
        self.assertGreaterEqual(sys_data["cpu_cores_logical"], 1)

    def test_gpu_scan_safe_execution(self):
        # Should execute safely and return None or valid GPU dict
        gpu_result = _scan_gpu_telemetry()
        if gpu_result is not None:
            self.assertIn("gpu_util_percent", gpu_result)
            self.assertIn("vram_used_mb", gpu_result)
            self.assertIn("vram_total_mb", gpu_result)
            self.assertIn("gpu_name", gpu_result)
        else:
            self.assertIsNone(gpu_result)

if __name__ == "__main__":
    unittest.main()
