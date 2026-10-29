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
    """Extrema of a scalar trig function over a closed angle interval."""
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
        box_distant = ((4, -1, -1), (4.2, 1, 1))
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
