"""Analytic independent 2D circular-arc/rectangle reference for FK proxy QA.

This reference does NOT call the implementation's Lipschitz bound,
chord algorithm or recursive FK evaluation. It only models one known
revolute circle in a fixed virtual plane with a cylindrical z overlap.
"""

from __future__ import annotations

from hashlib import sha256
from math import acos, asin, atan2, ceil, cos, floor, hypot, pi, sin
from pathlib import Path
import tempfile
import unittest

from rvi.robot_model import inspect_urdf
from rvi.trajectory import inspect_rotary_proxy_sweep


UNIT_ARM = """<robot name="independent_analytic_orbit">
<link name="base"/><link name="arm"/><link name="tip"/>
<joint name="q" type="revolute">
<parent link="base"/><child link="arm"/><axis xyz="0 0 1"/>
<limit lower="-2" upper="2"/>
</joint>
<joint name="tip_mount" type="fixed">
<parent link="arm"/><child link="tip"/><origin xyz="1 0 0"/>
</joint>
</robot>"""


def _arc_box_gap(start: float, stop: float,
                 box: tuple[float, float, float, float],
                 sphere_radius: float) -> float:
    """Reference minimum sphere–rectangle clearance along a unit circular arc.

    Splits the analytic distance-to-AABB curve at coordinate boundaries.
    Inside each cell the squared distance is a linear combination of
    cos(theta), sin(theta), 1 or cos(2theta)/sin(2theta).
    Stationary points occur at rectangle-corner bearing angles and
    cardinal directions; section boundaries occur where the orbit
    crosses each rectangle side coordinate.
    """
    xmin, xmax, ymin, ymax = box
    if not (-2 <= start < stop <= 2 and xmin < xmax and ymin < ymax):
        raise ValueError("unsupported analytic test domain")
    candidates = [start, stop]
    cardinal = [0, pi / 2, pi, 3 * pi / 2]
    for x in (xmin, xmax):
        if abs(x) <= 1:
            theta = acos(x)
            cardinal.extend([theta, -theta])
    for y in (ymin, ymax):
        if abs(y) <= 1:
            theta = asin(y)
            cardinal.extend([theta, pi - theta])
    for x in (xmin, xmax):
        for y in (ymin, ymax):
            angle = atan2(y, x)
            cardinal.extend([angle, angle + pi])
    for angle in cardinal:
        minimum_shift = floor((start - angle) / (2 * pi)) - 1
        maximum_shift = ceil((stop - angle) / (2 * pi)) + 1
        for k in range(minimum_shift, maximum_shift + 1):
            value = angle + 2 * pi * k
            if start <= value <= stop:
                candidates.append(value)
    distance = min(
        hypot(
            max(xmin - cos(theta), 0, cos(theta) - xmax),
            max(ymin - sin(theta), 0, sin(theta) - ymax),
        )
        for theta in candidates
    )
    return distance - sphere_radius


def _fixture(box: tuple[float, float, float, float],
             radius: float = 0.1) -> dict:
    xmin, xmax, ymin, ymax = box
    return {
        "schema_version": "1.0.0",
        "clearance_margin_m": 0.0,
        "spheres": [
            {"id": "orbit", "link": "tip", "center_local_m": [0, 0, 0],
             "radius_m": radius},
        ],
        "boxes": [
            {"id": "rectangle", "min_xyz_m": [xmin, ymin, -0.02],
             "max_xyz_m": [xmax, ymax, 0.02]},
        ],
        "self_pairs": [],
    }


class IndependentRotaryReferenceTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.path = Path(self.workspace.name) / "unit_arm.urdf"
        raw = UNIT_ARM.encode("utf-8")
        self.path.write_bytes(raw)
        self.digest = sha256(raw).hexdigest()

    def forward_pose(self, positions: dict) -> dict:
        return inspect_urdf(self.path, self.digest,
                            joint_positions=positions)["configured_joint_pose"]

    def audit(self, angle_start: float, angle_stop: float,
              fixture: dict, limit: int = 64) -> dict:
        poses = [self.forward_pose({"q": angle_start}),
                 self.forward_pose({"q": angle_stop})]
        return inspect_rotary_proxy_sweep(
            poses, fixture, self.forward_pose, max_evaluations=limit)

    def test_reference_has_known_exact_distances(self):
        # The unit arc at q=0 passes through (1,0).
        examples = [
            ((0.95, 1.05, -0.05, 0.05), 0.1, -0.1),
            ((1.10, 1.20, -0.05, 0.05), 0.1, 0.0),
            ((1.25, 1.35, -0.05, 0.05), 0.1, 0.15),
            ((-1.35, -1.25, -0.05, 0.05), 0.1, 1.15),
        ]
        for box, radius, expected in examples:
            with self.subTest(box=box):
                reference = _arc_box_gap(-pi / 2, pi / 2, box, radius)
                self.assertAlmostEqual(reference, expected, places=12)

    def test_independent_arc_overlap_never_gets_proxy_clear(self):
        cases = [
            (-pi / 2, pi / 2, (0.95, 1.05, -0.05, 0.05)),
            (-pi / 2, pi / 2, (0.7, 0.8, 0.7, 0.8)),
            (-1.8, 1.8, (0.9, 1.0, -0.15, 0.15)),
            (0, 1.5, (0.0, 0.15, 0.9, 1.1)),
            (-pi / 2, pi / 2, (0.75, 0.85, 0.75, 0.85)),
        ]
        for start, stop, box in cases:
            with self.subTest(start=start, stop=stop, box=box):
                reference = _arc_box_gap(start, stop, box, 0.1)
                self.assertLess(reference, -1e-6)
                result = self.audit(start, stop, _fixture(box))
                self.assertNotEqual(result["status"],
                                    "declared_proxies_only_screened")
                self.assertIn(result["status"], (
                    "proxy_overlap_between_waypoints",
                    "rotary_sweep_unresolved",
                ))
                self.assertEqual(
                    result["full_body_or_robot_motion_certification"],
                    "not_performed")

    def test_tangent_near_miss_and_budget_guard(self):
        boxes = [
            (1.10, 1.20, -0.05, 0.05),  # tangent at zero
            (1.100001, 1.20, -0.05, 0.05),  # 1 micrometre gap
            (1.099999, 1.20, -0.05, 0.05),  # 1 micrometre overlap
        ]
        for box in boxes:
            with self.subTest(box=box):
                gap = _arc_box_gap(-pi / 2, pi / 2, box, 0.1)
                self.assertAlmostEqual(gap, box[0] - 1.1, places=12)
                result = self.audit(-pi / 2, pi / 2, _fixture(box))
                if gap <= 1e-10:
                    self.assertNotEqual(result["status"],
                                        "declared_proxies_only_screened")
                self.assertLessEqual(result["total_evaluations"], 64)
                no_budget = self.audit(-pi / 2, pi / 2, _fixture(box), 0)
                self.assertEqual(no_budget["status"], "rotary_sweep_unresolved")

    def test_far_analytic_clear_is_only_proxy_clear(self):
        cases = [
            (-pi / 2, pi / 2, (10.0, 11.0, -0.1, 0.1)),
            (-1.5, 1.5, (-10.0, -9.0, -1, 1)),
            (-pi / 2, pi / 2, (0.9, 1.0, 10, 11)),
        ]
        for start, stop, box in cases:
            with self.subTest(box=box):
                self.assertGreater(_arc_box_gap(start, stop, box, 0.1), 0)
                result = self.audit(start, stop, _fixture(box), 0)
                self.assertEqual(result["status"],
                                 "declared_proxies_only_screened")
                self.assertEqual(result["total_evaluations"], 0)

    def test_midpoint_test_retains_source_pose_units(self):
        fixture = _fixture((0.95, 1.05, -0.05, 0.05))
        first = self.forward_pose({"q": -pi / 2})
        last = self.forward_pose({"q": pi / 2})
        self.assertEqual(first["movable_joint_types"], {"q": "revolute"})
        self.assertAlmostEqual(first["all_joint_origin_length_sum_m"], 1)
        report = inspect_rotary_proxy_sweep([first, last], fixture,
                                            self.forward_pose)
        self.assertEqual(report["segments"][0]["collision_fraction"], 0.5)
        self.assertEqual(report["assumed_joint_motion"],
                         "linear_interpolation_fixed_virtual_base")


if __name__ == "__main__":
    unittest.main()
