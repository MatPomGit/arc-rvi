"""Robot-description structural tests, without external assets or robot I/O."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
from io import StringIO
import json
from math import isclose, pi
from pathlib import Path
import tempfile
import unittest

from rvi.adapters.robot import UnconfiguredRobotAdapter
from rvi.cli import main
from rvi.interfaces import AdapterUnavailable
from rvi.robot_model import inspect_urdf

TOY = """<robot name="neutral_test">
<link name="pelvis"/><link name="mast"/><link name="camera"/><link name="arm"/>
<joint name="mast_joint" type="fixed">
  <parent link="pelvis"/><child link="mast"/>
  <origin xyz="1 0 0" rpy="0 0 1.5707963267948966"/>
</joint>
<joint name="camera_mount" type="fixed">
  <parent link="mast"/><child link="camera"/><origin xyz="1 0 0"/>
</joint>
<joint name="arm_joint" type="revolute">
  <parent link="pelvis"/><child link="arm"/><origin xyz="0 0 1"/>
  <axis xyz="0 0 1"/><limit lower="-1.0" upper="1.0"/>
</joint>
</robot>"""


def write_model(root: Path, content: str) -> tuple[Path, str]:
    path = root / "model.urdf"
    raw = content.encode("utf-8")
    path.write_bytes(raw)
    return path, sha256(raw).hexdigest()


class RobotModelAuditTests(unittest.TestCase):
    def test_analytic_transform_tree_and_camera_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, checksum = write_model(Path(tmp), TOY)
            report = inspect_urdf(path, checksum, camera_frame="camera")
            self.assertEqual(report["evidence_type"], "fixture")
            self.assertEqual(report["robot_name"], "neutral_test")
            self.assertEqual(report["link_count"], 4)
            self.assertEqual(report["joint_count"], 3)
            self.assertEqual(report["joint_types"], {"fixed": 2, "revolute": 1})
            self.assertEqual(report["max_tree_depth"], 2)
            self.assertTrue(report["zero_joint_pose_within_declared_limits"])
            self.assertEqual(report["root_link"], "pelvis")
            frame = report["camera_frame"]
            self.assertTrue(frame["frame_in_model"])
            self.assertTrue(all(isclose(actual, expected, abs_tol=1e-12)
                                for actual, expected in zip(
                                    frame["zero_joint_pose"]["translation_m"],
                                    (1, 1, 0))))
            rotation = frame["zero_joint_pose"]["rotation_matrix"]
            self.assertTrue(isclose(rotation[0][1], -1, abs_tol=1e-12))
            self.assertTrue(isclose(rotation[1][0], 1, abs_tol=1e-12))
            self.assertEqual(report["robot_adapter"], "not_configured")
            self.assertEqual(report["physical_or_collision_validation"], "not_performed")
            self.assertEqual(report, inspect_urdf(path, checksum, camera_frame="camera"))

    def test_camera_frame_not_in_description_is_unverified_not_fabricated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, checksum = write_model(Path(tmp), TOY)
            report = inspect_urdf(path, checksum, camera_frame="optical_frame")
            self.assertFalse(report["camera_frame"]["frame_in_model"])
            self.assertIsNone(report["camera_frame"]["zero_joint_pose"])
            without = inspect_urdf(path, checksum)
            self.assertIsNone(without["camera_frame"]["requested_frame"])
            self.assertFalse(without["camera_frame"]["frame_in_model"])

    def test_bad_hash_and_xml_security_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, digest = write_model(root, TOY)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                inspect_urdf(path, "0" * 64)
            for bad_digest in ("bad", "F" * 64, 42, None):
                with self.subTest(digest=bad_digest), self.assertRaises(ValueError):
                    inspect_urdf(path, bad_digest)
            with self.assertRaises(ValueError):
                inspect_urdf(path, digest, camera_frame=" ")
            symlink = root / "alias.urdf"
            symlink.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "non-symlinked"):
                inspect_urdf(symlink, digest)
            for snippet in ('<!DOCTYPE robot [<!ENTITY x "ignored">]>',
                            "<!ENTITY x SYSTEM 'file:///etc/passwd'>"):
                content = snippet + TOY
                p, checksum = write_model(root, content)
                with self.subTest(snippet=snippet), self.assertRaisesRegex(
                        ValueError, "DTD and entities"):
                    inspect_urdf(p, checksum)
            p, checksum = write_model(root, "<robot>")
            with self.assertRaisesRegex(ValueError, "malformed"):
                inspect_urdf(p, checksum)

    def test_invalid_joint_graph_and_limits(self):
        edits = [
            ('<link name="mast"/>', '<link name="pelvis"/>'),
            ('<child link="camera"/>', '<child link="missing"/>'),
            ('<child link="mast"/>', '<child link="pelvis"/>'),
            ('type="revolute"', 'type="floating"'),
            ('<axis xyz="0 0 1"/>', '<axis xyz="0 0 0"/>'),
            ('lower="-1.0" upper="1.0"', 'lower="2" upper="-2"'),
            ('lower="-1.0" upper="1.0"', 'lower="nan" upper="1"'),
            ('lower="-1.0" upper="1.0"', ''),
            ('rpy="0 0 1.5707963267948966"', 'rpy="0 nan 0"'),
            ('<parent link="mast"/><child link="camera"/>',
             '<parent link="pelvis"/><child link="pelvis"/>'),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for old, new in edits:
                with self.subTest(change=(old, new)):
                    path, digest = write_model(root, TOY.replace(old, new))
                    with self.assertRaises(ValueError):
                        inspect_urdf(path, digest)
            # An orphaned 2-link cycle with a separate root is rejected.
            xml = TOY.replace(
                '</robot>',
                '<link name="orphan1"/><link name="orphan2"/>'
                '<joint name="cycle1" type="fixed"><parent link="orphan1"/>'
                '<child link="orphan2"/></joint>'
                '<joint name="cycle2" type="fixed"><parent link="orphan2"/>'
                '<child link="orphan1"/></joint></robot>',
            )
            path, digest = write_model(root, xml)
            with self.assertRaisesRegex(ValueError, "disconnected or cyclic"):
                inspect_urdf(path, digest)

    def test_zero_pose_outside_joint_limits_is_not_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = TOY.replace('lower="-1.0" upper="1.0"',
                                'lower="0.2" upper="1.0"')
            path, digest = write_model(Path(tmp), model)
            report = inspect_urdf(path, digest)
            self.assertFalse(report["zero_joint_pose_within_declared_limits"])
            self.assertEqual(report["zero_pose_limit_violations"], ["arm_joint"])

    def test_cli_is_offline_and_never_overwrites_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, digest = write_model(root, TOY)
            out = root / "report.json"
            cmd = ["robot-model", "--urdf", str(path),
                   "--expected-sha256", digest, "--camera-frame", "camera",
                   "--output", str(out)]
            with redirect_stdout(StringIO()):
                self.assertEqual(main(cmd), 0)
            first = out.read_bytes()
            self.assertTrue(json.loads(first)["camera_frame"]["frame_in_model"])
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as exc:
                main(cmd)
            self.assertEqual(exc.exception.code, 2)
            self.assertEqual(out.read_bytes(), first)
            with self.assertRaises(AdapterUnavailable):
                UnconfiguredRobotAdapter().navigate_to(0.0, 0.0)


if __name__ == "__main__":
    unittest.main()
