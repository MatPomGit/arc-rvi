"""Independent 3D multi-axis analytic and interval references for P03 proxy sweeps.

This module does NOT import the implementation's FK matrices, velocity
bound, recursive splitter or collision distance. Synthetic 2-DoF
forward positions are independently derived from trigonometry.
"""

from __future__ import annotations

from hashlib import sha256
from math import cos, floor, hypot, pi, sin, sqrt
from pathlib import Path
import tempfile
import unittest

from rvi.robot_model import inspect_urdf
from rvi.trajectory import inspect_rotary_proxy_sweep


GIMBAL = """<robot name="two_axis_analytic_3d">
<link name="base"/><link name="yaw_link"/><link name="pitch_link"/><link name="tip"/>
<joint name="yaw" type="revolute">
  <parent link="base"/><child link="yaw_link"/><axis xyz="0 0 1"/>
  <limit lower="-2" upper="2"/>
</joint>
<joint name="pitch" type="revolute">
  <parent link="yaw_link"/><child link="pitch_link"/><axis xyz="0 1 0"/>
  <limit lower="-2" upper="2"/>
</joint>
<joint name="tip_mount" type="fixed">
  <parent link="pitch_link"/><child link="tip"/><origin xyz="1 0 0"/>
</joint></robot>"""

TWO_ARMS = """<robot name="independent_two_arm_reference">
<link name="base"/><link name="yaw_link"/><link name="pitch_link"/>
<link name="yaw_tip"/><link name="pitch_tip"/>
<joint name="yaw" type="revolute">
  <parent link="base"/><child link="yaw_link"/><axis xyz="0 0 1"/>
  <limit lower="-2" upper="2"/>
</joint>
<joint name="pitch" type="revolute">
  <parent link="base"/><child link="pitch_link"/><axis xyz="0 1 0"/>
  <limit lower="-2" upper="2"/>
</joint>
<joint name="a_mount" type="fixed">
  <parent link="yaw_link"/><child link="yaw_tip"/><origin xyz="1 0 0"/>
</joint>
<joint name="b_mount" type="fixed">
  <parent link="pitch_link"/><child link="pitch_tip"/><origin xyz="1 0 0"/>
</joint></robot>"""


def analytic_gimbal(yaw: float, pitch: float) -> tuple[float, float, float]:
    """Analytic Rz(yaw)Ry(pitch)(1,0,0), without robot-model transforms."""
    return (cos(yaw) * cos(pitch), sin(yaw) * cos(pitch), -sin(pitch))


def point_box_gap(point: tuple[float, float, float], box: tuple,
                  radius: float) -> float:
    """Independent Euclidean sphere-to-AABB gap (metres)."""
    mins, maxs = box
    return sqrt(sum(max(lo - value, 0.0, value - hi) ** 2
                    for value, lo, hi in zip(point, mins, maxs))) - radius


def trig_range(lo: float, hi: float, *, cosine: bool) -> tuple[float, float]:
    """Extrema of a scalar trig function over a closed angle interval.

    Joint interpolation can run in either direction. Normalize both
    bounds before looking for interior stationary extrema.
    """
    lo, hi = sorted((lo, hi))
    func = cos if cosine else sin
    values = [func(lo), func(hi)]
    start = floor((lo - pi / 2) / (pi / 2)) - 2
    end = floor((hi + pi / 2) / (pi / 2)) + 2
    for k in range(start, end + 1):
        stationary = k * pi if cosine else pi / 2 + k * pi
        if lo <= stationary <= hi:
            values.append(func(stationary))
    return min(values), max(values)


def product_interval(a: tuple[float, float],
                     b: tuple[float, float]) -> tuple[float, float]:
    products = [x * y for x in a for y in b]
    return min(products), max(products)


def analytic_gimbal_enclosure(yaw_range: tuple[float, float],
                              pitch_range: tuple[float, float]) -> tuple:
    """Independent interval enclosure of the whole 3D gimbal arc."""
    c_yaw = trig_range(*yaw_range, cosine=True)
    s_yaw = trig_range(*yaw_range, cosine=False)
    c_pitch = trig_range(*pitch_range, cosine=True)
    s_pitch = trig_range(*pitch_range, cosine=False)
    return (product_interval(c_yaw, c_pitch),
            product_interval(s_yaw, c_pitch),
            (-s_pitch[1], -s_pitch[0]))


