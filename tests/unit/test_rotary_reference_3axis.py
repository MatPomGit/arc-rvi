"""Independent three-axis FK and rotary contact reference for P03 #100.

This test oracle uses direct trigonometry, not production FK matrices,
Lipschitz displacement bounds or adaptive subdivision. Synthetic only.
"""
from __future__ import annotations

from hashlib import sha256
from math import cos, dist, sin, sqrt
from pathlib import Path
import tempfile
import unittest

from rvi.robot_model import inspect_urdf
from rvi.trajectory import inspect_rotary_proxy_sweep


THREE_AXIS = """<robot name="independent_xyz_gimbal">
<link name="base"/><link name="yaw_link"/><link name="pitch_link"/>
<link name="roll_link"/><link name="tip"/>
<joint name="yaw" type="revolute">
  <parent link="base"/><child link="yaw_link"/>
  <axis xyz="0 0 1"/><limit lower="-2" upper="2"/>
</joint>
<joint name="pitch" type="revolute">
  <parent link="yaw_link"/><child link="pitch_link"/>
  <axis xyz="0 1 0"/><limit lower="-2" upper="2"/>
</joint>
<joint name="roll" type="revolute">
  <parent link="pitch_link"/><child link="roll_link"/>
  <axis xyz="1 0 0"/><limit lower="-2" upper="2"/>
</joint>
<joint name="tip_mount" type="fixed">
  <parent link="roll_link"/><child link="tip"/>
  <origin xyz="1 1 1"/>
</joint>
</robot>"""


def analytic_tip(yaw: float, pitch: float, roll: float) -> tuple:
    """Closed form Rz(yaw) Ry(pitch) Rx(roll) (1, 1, 1)."""
    yr = cos(roll) - sin(roll)
    zr = sin(roll) + cos(roll)
    xp = cos(pitch) + sin(pitch) * zr
    zp = -sin(pitch) + cos(pitch) * zr
    return (cos(yaw) * xp - sin(yaw) * yr,
            sin(yaw) * xp + cos(yaw) * yr, zp)


def at_fraction(first: dict, last: dict, fraction: float) -> dict:
    """Compute a test-only linear joint interpolation."""
    return {name: first[name] + (last[name] - first[name]) * fraction
            for name in first}


def box_near(center: tuple, radius: float = 0.1) -> dict:
    return {
        "schema_version": "1.0.0", "clearance_margin_m": 0.0,
        "spheres": [{
            "id": "ball", "link": "tip", "center_local_m": [0, 0, 0],
            "radius_m": radius,
        }],
        "boxes": [{
            "id": "box",
            "min_xyz_m": [value - 0.025 for value in center],
            "max_xyz_m": [value + 0.025 for value in center],
        }],
        "self_pairs": [],
    }


class ThreeAxisReferenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "three_axis.urdf"
        raw = THREE_AXIS.encode("utf-8")
        self.path.write_bytes(raw)
        self.digest = sha256(raw).hexdigest()

    def fk(self, joints: dict) -> dict:
        return inspect_urdf(
            self.path, self.digest, joint_positions=joints
        )["configured_joint_pose"]

    def sweep(self, first: dict, last: dict, obstacle: dict,
              budget: int = 64) -> dict:
        return inspect_rotary_proxy_sweep(
            [self.fk(first), self.fk(last)], obstacle, self.fk,
            max_evaluations=budget,
        )

    def test_three_distinct_rotary_axes_against_closed_form(self):
        angles = (
            (0.0, 0.0, 0.0), (-0.9, -0.8, -0.7),
            (0.9, 0.8, 0.7), (-1.2, -0.9, -0.5),
            (1.2, 0.9, 0.5), (0.7, -0.6, 1.1),
            (-0.4, 1.2, -0.8),
        )
        for yaw, pitch, roll in angles:
            with self.subTest(yaw=yaw, pitch=pitch, roll=roll):
                observed = self.fk(
                    {"yaw": yaw, "pitch": pitch, "roll": roll}
                )["frame_poses"]["tip"]["translation_m"]
                expected = analytic_tip(yaw, pitch, roll)
                for actual, reference in zip(observed, expected):
                    self.assertAlmostEqual(actual, reference, places=11)
                self.assertAlmostEqual(
                    sqrt(sum(value * value for value in observed)),
                    sqrt(3), places=11,
                )

    def test_interior_three_axis_contact_cannot_be_proxy_clear(self):
        paths = (
            ({"yaw": -0.9, "pitch": -0.8, "roll": -0.7},
             {"yaw": 0.9, "pitch": 0.8, "roll": 0.7}, 0.5),
            ({"yaw": -1.2, "pitch": -0.8, "roll": -0.7},
             {"yaw": 0.8, "pitch": 0.6, "roll": 0.9}, 0.25),
        )
        for first, last, fraction in paths:
            with self.subTest(fraction=fraction):
                center = analytic_tip(**at_fraction(first, last, fraction))
                self.assertGreater(dist(analytic_tip(**first), center), 0.2)
                self.assertGreater(dist(analytic_tip(**last), center), 0.2)
                result = self.sweep(first, last, box_near(center))
                self.assertNotEqual(
                    result["status"], "declared_proxies_only_screened"
                )
                self.assertLessEqual(result["total_evaluations"], 64)
                self.assertEqual(
                    result["full_body_or_robot_motion_certification"],
                    "not_performed",
                )

    def test_tangent_contact_and_zero_budget_fail_closed(self):
        first = {"yaw": -0.9, "pitch": -0.8, "roll": -0.7}
        last = {"yaw": 0.9, "pitch": 0.8, "roll": 0.7}
        for delta in (-1e-6, 0.0):
            with self.subTest(delta=delta):
                # Midpoint is analytically (1,1,1); box begins at
                # x=1.1+delta and sphere radius is 0.1 metres.
                fixture = box_near((1.125 + delta, 1.0, 1.0))
                fixture["boxes"][0]["min_xyz_m"][0] = 1.1 + delta
                fixture["boxes"][0]["max_xyz_m"][0] = 1.2
                result = self.sweep(first, last, fixture)
                self.assertNotEqual(
                    result["status"], "declared_proxies_only_screened"
                )
                blocked = self.sweep(first, last, fixture, budget=0)
                self.assertEqual(blocked["status"], "rotary_sweep_unresolved")

    def test_far_3d_obstacle_is_only_declared_proxy_clear(self):
        first = {"yaw": -0.9, "pitch": -0.8, "roll": -0.7}
        last = {"yaw": 0.9, "pitch": 0.8, "roll": 0.7}
        result = self.sweep(
            first, last, box_near((10, 0, 0)), budget=0
        )
        self.assertEqual(result["status"], "declared_proxies_only_screened")
        self.assertEqual(result["total_evaluations"], 0)
        self.assertEqual(
            result["coverage"],
            "declared_spheres_AABBs_and_explicit_self_pairs_only",
        )


if __name__ == "__main__":
    unittest.main()
