import os
import unittest
from unittest.mock import patch, mock_open
from core.system_stress_guard import SystemStressGuard

class TestSystemStressGuard(unittest.TestCase):
    def test_get_available_memory_mb(self):
        mock_meminfo = "MemTotal: 24000000 kB\nMemAvailable: 5000000 kB\n"
        with patch("builtins.open", mock_open(read_data=mock_meminfo)):
            guard = SystemStressGuard()
            self.assertEqual(guard.get_available_memory_mb(), 5000000 // 1024)

    def test_is_host_under_stress_mem(self):
        # Stress por memoria baja
        with patch.object(SystemStressGuard, "get_available_memory_mb", return_value=500):
            with patch.object(SystemStressGuard, "get_load_avg", return_value=(0.1, 0.1, 0.1)):
                guard = SystemStressGuard(min_available_mb=1000)
                self.assertTrue(guard.is_host_under_stress())
                snapshot = guard.get_stress_snapshot()
                self.assertTrue(snapshot["is_mem_stressed"])
                self.assertFalse(snapshot["is_cpu_stressed"])

    def test_is_host_under_stress_cpu(self):
        # Stress por load alto
        with patch.object(SystemStressGuard, "get_available_memory_mb", return_value=5000):
            with patch.object(SystemStressGuard, "get_load_avg", return_value=(10.0, 5.0, 2.0)):
                with patch.object(SystemStressGuard, "get_cpu_count", return_value=4):
                    # Límite por defecto es 2.0 * cpu_count = 8.0
                    guard = SystemStressGuard(max_load_rel=2.0)
                    self.assertTrue(guard.is_host_under_stress())
                    snapshot = guard.get_stress_snapshot()
                    self.assertTrue(snapshot["is_cpu_stressed"])

    def test_not_under_stress(self):
        with patch.object(SystemStressGuard, "get_available_memory_mb", return_value=5000):
            with patch.object(SystemStressGuard, "get_load_avg", return_value=(1.0, 1.0, 1.0)):
                with patch.object(SystemStressGuard, "get_cpu_count", return_value=4):
                    guard = SystemStressGuard(min_available_mb=1000, max_load_rel=2.0)
                    self.assertFalse(guard.is_host_under_stress())

if __name__ == "__main__":
    unittest.main()