def enclosure_gap(enclosure: tuple, box: tuple, radius: float) -> float:
    """Lower bound on distance between an interval box and obstacle AABB."""
    mins, maxs = box
    return sqrt(sum(max(lo - interval[1], 0.0, interval[0] - hi) ** 2
                    for interval, lo, hi in zip(enclosure, mins, maxs))) - radius


def independent_interval_clear(a: tuple, b: tuple, box: tuple,
                               radius: float, cells: int = 64) -> bool:
    """Sufficient (not necessary) collision-exclusion test without FK/bounds.

    Each segment encloses exact analytic trig coordinate extrema. Returning
    False means unknown or possible contact, never proof of collision.
    """
    if cells < 1:
        raise ValueError("requires at least one interval")
    for i in range(cells):
        start, end = i / cells, (i + 1) / cells
        yaw = (a[0] + start * (b[0] - a[0]),
               a[0] + end * (b[0] - a[0]))
        pitch = (a[1] + start * (b[1] - a[1]),
                 a[1] + end * (b[1] - a[1]))
        if enclosure_gap(analytic_gimbal_enclosure(yaw, pitch),
                         box, radius) <= 1e-10:
            return False
    return True


def gimbal_fixture(box: tuple, radius: float = 0.1) -> dict:
    return {
        "schema_version": "1.0.0", "clearance_margin_m": 0.0,
        "spheres": [{"id": "tip_ball", "link": "tip",
                     "center_local_m": [0, 0, 0], "radius_m": radius}],
        "boxes": [{"id": "beam", "min_xyz_m": list(box[0]),
                   "max_xyz_m": list(box[1])}],
        "self_pairs": [],
    }


