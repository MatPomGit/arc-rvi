"""Analytic scenes with independently specified geometric and timing outcomes."""

from dataclasses import replace
from math import pi, sqrt
from pathlib import Path
import json
import tempfile
import unittest

from rvi.adapters.simulator import (CameraModel, Circle, MotionModel, PlanarScene,
                                   PlanarSimulator, SurfacePatch, run_simulation)
from rvi.geometry import angular_distance, segment_distance
from rvi.interfaces import CameraPose, SimulatorAdapter

ROOT = Path(__file__).resolve().parents[2]


def scene(**changes):
    nominal = PlanarScene(
        "analytic", CameraPose(0, 0, 0), CameraModel(pi / 2, 0.1, 10, pi / 3),
        MotionModel(1, 1, 0.2, 1, 100), (),
        (SurfacePatch("front", 3, 0, pi, 1),), ())
    return replace(nominal, **changes)


class GeometryTests(unittest.TestCase):
    def test_segment_projection_endpoints_and_zero_length(self):
        self.assertEqual(segment_distance((2, 3), (0, 0), (4, 0)), 3)
        self.assertEqual(segment_distance((-3, 4), (0, 0), (2, 0)), 5)
        self.assertEqual(segment_distance((5, 4), (0, 0), (2, 0)), 5)
        self.assertEqual(segment_distance((3, 4), (0, 0), (0, 0)), 5)
        self.assertAlmostEqual(segment_distance((1, 0), (0, 0), (1, 1)), sqrt(0.5))

    def test_shortest_rotation_and_equivalent_boundary_angles(self):
        self.assertAlmostEqual(angular_distance(170 * pi / 180, -170 * pi / 180), 20 * pi / 180)
        self.assertEqual(angular_distance(pi, -pi), 0)


class PlanarSimulatorTests(unittest.TestCase):
    def test_camera_range_fov_normal_and_degenerate_point(self):
        patches = (
            SurfacePatch("front", 3, 0, pi, 1),
            SurfacePatch("edge", 1, 1, -3 * pi / 4, 1),
            SurfacePatch("outside_fov", 0, 3, -pi / 2, 1),
            SurfacePatch("back_facing", 3, 0, 0, 1),
            SurfacePatch("too_far", 11, 0, pi, 1),
            SurfacePatch("too_near", 0.05, 0, pi, 1),
            SurfacePatch("coincident", 0, 0, pi, 1))
        simulator = PlanarSimulator(scene(patches=patches))
        self.assertEqual(simulator.visible_patches(CameraPose(0, 0, 0)), ("edge", "front"))
        rotated = simulator.visible_patches(CameraPose(0, 0, pi / 2))
        self.assertIn("outside_fov", rotated)
        self.assertNotIn("front", rotated)

    def test_exact_range_and_incidence_boundaries(self):
        camera = CameraModel(pi, 1, 3, pi / 2)
        patches = (SurfacePatch("near", 1, 0, pi, 1),
                   SurfacePatch("far", 3, 0, pi / 2, 1))
        simulator = PlanarSimulator(scene(camera=camera, patches=patches))
        self.assertEqual(simulator.visible_patches(CameraPose(0, 0, 0)), ("far", "near"))

    def test_occlusion_interior_tangent_and_behind_target(self):
        for obstacle, expected in ((Circle(1.5, 0, 0.1), ()),
                                   (Circle(1.5, 0.2, 0.2), ()),
                                   (Circle(4, 0, 0.1), ("front",))):
            with self.subTest(obstacle=obstacle):
                simulator = PlanarSimulator(scene(obstacles=(obstacle,)))
                self.assertEqual(simulator.visible_patches(CameraPose(0, 0, 0)), expected)

    def test_motion_sweep_detects_midpoint_and_robot_radius(self):
        # Both endpoints are clear. Only the swept disc touches the obstacle.
        simulator = PlanarSimulator(scene(obstacles=(Circle(2, 0.4, 0.2),)))
        result = simulator.acquire(CameraPose(4, 0, 0))
        self.assertEqual(result.failure_reason, "path_collision")
        self.assertEqual(result.pose, CameraPose(0, 0, 0))
        self.assertEqual(result.elapsed_time_s, 0)
        self.assertEqual(result.travel_distance_m, 0)
        self.assertEqual(result.visible_patch_ids, ())
        with self.assertRaises(ValueError):
            simulator.acquire(CameraPose(0, 1, 0))

    def test_translation_rotation_capture_time_and_reset(self):
        simulator = PlanarSimulator(scene(motion=MotionModel(2, pi / 2, 0.2, 0.5, 10)))
        self.assertIsInstance(simulator, SimulatorAdapter)
        result = simulator.acquire(CameraPose(3, 4, pi / 2))
        # Five metres / 2 m/s + quarter-turn / (pi/2 rad/s) + capture.
        self.assertEqual(result.elapsed_time_s, 4)
        self.assertEqual(result.travel_distance_m, 5)
        again = simulator.acquire(CameraPose(3, 4, pi / 2))
        self.assertEqual(again.elapsed_time_s, 4.5)
        simulator.reset()
        self.assertEqual(simulator.acquire(CameraPose(3, 4, pi / 2)), result)

    def test_time_budget_preserves_partial_state_and_accepts_boundary(self):
        simulator = PlanarSimulator(scene(motion=MotionModel(1, 1, 0.2, 1, 2)))
        first = simulator.acquire(CameraPose(1, 0, 0))
        self.assertEqual(first.elapsed_time_s, 2)
        self.assertIsNone(first.failure_reason)
        rejected = simulator.acquire(CameraPose(2, 0, 0))
        self.assertEqual(rejected.failure_reason, "time_budget_exceeded")
        self.assertEqual(rejected.elapsed_time_s, 2)
        self.assertEqual(rejected.travel_distance_m, 1)
        self.assertEqual(rejected.pose, first.pose)

    def test_decimal_time_boundary_allows_rounding_only(self):
        simulator = PlanarSimulator(scene(motion=MotionModel(1, 1, 0, 0.1, 0.3)))
        for _ in range(3):
            result = simulator.acquire(CameraPose(0, 0, 0))
            self.assertIsNone(result.failure_reason)
        self.assertAlmostEqual(result.elapsed_time_s, 0.3)
        self.assertEqual(simulator.acquire(CameraPose(0, 0, 0)).failure_reason,
                         "time_budget_exceeded")

    def test_zero_budget_and_equivalent_angle_allow_zero_duration_capture(self):
        simulator = PlanarSimulator(scene(start=CameraPose(0, 0, -pi),
                                          motion=MotionModel(1, 1, 0, 0, 0)))
        result = simulator.acquire(CameraPose(0, 0, pi))
        self.assertIsNone(result.failure_reason)
        self.assertEqual(result.elapsed_time_s, 0)

    def test_invalid_models_fail_before_acquisition(self):
        cases = (scene(camera=CameraModel(0, 0, 1, 0)),
                 scene(camera=CameraModel(pi, 2, 1, 0)),
                 scene(motion=MotionModel(0, 1, 0, 1, 2)),
                 scene(motion=MotionModel(1, True, 0, 1, 2)),
                 scene(start=CameraPose(0, 0, 2 * pi)),
                 scene(obstacles=(Circle(0, 0, 0.1),)),
                 scene(patches=()),
                 scene(patches=(SurfacePatch("a", 1, 0, pi, 0),)),
                 scene(patches=(SurfacePatch("a", 1, 0, pi, 1),) * 2))
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                PlanarSimulator(case)


