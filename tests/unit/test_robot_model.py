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
from rvi.robot_model import inspect_urdf, load_joint_state

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
            ('type="revolute"', 'type="planar"'),
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

    def test_one_root_floating_joint_uses_virtual_identity_not_robot_pose(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefix = (
                '<link name="world"/>'
                '<joint name="floating_base" type="floating">'
                '<parent link="world"/><child link="pelvis"/>'
                '</joint>'
            )
            path, checksum = write_model(
                Path(tmp), TOY.replace('<link name="pelvis"/>',
                                        prefix + '<link name="pelvis"/>'))
            report = inspect_urdf(path, checksum, camera_frame="camera")
            self.assertEqual(report["root_link"], "world")
            self.assertEqual(report["joint_types"]["floating"], 1)
            self.assertTrue(report["floating_base_zero_pose_assumed"])
            self.assertEqual(report["camera_frame"]["zero_joint_pose"]["relative_to"],
                             "world")
            self.assertEqual(report["physical_or_collision_validation"], "not_performed")

            misplaced = TOY.replace('name="camera_mount" type="fixed"',
                                    'name="camera_mount" type="floating"')
            path, checksum = write_model(Path(tmp), misplaced)
            with self.assertRaisesRegex(ValueError, "floating-base"):
                inspect_urdf(path, checksum)

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



    def test_joint_state_configured_fk_against_analytic_two_joint_chain(self):
        """A 90-degree yaw rotates the prismatic rail and camera offset."""
        model = """<robot name="analytic_articulated">
<link name="base"/><link name="arm"/><link name="camera"/><link name="tip"/>
<joint name="yaw" type="revolute">
  <parent link="base"/><child link="arm"/>
  <origin xyz="1 0 0"/><axis xyz="0 0 2"/>
  <limit lower="-1.5707963267948966" upper="1.5707963267948966"/>
</joint>
<joint name="camera_mount" type="fixed">
  <parent link="arm"/><child link="camera"/><origin xyz="2 0 0"/>
</joint>
<joint name="slider" type="prismatic">
  <parent link="arm"/><child link="tip"/>
  <origin xyz="1 0 0"/><axis xyz="2 0 0"/>
  <limit lower="0" upper="2"/>
</joint>
</robot>"""
        with tempfile.TemporaryDirectory() as tmp:
            path, checksum = write_model(Path(tmp), model)
            state = {"yaw": pi / 2, "slider": 0.5}
            result = inspect_urdf(path, checksum, camera_frame="camera",
                                  joint_positions=state)
            self.assertEqual(result["camera_frame"]["zero_joint_pose"]
                             ["translation_m"], [3.0, 0.0, 0.0])
            poses = result["configured_joint_pose"]["frame_poses"]
            for name, point in (
                    ("base", (0, 0, 0)), ("arm", (1, 0, 0)),
                    ("camera", (1, 2, 0)), ("tip", (1, 1.5, 0))):
                with self.subTest(link=name):
                    self.assertTrue(all(isclose(a, b, abs_tol=1e-12)
                                        for a, b in zip(poses[name]["translation_m"],
                                                        point)))
            self.assertTrue(isclose(poses["camera"]["rotation_matrix"][0][1],
                                    -1, abs_tol=1e-12))
            self.assertEqual(result["configured_joint_pose"]["collision_or_ik_validation"],
                             "not_performed")
            self.assertEqual(result["configured_joint_pose"]["physical_robot_validation"],
                             "not_performed")
            self.assertEqual(result, inspect_urdf(path, checksum, camera_frame="camera",
                                                  joint_positions=state))

    def test_configured_fk_joint_limits_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, checksum = write_model(Path(tmp), TOY)
            for invalid in ({"arm_joint": 1.01}, {"arm_joint": -1.01},
                            {"arm_joint": float("nan")}, {"arm_joint": True},
                            {"mast_joint": 0.0}, {}, {"arm_joint": 0, "extra": 0}):
                with self.subTest(state=invalid), self.assertRaises(ValueError):
                    inspect_urdf(path, checksum, joint_positions=invalid)
            accepted = inspect_urdf(path, checksum, joint_positions={"arm_joint": 1})
            self.assertEqual(accepted["configured_joint_pose"]["joints"], {"arm_joint": 1})

    def test_continuous_joint_and_virtual_floating_base_state_is_assumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            xml = TOY.replace('type="revolute"', 'type="continuous"')
            xml = xml.replace('<link name="pelvis"/>',
                              '<link name="world"/><link name="pelvis"/>'
                              '<joint name="base_joint" type="floating">'
                              '<parent link="world"/><child link="pelvis"/>'
                              '</joint>')
            path, checksum = write_model(Path(tmp), xml)
            result = inspect_urdf(path, checksum, joint_positions={"arm_joint": pi})
            self.assertTrue(result["configured_joint_pose"]["floating_base_identity_assumed"])
            self.assertEqual(result["configured_joint_pose"]["frame_poses"]["world"]
                             ["translation_m"], [0.0, 0.0, 0.0])
            with self.assertRaisesRegex(ValueError, "unexpected"):
                inspect_urdf(path, checksum,
                             joint_positions={"arm_joint": 0, "base_joint": 0})

    def test_joint_state_cli_source_hash_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, checksum = write_model(root, TOY)
            state = root / "pose.json"
            raw = b'{"schema_version":"1.0.0","joint_positions":{"arm_joint":0.25}}\n'
            state.write_bytes(raw)
            self.assertEqual(load_joint_state(state)[1], sha256(raw).hexdigest())
            output = root / "poses.json"
            cmd = ["robot-model", "--urdf", str(path), "--expected-sha256",
                   checksum, "--camera-frame", "camera",
                   "--joint-state", str(state), "--output", str(output)]
            with redirect_stdout(StringIO()):
                self.assertEqual(main(cmd), 0)
            report = json.loads(output.read_text())
            self.assertEqual(report["configured_joint_pose"]["joints"],
                             {"arm_joint": 0.25})
            self.assertEqual(report["configured_joint_pose"]["state_source_sha256"],
                             sha256(raw).hexdigest())
            original = output.read_bytes()
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(cmd)
            self.assertEqual(output.read_bytes(), original)
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(cmd[:-1] + [str(state)])
            self.assertEqual(state.read_bytes(), raw)
            link = root / "link.json"
            link.symlink_to(state)
            with self.assertRaises(ValueError):
                load_joint_state(link)

    def test_joint_state_json_and_schema_hard_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "joint.json"
            for content in (
                    '{"schema_version":"1.0.0","joint_positions":{"x":NaN}}',
                    '{"schema_version":"1.0.0","joint_positions":[]}',
                    '{"schema_version":"2.0.0","joint_positions":{}}',
                    '{"schema_version":"1.0.0","joint_positions":{},"foo":1}',
                    '[]',
                    'malformed',
                    ):
                state.write_text(content)
                with self.subTest(content=content), self.assertRaises(ValueError):
                    load_joint_state(state)
            state.write_bytes(b'X' * 65537)
            with self.assertRaisesRegex(ValueError, "size limit"):
                load_joint_state(state)


if __name__ == "__main__":
    unittest.main()
