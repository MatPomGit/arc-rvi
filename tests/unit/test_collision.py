"""Independent analytic tests for fixture-only FK-attached collision spheres."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from hashlib import sha256
from io import StringIO
import json
from math import isclose, pi
from pathlib import Path
import tempfile
import unittest

from rvi.cli import main
from rvi.collision import inspect_collision_proxies, load_collision_fixture
from rvi.robot_model import inspect_urdf


TOY = """<robot name="neutral_collision_chain">
<link name="root"/><link name="arm"/><link name="camera"/>
<joint name="yaw" type="revolute">
<parent link="root"/><child link="arm"/>
<axis xyz="0 0 1"/><limit lower="-2" upper="2"/>
</joint>
<joint name="mount" type="fixed">
<parent link="arm"/><child link="camera"/><origin xyz="1 0 0"/>
</joint>
</robot>"""


def collision_fixture() -> dict:
    return {
        "schema_version": "1.0.0",
        "clearance_margin_m": 0.0,
        "spheres": [
            {"id": "camera_ball", "link": "camera",
             "center_local_m": [0, 0, 0], "radius_m": 0.1}
        ],
        "boxes": [
            {"id": "beam", "min_xyz_m": [-0.05, 0.95, -0.05],
             "max_xyz_m": [0.05, 1.05, 0.05]},
        ],
        "self_pairs": [],
    }


def pose():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "toy.urdf"
        raw = TOY.encode("utf-8")
        path.write_bytes(raw)
        return inspect_urdf(path, sha256(raw).hexdigest(),
                            joint_positions={"yaw": pi / 2})["configured_joint_pose"]


class CollisionProxyTests(unittest.TestCase):
    def test_rotating_link_sphere_hits_axis_aligned_beam(self):
        result = inspect_collision_proxies(pose(), collision_fixture())
        self.assertEqual(result["status"], "proxy_overlap_detected")
        self.assertEqual(result["checked_pairs"], 1)
        self.assertEqual(result["full_body_collision_validation"], "not_performed")
        self.assertEqual(result["trajectory_sweep_validation"], "not_performed")
        self.assertTrue(isclose(result["minimum_signed_clearance_m"], -0.1,
                                abs_tol=1e-12))
        self.assertTrue(result["checks"][0]["touch_or_overlap"])

    def test_separate_obstacle_and_margin_analytic(self):
        fixture = collision_fixture()
        fixture["boxes"][0] = {
            "id": "distant", "min_xyz_m": [2, 0.95, -0.05],
            "max_xyz_m": [3, 1.05, 0.05],
        }
        report = inspect_collision_proxies(pose(), fixture)
        self.assertEqual(report["status"], "no_proxy_overlap_unverified")
        self.assertTrue(isclose(report["minimum_signed_clearance_m"], 1.9,
                                abs_tol=1e-12))
        fixture["clearance_margin_m"] = 1.9
        touching = inspect_collision_proxies(pose(), fixture)
        self.assertEqual(touching["status"], "proxy_overlap_detected")
        self.assertTrue(touching["checks"][0]["touch_or_overlap"])

    def test_explicit_self_pairs_not_claimed_exhaustive(self):
        fixture = collision_fixture()
        fixture["boxes"] = []
        fixture["spheres"].append({
            "id": "arm_ball", "link": "arm",
            "center_local_m": [0, 0, 0], "radius_m": 0.1,
        })
        fixture["self_pairs"] = [["arm_ball", "camera_ball"]]
        report = inspect_collision_proxies(pose(), fixture)
        self.assertEqual(report["status"], "no_proxy_overlap_unverified")
        self.assertEqual(report["explicit_self_pairs"], 1)
        self.assertAlmostEqual(report["minimum_signed_clearance_m"], 0.8)
        fixture["spheres"][0]["radius_m"] = 0.6
        fixture["spheres"][1]["radius_m"] = 0.6
        self.assertEqual(inspect_collision_proxies(pose(), fixture)["status"],
                         "proxy_overlap_detected")
        fixture["self_pairs"].append(["camera_ball", "arm_ball"])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            inspect_collision_proxies(pose(), fixture)

    def test_missing_scope_and_unknown_link_fail_closed(self):
        fixture = collision_fixture()
        fixture["boxes"] = []
        with self.assertRaisesRegex(ValueError, "at least one"):
            inspect_collision_proxies(pose(), fixture)
        fixture = collision_fixture()
        fixture["spheres"][0]["link"] = "imaginary"
        with self.assertRaisesRegex(ValueError, "undeclared"):
            inspect_collision_proxies(pose(), fixture)
        fixture = collision_fixture()
        fixture["self_pairs"] = [["camera_ball", "missing"]]
        with self.assertRaises(ValueError):
            inspect_collision_proxies(pose(), fixture)
        with self.assertRaises(ValueError):
            inspect_collision_proxies({}, collision_fixture())

    def test_invalid_geometry_types_and_ranges_fail_closed(self):
        for key, value in [
            ("clearance_margin_m", -0.1),
            ("clearance_margin_m", float("nan")),
            ("clearance_margin_m", True),
            ("boxes", [{"id":"b", "min_xyz_m":[1, 1, 1],
                        "max_xyz_m":[0, 2, 2]}]),
            ("boxes", [{"id":"b", "min_xyz_m":[1, 1, 1],
                        "max_xyz_m":[1, 2, 2]}]),
            ("spheres", []),
            ("self_pairs", [["bad"]]),
            ("schema_version", "2.0.0")
        ]:
            fixture = collision_fixture()
            fixture[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                inspect_collision_proxies(pose(), fixture)
        for entry in [
            {"id": "camera_ball", "link": "camera",
             "center_local_m": [0, 0, 0], "radius_m": 0},
            {"id": "camera_ball", "link": "camera",
             "center_local_m": [0, float("inf"), 0], "radius_m": 1},
        ]:
            fixture = collision_fixture()
            fixture["spheres"][0] = entry
            with self.assertRaises(ValueError):
                inspect_collision_proxies(pose(), fixture)

    def test_integrated_cli_provenance_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            urdf = root / "toy.urdf"
            raw_model = TOY.encode("utf-8")
            urdf.write_bytes(raw_model)
            state = root / "pose.json"
            state.write_text(json.dumps({"schema_version":"1.0.0",
                                         "joint_positions":{"yaw":pi / 2}}))
            fixture = root / "boxes.json"
            raw_fixture = (json.dumps(collision_fixture(), sort_keys=True) + "\n").encode()
            fixture.write_bytes(raw_fixture)
            report_file = root / "result.json"
            command = ["robot-model", "--urdf", str(urdf), "--expected-sha256",
                       sha256(raw_model).hexdigest(), "--joint-state", str(state),
                       "--collision-fixture", str(fixture), "--output", str(report_file)]
            with redirect_stdout(StringIO()):
                self.assertEqual(main(command), 0)
            result = json.loads(report_file.read_text())
            collision = result["configured_joint_pose"]["collision_proxies"]
            self.assertEqual(collision["status"], "proxy_overlap_detected")
            self.assertEqual(collision["source_sha256"], sha256(raw_fixture).hexdigest())
            previous = report_file.read_bytes()
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(command)
            self.assertEqual(report_file.read_bytes(), previous)
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(["robot-model", "--urdf", str(urdf), "--expected-sha256",
                      sha256(raw_model).hexdigest(), "--collision-fixture", str(fixture),
                      "--output", str(root / "invalid.json")])
            self.assertFalse((root / "invalid.json").exists())
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(command[:-1] + [str(fixture)])
            self.assertEqual(fixture.read_bytes(), raw_fixture)
            link = root / "alias.json"
            link.symlink_to(fixture)
            with self.assertRaises(ValueError):
                load_collision_fixture(link)
            fixture.write_bytes(b"X" * 65537)
            with self.assertRaisesRegex(ValueError, "size limit"):
                load_collision_fixture(fixture)
            fixture.write_text('{"schema_version":"1.0.0","spheres":NaN}')
            with self.assertRaises(ValueError):
                load_collision_fixture(fixture)


if __name__ == "__main__":
    unittest.main()