class SimulationReportTests(unittest.TestCase):
    def test_demo_area_union_and_time(self):
        result = run_simulation(ROOT / "simulation/worlds/planar_inspection.json")
        self.assertEqual(result["evidence_type"], "simulation")
        self.assertEqual(result["model"], "planar_geometry_kinematics_v1")
        self.assertEqual(result["observations"][0]["visible_patch_ids"], ("lower",))
        self.assertEqual(result["observations"][1]["visible_patch_ids"], ("upper",))
        self.assertEqual(result["sampled_surface_coverage"], 1)
        self.assertEqual(result["elapsed_time_s"], 3)
        self.assertEqual(result["travel_distance_m"], 1)
        self.assertTrue(result["route_complete"])
        self.assertTrue(result["coverage_complete"])

    def test_partial_area_weighting_deduplication_and_failure(self):
        demo = json.loads((ROOT / "simulation/worlds/planar_inspection.json").read_text())
        # Repeated lower capture, then a rejected move. The 1 m2 patch counts once.
        demo["route"].insert(0, demo["route"][0])
        demo["motion"]["max_time_s"] = 2
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "scene.json"
            path.write_text(json.dumps(demo))
            result = run_simulation(path)
        self.assertEqual(result["sampled_surface_coverage"], 0.25)
        self.assertEqual(result["elapsed_time_s"], 2)
        self.assertEqual(result["covered_patch_ids"], ["lower"])
        self.assertEqual(result["missing_patch_ids"], ["upper"])
        self.assertEqual(result["failure_reason"], "time_budget_exceeded")
        self.assertFalse(result["route_complete"])
        self.assertFalse(result["coverage_complete"])

    def test_completed_route_can_have_incomplete_coverage(self):
        demo = json.loads((ROOT / "simulation/worlds/planar_inspection.json").read_text())
        demo["route"] = []
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "scene.json"
            path.write_text(json.dumps(demo))
            result = run_simulation(path)
        self.assertTrue(result["route_complete"])
        self.assertFalse(result["coverage_complete"])
        self.assertEqual(result["sampled_surface_coverage"], 0)
        self.assertEqual(result["elapsed_time_s"], 0)
