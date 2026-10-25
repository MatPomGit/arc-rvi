import unittest

from rvi.quality import QualityLimits, accept_measurements


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.limits = QualityLimits(100.0, 40.0, 215.0)

    def test_accepts_boundary_values(self):
        self.assertTrue(accept_measurements(100.0, 40.0, self.limits))

    def test_rejects_blurred_measurements(self):
        self.assertFalse(accept_measurements(99.9, 80.0, self.limits))

    def test_rejects_bad_exposure(self):
        self.assertFalse(accept_measurements(150.0, 240.0, self.limits))

    def test_rejects_nonfinite_measurements(self):
        self.assertFalse(accept_measurements(float("nan"), 100, self.limits))

    def test_invalid_limits_fail(self):
        with self.assertRaises(ValueError):
            QualityLimits(100, 230, 10)


if __name__ == "__main__":
    unittest.main()
