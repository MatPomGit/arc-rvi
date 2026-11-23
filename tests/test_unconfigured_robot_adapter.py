"""Fail-closed contract tests for the deliberately unconfigured robot adapter."""

from pathlib import Path
import unittest

from rvi.adapters.robot import UnconfiguredRobotAdapter
from rvi.interfaces import AdapterUnavailable, RobotAdapter


class UnconfiguredRobotAdapterTests(unittest.TestCase):
    def test_implements_robot_protocol_without_enabling_hardware(self):
        adapter = UnconfiguredRobotAdapter()
        self.assertIsInstance(adapter, RobotAdapter)

    def test_every_device_operation_fails_closed(self):
        adapter = UnconfiguredRobotAdapter()
        operations = (
            ("confirm_target", lambda: adapter.confirm_target("car-01")),
            ("navigate_to", lambda: adapter.navigate_to(1.0, 2.0)),
            ("capture_image", lambda: adapter.capture_image(Path("unused.pgm"))),
            ("stop_motion", adapter.stop_motion),
        )
        for name, operation in operations:
            with self.subTest(operation=name):
                with self.assertRaises(AdapterUnavailable) as context:
                    operation()
                self.assertIn("not configured", str(context.exception))


if __name__ == "__main__":
    unittest.main()
