"""Regression tests for the SSH-only, read-only robot inventory tool."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import inspect_robot_ssh as inventory


class InventoryTests(unittest.TestCase):
    def test_sanitized_report_and_passive_default(self):
        with mock.patch.object(inventory, "_os_release", return_value={"id": "ubuntu"}), \
             mock.patch.object(inventory, "_list_devices", return_value=[]), \
             mock.patch.object(inventory, "_candidate_urdfs", return_value=[]), \
             mock.patch.object(inventory, "_net_interfaces", return_value=[
                 {"interface": "eth0", "carrier": "1", "operstate": "up"}]), \
             mock.patch.object(inventory, "_versions", return_value={}), \
             mock.patch.object(inventory, "_ros", return_value={}):
            record = inventory.collect()
        self.assertEqual(record["dds_lowstate"]["status"], "not_requested")
        self.assertIsNone(record["dds_lowstate"]["mode_machine"])
        self.assertEqual(record["control"], "no_publishers_no_commands_no_motion")
        self.assertNotIn("hostname", record["os"])
        self.assertNotIn("serial_number", record["devices"])
        self.assertNotIn("ChannelPublisher(", inventory.DDS_READ_ONLY)
        self.assertNotIn("LowCmd_", inventory.DDS_READ_ONLY)

    def test_candidate_description_hash_is_exact_and_shallow(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            urdf = root / "model.urdf"
            raw = b'<robot name="fixture"/>'
            urdf.write_bytes(raw)
            (root / "ignored.xml").write_text("not a URDF")
            (root / "nested").mkdir()
            (root / "nested" / "hidden.urdf").write_text("not scanned")
            symlink = root / "linked.urdf"
            symlink.symlink_to(urdf)
            with mock.patch.object(inventory.Path, "home", return_value=root / "no-home"):
                results = inventory._candidate_urdfs([root])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sha256"], sha256(raw).hexdigest())
        self.assertEqual(results[0]["bytes"], len(raw))

    def test_mode_machine_subscriber_is_optional_and_bounded(self):
        with mock.patch.object(inventory, "_net_interfaces", return_value=[
            {"interface": "eth0", "operstate": "up", "carrier": "1"}]):
            self.assertEqual(inventory._dds_mode(None)["status"], "not_requested")
            self.assertEqual(inventory._dds_mode("wlan7")["status"],
                             "interface_not_found")
            received = mock.Mock(returncode=0, stdout=(
                "sdk debug message\nRVI_DDS_JSON="
                + json.dumps({"status": "received", "mode_machine": 15}) + "\n"))
            with mock.patch.object(inventory.subprocess, "run", return_value=received) as run:
                result = inventory._dds_mode("eth0")
                self.assertEqual(result["mode_machine"], 15)
                args, kwargs = run.call_args
                self.assertEqual(args[0][-1], "eth0")
                self.assertEqual(kwargs["timeout"], inventory.DDS_TIMEOUT_S)
                self.assertTrue(kwargs["capture_output"])
            invalid = mock.Mock(returncode=0, stdout="RVI_DDS_JSON={\"status\":\"received\",\"mode_machine\":true}\n")
            with mock.patch.object(inventory.subprocess, "run", return_value=invalid):
                self.assertEqual(inventory._dds_mode("eth0")["status"],
                                 "invalid_subscriber_response")
            with mock.patch.object(inventory.subprocess, "run", side_effect=inventory.subprocess.TimeoutExpired("python", 9)):
                self.assertEqual(inventory._dds_mode("eth0")["status"],
                                 "bounded_timeout")

    def test_os_and_software_no_sensitive_system_dumps(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "os-release"
            f.write_text('ID=ubuntu\nVERSION_ID="22.04"\nPRETTY_NAME="Ubuntu 22.04"\nPASSWORD=secret\n')
            with mock.patch.object(inventory, "_read", return_value=f.read_text()):
                data = inventory._os_release()
            self.assertEqual(set(data), {"id", "version_id", "pretty_name"})
            self.assertNotIn("secret", json.dumps(data))


if __name__ == "__main__":
    unittest.main()