class MultiAxisIndependentReferences(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def model(self, xml: str):
        path = self.root / "fixture.urdf"
        raw = xml.encode("utf-8")
        path.write_bytes(raw)
        digest = sha256(raw).hexdigest()

        def fk(joints: dict) -> dict:
            return inspect_urdf(path, digest,
                                joint_positions=joints)["configured_joint_pose"]

        return fk

    def test_orthogonal_3d_fk_against_closed_form_at_distinct_angles(self):
        fk = self.model(GIMBAL)
        for yaw, pitch in [
            (0.0, 0.0), (-1.4, 1.4), (1.4, -1.4),
            (0.8, 0.4), (-0.7, -1.2), (pi / 2, pi / 2),
        ]:
            with self.subTest(yaw=yaw, pitch=pitch):
                from_model = fk({"yaw": yaw, "pitch": pitch})
                actual = from_model["frame_poses"]["tip"]["translation_m"]
                target = analytic_gimbal(yaw, pitch)
                for computed, oracle in zip(actual, target):
                    self.assertAlmostEqual(computed, oracle, places=12)
                self.assertTrue(from_model["all_joint_origin_length_sum_m"] >= 1)

    def test_two_rotary_axes_cross_obstacle_while_endpoint_chord_is_clear(self):
        fk = self.model(GIMBAL)
        a, b = {"yaw": -1.4, "pitch": -1.4}, {"yaw": 1.4, "pitch": 1.4}
        box = ((0.95, -0.05, -0.05), (1.05, 0.05, 0.05))
        self.assertLess(point_box_gap(analytic_gimbal(0, 0), box, 0.1), 0)
        self.assertGreater(point_box_gap(analytic_gimbal(**a), box, 0.1), 0)
        self.assertGreater(point_box_gap(analytic_gimbal(**b), box, 0.1), 0)
        # Endpoint x ~= 0.029, whereas the true curved path reaches x=1.
        self.assertLess(analytic_gimbal(**a)[0], 0.05)
        self.assertLess(analytic_gimbal(**b)[0], 0.05)
        sweep = inspect_rotary_proxy_sweep(
            [fk(a), fk(b)], gimbal_fixture(box), fk)
        self.assertEqual(sweep["status"], "proxy_overlap_between_waypoints")
        self.assertAlmostEqual(sweep["segments"][0]["collision_fraction"], 0.5)

    def test_two_arm_3d_self_contact_not_visible_at_endpoints(self):
        fk = self.model(TWO_ARMS)
        a, b = {"yaw": -1.4, "pitch": 1.4}, {"yaw": 1.4, "pitch": -1.4}
        # At the analytic midpoint both independent tips are (1,0,0).
        # At endpoints their separation is sqrt(2)*sin(1.4).
        gap = sqrt(2) * sin(1.4) - 0.2
        self.assertGreater(gap, 1)
        fixture = {
            "schema_version": "1.0.0", "clearance_margin_m": 0.0,
            "spheres": [
                {"id": "az", "link": "yaw_tip",
                 "center_local_m": [0, 0, 0], "radius_m": 0.1},
                {"id": "by", "link": "pitch_tip",
                 "center_local_m": [0, 0, 0], "radius_m": 0.1},
            ], "boxes": [], "self_pairs": [["az", "by"]],
        }
        sweep = inspect_rotary_proxy_sweep([fk(a), fk(b)], fixture, fk)
        self.assertEqual(sweep["status"], "proxy_overlap_between_waypoints")
        self.assertAlmostEqual(sweep["segments"][0]["collision_fraction"], 0.5)

    def test_3d_analytical_contact_near_tangent_is_not_false_clear(self):
        fk = self.model(GIMBAL)
        a, b = {"yaw": -1.4, "pitch": -1.4}, {"yaw": 1.4, "pitch": 1.4}
        for delta in (-1e-6, 0.0, 1e-6):
            box = ((1.1 + delta, -0.05, -0.05),
                   (1.2, 0.05, 0.05))
            truth_at_zero = point_box_gap(analytic_gimbal(0, 0), box, 0.1)
            self.assertAlmostEqual(truth_at_zero, delta, places=11)
            outcome = inspect_rotary_proxy_sweep(
                [fk(a), fk(b)], gimbal_fixture(box), fk, max_evaluations=64)
            if delta <= 0:
                self.assertNotEqual(outcome["status"],
                                    "declared_proxies_only_screened")
            self.assertLessEqual(outcome["total_evaluations"], 64)
            unresolved = inspect_rotary_proxy_sweep(
                [fk(a), fk(b)], gimbal_fixture(box), fk, max_evaluations=0)
            self.assertEqual(unresolved["status"], "rotary_sweep_unresolved")

    def test_independent_interval_exclusions_and_known_inclusions(self):
        fk = self.model(GIMBAL)
        a, b = {"yaw": -1.2, "pitch": -0.8}, {"yaw": 1.3, "pitch": 0.7}
        box_distant = ((10, -1, -1), (10.2, 1, 1))
        self.assertTrue(independent_interval_clear(
            tuple(a.values()), tuple(b.values()), box_distant, 0.1))
        result = inspect_rotary_proxy_sweep(
            [fk(a), fk(b)], gimbal_fixture(box_distant), fk,
            max_evaluations=0)
        self.assertEqual(result["status"], "declared_proxies_only_screened")
        at_middle = analytic_gimbal((a["yaw"] + b["yaw"]) / 2,
                                    (a["pitch"] + b["pitch"]) / 2)
        halfwidth = 0.03
        contact_box = (
            tuple(x - halfwidth for x in at_middle),
            tuple(x + halfwidth for x in at_middle),
        )
        self.assertFalse(independent_interval_clear(
            tuple(a.values()), tuple(b.values()), contact_box, 0.1))
        self.assertLess(point_box_gap(at_middle, contact_box, 0.1), 0)
        result = inspect_rotary_proxy_sweep(
            [fk(a), fk(b)], gimbal_fixture(contact_box), fk)
        self.assertNotEqual(result["status"],
                            "declared_proxies_only_screened")

    def test_extreme_world_coordinates_fail_closed_instead_of_false_clear(self):
        fk = self.model(GIMBAL)
        a, b = {"yaw": -1.0, "pitch": -1.0}, {"yaw": 1.0, "pitch": 1.0}
        poses = [fk(a), fk(b)]
        for extent in (1_000_001, 1e12, 1e150):
            box = ((extent, -0.05, -0.05), (extent + 1, 0.05, 0.05))
            with self.subTest(extent=extent):
                result = inspect_rotary_proxy_sweep(
                    poses, gimbal_fixture(box), fk, max_evaluations=0)
                self.assertEqual(result["status"], "rotary_sweep_unresolved")
                self.assertEqual(result["segments"][0]["status"],
                                 "unresolved_invalid_bound")
                self.assertEqual(result["total_evaluations"], 0)
                self.assertEqual(result["numeric_model_limit_m"], 1_000_000)

    def test_invalid_model_scale_and_link_offset_fail_closed(self):
        fk = self.model(GIMBAL)
        poses = [fk({"yaw": -1.0, "pitch": -1.0}),
                 fk({"yaw": 1.0, "pitch": 1.0})]
        for bad in (float("nan"), float("inf"), -1, 1e20):
            with self.subTest(bad=bad):
                changed = [dict(p) for p in poses]
                for p in changed:
                    p["all_joint_origin_length_sum_m"] = bad
                result = inspect_rotary_proxy_sweep(
                    changed, gimbal_fixture(((10, 0, 0), (11, 1, 1))), fk)
                self.assertEqual(result["status"], "rotary_sweep_unresolved")
                self.assertEqual(result["segments"][0]["status"],
                                 "unresolved_invalid_bound")
        # The zero and midpoint samples can be fully finite while local
        # proxy geometry itself violates the audited arithmetic envelope.
        huge_sphere = gimbal_fixture(((10, 0, 0), (11, 1, 1)))
        huge_sphere["spheres"][0]["center_local_m"] = [1e12, 0, 0]
        result = inspect_rotary_proxy_sweep(poses, huge_sphere, fk)
        self.assertEqual(result["status"], "rotary_sweep_unresolved")

    def test_extreme_continuous_joint_angles_fail_closed(self):
        xml = GIMBAL.replace('type="revolute"', 'type="continuous"')
        fk = self.model(xml)
        poses = [fk({"yaw": 101.0, "pitch": 0.0}),
                 fk({"yaw": 102.0, "pitch": 0.0})]
        result = inspect_rotary_proxy_sweep(
            poses, gimbal_fixture(((10, 0, 0), (11, 1, 1))), fk)
        self.assertEqual(result["status"], "rotary_sweep_unresolved")
        self.assertEqual(result["segments"][0]["status"],
                         "unresolved_invalid_bound")
        self.assertEqual(result["numeric_joint_angle_limit_rad"], 100)

    def test_tiny_contact_perturbations_do_not_create_false_clear(self):
        fk = self.model(GIMBAL)
        a, b = {"yaw": -1.4, "pitch": -1.4}, {"yaw": 1.4, "pitch": 1.4}
        poses = [fk(a), fk(b)]
        for perturbation in (-1e-7, -1e-9, -1e-11, 0.0, 1e-11):
            box = ((1.1 + perturbation, -0.05, -0.05),
                   (1.2, 0.05, 0.05))
            with self.subTest(perturbation=perturbation):
                analytic_gap = point_box_gap(analytic_gimbal(0, 0), box, 0.1)
                self.assertAlmostEqual(analytic_gap, perturbation, places=12)
                report = inspect_rotary_proxy_sweep(
                    poses, gimbal_fixture(box), fk, max_evaluations=64)
                if analytic_gap <= 0:
                    self.assertNotEqual(report["status"],
                                        "declared_proxies_only_screened")
                self.assertLessEqual(report["total_evaluations"], 64)
                self.assertEqual(report["full_body_or_robot_motion_certification"],
                                 "not_performed")

    def test_reverse_interval_oracle_keeps_interior_extrema(self):
        # A descending yaw from +1.4 to -1.4 passes through yaw=0.
        # With a single analytic cell, endpoint-only extrema would
        # incorrectly exclude the x=1 midpoint of this unit gimbal.
        self.assertAlmostEqual(
            trig_range(1.4, -1.4, cosine=True)[1], 1.0, places=12
        )
        self.assertAlmostEqual(
            trig_range(1.4, -1.4, cosine=True)[0],
            cos(1.4), places=12,
        )
        center = analytic_gimbal(0.0, 0.0)
        box = (
            tuple(value - 0.005 for value in center),
            tuple(value + 0.005 for value in center),
        )
        self.assertLess(point_box_gap(center, box, 0.01), -0.009)
        for first, last in (
            ((-1.4, -1.4), (1.4, 1.4)),
            ((1.4, 1.4), (-1.4, -1.4)),
        ):
            for cells in (1, 3, 8, 64):
                with self.subTest(first=first, last=last, cells=cells):
                    self.assertFalse(independent_interval_clear(
                        first, last, box, 0.01, cells=cells
                    ))

    def test_bidirectional_adversarial_contact_grid_never_false_clear(self):
        # Exact contact witnesses are obtained analytically at t=1/4,
        # 1/2 and 3/4, not by using production FK or dense sampling.
        fk = self.model(GIMBAL)
        paths = (
            (-1.4, 1.4, -1.4, 1.4),
            (-1.3, 1.1, 1.0, -1.2),
            (0.0, 1.5, -1.5, 0.8),
            (1.4, -0.9, -0.8, 1.2),
        )
        radius = 0.06
        for y0, y1, p0, p1 in paths:
            forward = ({"yaw": y0, "pitch": p0},
                       {"yaw": y1, "pitch": p1})
            for fraction in (0.25, 0.5, 0.75):
                witness = analytic_gimbal(
                    y0 + fraction * (y1 - y0),
                    p0 + fraction * (p1 - p0),
                )
                box = (
                    tuple(value - 0.015 for value in witness),
                    tuple(value + 0.015 for value in witness),
                )
                # This exact known point lies inside the AABB; a
                # proxy-only-clear result is therefore a counterexample.
                self.assertAlmostEqual(
                    point_box_gap(witness, box, radius),
                    -radius, places=12,
                )
                fixture = gimbal_fixture(box, radius)
                for a, b in (forward, forward[::-1]):
                    for cells in (1, 8):
                        self.assertFalse(independent_interval_clear(
                            (a["yaw"], a["pitch"]),
                            (b["yaw"], b["pitch"]),
                            box, radius, cells=cells,
                        ))
                    poses = [fk(a), fk(b)]
                    for budget in (0, 4, 64):
                        with self.subTest(
                            start=a, stop=b, fraction=fraction,
                            evaluations=budget,
                        ):
                            result = inspect_rotary_proxy_sweep(
                                poses, fixture, fk, max_evaluations=budget
                            )
                            self.assertNotEqual(
                                result["status"],
                                "declared_proxies_only_screened",
                            )
                            self.assertIn(result["status"], (
                                "proxy_overlap_between_waypoints",
                                "proxy_overlap_at_waypoint",
                                "rotary_sweep_unresolved",
                            ))
                            self.assertLessEqual(
                                result["total_evaluations"], budget
                            )
                            self.assertEqual(
                                result["full_body_or_robot_motion_certification"],
                                "not_performed",
                            )

    def test_deterministic_multi_axis_interior_contact_family(self):
        fk = self.model(GIMBAL)
        # Multiple approach directions, no endpoint oracle/truth leakage.
        cases = [
            (-1.3, 1.1, -1.0, 1.2),
            (-1.6, 1.4, 0.9, -1.3),
            (0.0, 1.5, -1.5, 0.8),
            (-0.8, 0.7, 0.6, -0.7),
            (1.5, -1.2, -1.4, 1.0),
            (-1.4, 1.6, 1.5, -1.4),
        ]
        for ya, yb, pa, pb in cases:
            with self.subTest(yaw=(ya, yb), pitch=(pa, pb)):
                a, b = {"yaw": ya, "pitch": pa}, {"yaw": yb, "pitch": pb}
                ref = analytic_gimbal((ya + yb) / 2, (pa + pb) / 2)
                box = (tuple(x - 0.015 for x in ref),
                       tuple(x + 0.015 for x in ref))
                self.assertLess(point_box_gap(ref, box, 0.06), 0)
                report = inspect_rotary_proxy_sweep(
                    [fk(a), fk(b)], gimbal_fixture(box, 0.06), fk)
                self.assertNotEqual(report["status"],
                                    "declared_proxies_only_screened")
                self.assertIn(report["status"], (
                    "proxy_overlap_between_waypoints",
                    "rotary_sweep_unresolved",
                ))
                self.assertEqual(report["coverage"],
                                 "declared_spheres_AABBs_and_explicit_self_pairs_only")


if __name__ == "__main__":
    unittest.main()
