"""Independent FK waypoint and conservative centre-chord regression tests."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
from io import StringIO
import json
from math import pi
from pathlib import Path
import tempfile
import unittest

from rvi.cli import main
from rvi.collision import inspect_collision_proxies
from rvi.robot_model import inspect_urdf
from rvi.trajectory import (inspect_rotary_proxy_sweep,
                            inspect_waypoint_collision, load_trajectory,
                            validate_waypoints)

PRISMATIC = """<robot name="synthetic_translation">
<link name="root"/><link name="camera"/>
<joint name="slider" type="prismatic">
<parent link="root"/><child link="camera"/>
<axis xyz="1 0 0"/><limit lower="-2" upper="2"/>
</joint></robot>"""

REVOLUTE = """<robot name="synthetic_rotation">
<link name="root"/><link name="arm"/><link name="camera"/>
<joint name="yaw" type="revolute">
<parent link="root"/><child link="arm"/>
<axis xyz="0 0 1"/><limit lower="-2" upper="2"/>
</joint>
<joint name="mount" type="fixed">
<parent link="arm"/><child link="camera"/><origin xyz="1 0 0"/>
</joint></robot>"""


def obstacle(x: float = 0.0, y: float = 0.0) -> dict:
    return {
        "schema_version": "1.0.0",
        "clearance_margin_m": 0.0,
        "spheres": [{"id": "eye", "link": "camera",
                     "center_local_m": [0, 0, 0], "radius_m": 0.1}],
        "boxes": [{"id": "beam",
                   "min_xyz_m": [x - 0.05, y - 0.05, -0.05],
                   "max_xyz_m": [x + 0.05, y + 0.05, 0.05]}],
        "self_pairs": [],
    }


def inspected_poses(model: str, state_name: str, values: list[float]) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fixture.urdf"
        content = model.encode("utf-8")
        path.write_bytes(content)
        return [
            inspect_urdf(path, sha256(content).hexdigest(),
                         joint_positions={state_name: value})["configured_joint_pose"]
            for value in values
        ]


class WaypointCollisionTests(unittest.TestCase):
    def test_inter_sample_chord_detects_midway_box_with_clear_endpoints(self):
        poses = inspected_poses(PRISMATIC, "slider", [-1.0, 1.0])
        box = obstacle()
        self.assertTrue(all(inspect_collision_proxies(p, box)["status"]
                            == "no_proxy_overlap_unverified" for p in poses))
        outcome = inspect_waypoint_collision(poses, box, [0, 2])
        self.assertEqual(outcome["status"], "possible_chord_obstacle_overlap")
        self.assertEqual(outcome["overlap_waypoint_indices"], [])
        self.assertEqual(outcome["segment_count"], 1)
        self.assertEqual(outcome["possible_chord_contacts"][0]["sphere_id"], "eye")
        self.assertEqual(outcome["continuous_articulated_collision_validation"],
                         "not_performed")
        self.assertEqual(outcome, inspect_waypoint_collision(poses, box, [0, 2]))

    def test_affine_prismatic_sweep_clear_for_declared_proxies_only(self):
        poses = inspected_poses(PRISMATIC, "slider", [-1.0, 1.0])
        report = inspect_waypoint_collision(poses, obstacle(x=5), [0, 2])
        self.assertEqual(report["status"], "affine_proxy_sweep_clear_unverified_body")
        self.assertEqual(report["segment_kinematics"],
                         ["affine_prismatic_interpolation"])
        self.assertEqual(report["affine_proxy_segments"], 1)
        self.assertEqual(report["rotationally_unresolved_segments"], 0)
        self.assertEqual(report["possible_affine_self_contacts"], [])
        self.assertEqual(report["full_body_collision_validation"], "not_performed")

    def test_affine_self_proxy_collision_between_clear_endpoints(self):
        poses = inspected_poses(PRISMATIC, "slider", [-1, 1])
        fixture = {
            "schema_version": "1.0.0", "clearance_margin_m": 0.0,
            "spheres": [
                {"id": "moving", "link": "camera",
                 "center_local_m": [0, 0, 0], "radius_m": 0.2},
                {"id": "stationary", "link": "root",
                 "center_local_m": [0, 0, 0], "radius_m": 0.2},
            ],
            "boxes": [],
            "self_pairs": [["moving", "stationary"]],
        }
        self.assertTrue(all(inspect_collision_proxies(p, fixture)["status"]
                            == "no_proxy_overlap_unverified" for p in poses))
        report = inspect_waypoint_collision(poses, fixture, [0, 1])
        self.assertEqual(report["status"], "affine_self_proxy_overlap_candidate")
        self.assertEqual(report["overlap_waypoint_indices"], [])
        self.assertEqual(len(report["possible_affine_self_contacts"]), 1)
        self.assertAlmostEqual(
            report["possible_affine_self_contacts"][0]["minimum_signed_clearance_m"],
            -0.4, places=12)
        self.assertEqual(report["self_collision_between_waypoints"],
                         "explicit_pairs_affine_only")

    def test_multiple_joint_type_mismatch_rejected(self):
        poses = inspected_poses(PRISMATIC, "slider", [-1.0, 1.0])
        altered = dict(poses[1])
        altered["movable_joint_types"] = {"slider": "revolute"}
        with self.assertRaisesRegex(ValueError, "inconsistent FK joint"):
            inspect_waypoint_collision([poses[0], altered], obstacle(x=5), [0, 1])

    def test_observed_waypoint_overlap_takes_priority(self):
        poses = inspected_poses(PRISMATIC, "slider", [-1, 0, 1])
        result = inspect_waypoint_collision(poses, obstacle(), [0, 1, 2])
        self.assertEqual(result["status"], "proxy_overlap_at_waypoint")
        self.assertEqual(result["overlap_waypoint_indices"], [1])
        self.assertEqual(result["waypoint_count"], 3)

    def test_clear_chord_does_not_prove_curved_fk_motion_clear(self):
        # Two endpoint camera centres are (0,-1,0) and (0,1,0).
        # A true positive-yaw joint sweep goes through (+1,0,0),
        # intersecting the beam at x=1; their straight chord x=0 does not.
        poses = inspected_poses(REVOLUTE, "yaw", [-pi / 2, pi / 2])
        result = inspect_waypoint_collision(poses, obstacle(x=1.0), [0, 1])
        self.assertEqual(result["status"], "rotational_sweep_unresolved")
        self.assertEqual(result["possible_chord_contacts"], [])
        self.assertEqual(result["segment_kinematics"], ["rotary_motion_unresolved"])
        self.assertEqual(result["rotationally_unresolved_segments"], 1)
        self.assertEqual(result["full_body_collision_validation"], "not_performed")

    def test_rotary_arc_midpoint_hits_box_with_clear_endpoint_chord(self):
        # Exact reference: camera centre = (cos(yaw), sin(yaw), 0).
        # At yaw=0 the point is (1,0,0) and intersects a small beam,
        # although yaw=±pi/2 endpoints and their x=0 chord are clear.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "arc.urdf"
            raw = REVOLUTE.encode("utf-8")
            path.write_bytes(raw)
            checksum = sha256(raw).hexdigest()

            def fk(state):
                return inspect_urdf(path, checksum,
                                    joint_positions=state)["configured_joint_pose"]

            poses = [fk({"yaw": -pi / 2}), fk({"yaw": pi / 2})]
            box = obstacle(x=1.0)
            before = inspect_waypoint_collision(poses, box, [0, 2])
            self.assertEqual(before["status"], "rotational_sweep_unresolved")
            self.assertEqual(before["possible_chord_contacts"], [])
            sweep = inspect_rotary_proxy_sweep(poses, box, fk)
            self.assertEqual(sweep["status"], "proxy_overlap_between_waypoints")
            self.assertEqual(sweep["segments"][0]["status"],
                             "proxy_overlap_between_waypoints")
            self.assertAlmostEqual(sweep["segments"][0]["collision_fraction"], 0.5)
            self.assertGreaterEqual(sweep["total_evaluations"], 1)
            self.assertEqual(sweep["full_body_or_robot_motion_certification"],
                             "not_performed")

    def test_rotary_far_obstacle_is_proxy_only_clear_by_global_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "arc.urdf"
            raw = REVOLUTE.encode("utf-8")
            path.write_bytes(raw)
            checksum = sha256(raw).hexdigest()
            def fk(q):
                return inspect_urdf(path, checksum,
                                    joint_positions=q)["configured_joint_pose"]
            poses = [fk({"yaw": -pi / 2}), fk({"yaw": pi / 2})]
            sweep = inspect_rotary_proxy_sweep(poses, obstacle(x=10), fk,
                                              max_evaluations=0)
            self.assertEqual(sweep["status"], "declared_proxies_only_screened")
            self.assertEqual(sweep["segments"][0]["status"],
                             "rotary_declared_proxy_clear_only")
            self.assertEqual(sweep["total_evaluations"], 0)
            self.assertEqual(sweep["coverage"],
                             "declared_spheres_AABBs_and_explicit_self_pairs_only")

    def test_rotary_budget_exhaustion_is_unknown_not_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "arc.urdf"
            raw = REVOLUTE.encode("utf-8")
            path.write_bytes(raw)
            checksum = sha256(raw).hexdigest()
            def fk(q):
                return inspect_urdf(path, checksum,
                                    joint_positions=q)["configured_joint_pose"]
            poses = [fk({"yaw": -pi / 2}), fk({"yaw": pi / 2})]
            sweep = inspect_rotary_proxy_sweep(poses, obstacle(x=1), fk,
                                              max_evaluations=0)
            self.assertEqual(sweep["status"], "rotary_sweep_unresolved")
            self.assertEqual(sweep["total_evaluations"], 0)
            self.assertEqual(sweep["segments"][0]["status"],
                             "rotary_sweep_unresolved_budget")
            self.assertGreater(sweep["segments"][0]["unresolved_intervals"], 0)
            for invalid in (-1, True, 129, 2.5):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    inspect_rotary_proxy_sweep(poses, obstacle(x=1), fk,
                                               max_evaluations=invalid)

    def test_rotary_self_contact_from_stationary_root_proxy(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "arc.urdf"
            raw = REVOLUTE.encode("utf-8")
            path.write_bytes(raw)
            checksum = sha256(raw).hexdigest()
            def fk(q):
                return inspect_urdf(path, checksum,
                                    joint_positions=q)["configured_joint_pose"]
            poses = [fk({"yaw": -pi / 2}), fk({"yaw": pi / 2})]
            fixture = {
                "schema_version": "1.0.0", "clearance_margin_m": 0.0,
                "spheres": [
                    {"id": "rotating", "link": "camera",
                     "center_local_m": [0, 0, 0], "radius_m": 0.1},
                    {"id": "fixed", "link": "root",
                     "center_local_m": [1, 0, 0], "radius_m": 0.1},
                ],
                "boxes": [], "self_pairs": [["rotating", "fixed"]],
            }
            self.assertTrue(all(inspect_collision_proxies(p, fixture)["status"]
                                == "no_proxy_overlap_unverified" for p in poses))
            sweep = inspect_rotary_proxy_sweep(poses, fixture, fk)
            self.assertEqual(sweep["status"], "proxy_overlap_between_waypoints")
            self.assertAlmostEqual(sweep["segments"][0]["collision_fraction"], 0.5)

    def test_rotary_bound_unknown_if_fk_metadata_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "arc.urdf"
            raw = REVOLUTE.encode("utf-8")
            path.write_bytes(raw)
            checksum = sha256(raw).hexdigest()
            def fk(q):
                return inspect_urdf(path, checksum,
                                    joint_positions=q)["configured_joint_pose"]
            poses = [fk({"yaw": -pi / 2}), fk({"yaw": pi / 2})]
            original = poses[1]["all_joint_origin_length_sum_m"]
            poses[1] = dict(poses[1])
            poses[1]["all_joint_origin_length_sum_m"] = original + 1
            sweep = inspect_rotary_proxy_sweep(poses, obstacle(x=10), fk)
            self.assertEqual(sweep["segments"][0]["status"],
                             "unresolved_invalid_bound")
            self.assertEqual(sweep["status"], "rotary_sweep_unresolved")
            with self.assertRaisesRegex(ValueError, "intermediate FK state"):
                inspect_rotary_proxy_sweep(
                    [fk({"yaw": -pi / 2}), fk({"yaw": pi / 2})],
                    obstacle(x=1), lambda q: fk({"yaw": pi / 2}))

    def test_rotary_cli_status_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            urdf = root / "model.urdf"
            raw = REVOLUTE.encode("utf-8")
            urdf.write_bytes(raw)
            traj = root / "motion.json"
            states = {"schema_version": "1.0.0", "waypoints": [
                {"time_s": 0, "joint_positions": {"yaw": -pi / 2}},
                {"time_s": 2, "joint_positions": {"yaw": pi / 2}},
            ]}
            trajectory_bytes = (json.dumps(states) + "\\n").encode()
            traj.write_bytes(trajectory_bytes)
            fixture = root / "boxes.json"
            raw_fixture = (json.dumps(obstacle(x=1), sort_keys=True) + "\\n").encode()
            fixture.write_bytes(raw_fixture)
            out = root / "audit.json"
            base = [
                "robot-model", "--urdf", str(urdf), "--expected-sha256",
                sha256(raw).hexdigest(), "--trajectory", str(traj),
                "--collision-fixture", str(fixture),
            ]
            with redirect_stdout(StringIO()):
                self.assertEqual(main(base + ["--output", str(out)]), 0)
            result = json.loads(out.read_text())["trajectory_proxy"]
            self.assertEqual(result["status"], "proxy_overlap_between_waypoints")
            self.assertEqual(result["rotary_sweep"]["total_evaluations"], 1)
            self.assertEqual(result["source_sha256"], sha256(trajectory_bytes).hexdigest())
            self.assertEqual(result["collision_fixture_sha256"],
                             sha256(raw_fixture).hexdigest())
            blocked = root / "blocked.json"
            with redirect_stdout(StringIO()):
                self.assertEqual(main(base + ["--rotary-evaluations", "0",
                                              "--output", str(blocked)]), 0)
            incomplete = json.loads(blocked.read_text())["trajectory_proxy"]
            self.assertEqual(incomplete["status"], "rotational_sweep_unresolved")
            self.assertEqual(incomplete["rotary_sweep"]["status"],
                             "rotary_sweep_unresolved")
            self.assertEqual(blocked.read_bytes(),
                             blocked.read_bytes())
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(base + ["--rotary-evaluations", "129",
                             "--output", str(root / "invalid.json")])
            self.assertFalse((root / "invalid.json").exists())

    def test_waypoint_schema_and_time_order_fail_closed(self):
        def payload(times):
            return {"schema_version": "1.0.0", "waypoints": [
                {"time_s": t, "joint_positions": {"slider": float(i)}}
                for i, t in enumerate(times)
            ]}
        self.assertEqual(len(validate_waypoints(payload([0, 1]))), 2)
        for times in ([0], [0, 0], [2, 1], [-1, 0],
                      [0, float("inf")], [0, True], list(range(33))):
            with self.subTest(times=times), self.assertRaises(ValueError):
                validate_waypoints(payload(times))
        invalid = payload([0, 1])
        invalid["waypoints"][1]["joint_positions"] = []
        with self.assertRaises(ValueError):
            validate_waypoints(invalid)
        invalid = payload([0, 1])
        invalid["waypoints"][0]["unrecognized"] = True
        with self.assertRaises(ValueError):
            validate_waypoints(invalid)
        with self.assertRaises(ValueError):
            inspect_waypoint_collision([], obstacle(), [])

    def test_cli_provenance_input_overwrite_and_bad_joint_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            urdf = root / "model.urdf"
            raw = PRISMATIC.encode("utf-8")
            urdf.write_bytes(raw)
            trajectory = root / "trajectory.json"
            document = {"schema_version": "1.0.0",
                        "waypoints": [
                            {"time_s": 0, "joint_positions": {"slider": -1}},
                            {"time_s": 1, "joint_positions": {"slider": 1}},
                        ]}
            source = (json.dumps(document, sort_keys=True) + "\n").encode()
            trajectory.write_bytes(source)
            collider = root / "obstacles.json"
            fixture = (json.dumps(obstacle(), sort_keys=True) + "\n").encode()
            collider.write_bytes(fixture)
            out = root / "audit.json"
            command = [
                "robot-model", "--urdf", str(urdf), "--expected-sha256",
                sha256(raw).hexdigest(), "--trajectory", str(trajectory),
                "--collision-fixture", str(collider), "--output", str(out),
            ]
            with redirect_stdout(StringIO()):
                self.assertEqual(main(command), 0)
            result = json.loads(out.read_text())["trajectory_proxy"]
            self.assertEqual(result["source_sha256"], sha256(source).hexdigest())
            self.assertEqual(result["collision_fixture_sha256"],
                             sha256(fixture).hexdigest())
            self.assertEqual(result["status"], "possible_chord_obstacle_overlap")
            saved = out.read_bytes()
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(command)
            self.assertEqual(out.read_bytes(), saved)
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(command[:-1] + [str(trajectory)])
            self.assertEqual(trajectory.read_bytes(), source)
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(["robot-model", "--urdf", str(urdf),
                      "--expected-sha256", sha256(raw).hexdigest(),
                      "--trajectory", str(trajectory), "--output",
                      str(root / "unused.json")])
            self.assertFalse((root / "unused.json").exists())
            invalid = dict(document)
            invalid["waypoints"] = [
                document["waypoints"][0],
                {"time_s": 1, "joint_positions": {"slider": 2.5}},
            ]
            trajectory.write_text(json.dumps(invalid))
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(command[:-1] + [str(root / "bad.json")])
            self.assertFalse((root / "bad.json").exists())

    def test_trajectory_json_rejects_duplicates_nonfinite_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "input.json"
            for raw in [
                b'{"schema_version":"1.0.0","schema_version":"1.0.0"}',
                b'{"waypoints":[{"time_s":NaN}]}',
                b'bad_json',
            ]:
                path.write_bytes(raw)
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    load_trajectory(path)
            path.write_bytes(b"X" * 65537)
            with self.assertRaises(ValueError):
                load_trajectory(path)
            path.write_text('{"schema_version":"1.0.0","waypoints":[]}')
            link = root / "link.json"
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                load_trajectory(link)


if __name__ == "__main__":
    unittest.main()
