"""Exact oracle tests with analytically tractable planar fixtures."""

from dataclasses import replace
import math
import unittest

from rvi.adapters.simulator import CameraModel, Circle, MotionModel, PlanarScene, SurfacePatch
from rvi.interfaces import CameraPose
from rvi.oracle import exact_oracle


class ExactOracleTests(unittest.TestCase):
    def fixture(self):
        return PlanarScene(
            "oracle_fixture", CameraPose(0, 0, 0),
            CameraModel(math.pi / 2, 0.1, 5, math.pi / 2),
            MotionModel(1, 1, 0.1, 0.2, 2.3), (),
            (SurfacePatch("a", 3, 0, math.pi, 1),
             SurfacePatch("b", 3, 4, math.pi, 2)),
            (CameraPose(0, 0, 0), CameraPose(0, 2, 0)),
        )

    def test_full_optimum_and_tight_budget(self):
        scene = self.fixture()
        result = exact_oracle(scene)
        self.assertTrue(result["full_feasible"])
        self.assertEqual(result["full_route"], [2])
        self.assertAlmostEqual(result["full_min_time_s"], 2.2)
        tight = replace(scene, motion=replace(scene.motion, max_time_s=2))
        result = exact_oracle(tight)
        self.assertFalse(result["full_feasible"])
        self.assertEqual(result["optimal_route"], [1])
        self.assertAlmostEqual(result["optimal_coverage"], 1 / 3)

    def test_empty_route_and_size_limit(self):
        scene = self.fixture()
        result = exact_oracle(replace(scene, route=()))
        self.assertFalse(result["full_feasible"])
        self.assertEqual(result["optimal_coverage"], 0)
        with self.assertRaisesRegex(ValueError, "candidate limit"):
            exact_oracle(replace(scene, route=scene.route * 5))

    def test_collision_excludes_otherwise_full_view(self):
        scene = replace(self.fixture(), obstacles=(Circle(0, 1, 0.2),))
        result = exact_oracle(scene)
        self.assertFalse(result["full_feasible"])
        self.assertEqual(result["optimal_route"], [1])


if __name__ == "__main__":
    unittest.main()
