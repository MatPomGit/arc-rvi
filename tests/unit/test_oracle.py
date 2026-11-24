"""Exact oracle tests with analytically tractable planar fixtures."""

from dataclasses import replace
import math
import unittest

from rvi.adapters.simulator import CameraModel, Circle, MotionModel, PlanarScene, SurfacePatch
from rvi.interfaces import CameraPose
from rvi.oracle import diagnose_trials, exact_oracle
from rvi.adapters.simulator import PlanarSimulator
from rvi.benchmark import evaluate_simulation_policy


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
        self.assertEqual(result["first_full_min_times_s"][0], None)
        self.assertAlmostEqual(result["first_full_min_times_s"][1], 2.2)
        tight = replace(scene, motion=replace(scene.motion, max_time_s=2))
        result = exact_oracle(tight)
        self.assertFalse(result["full_feasible"])
        self.assertEqual(result["optimal_route"], [1])
        self.assertAlmostEqual(result["optimal_coverage"], 1 / 3)

    def test_zero_gain_transit_required(self):
        scene = PlanarScene(
            "transit", CameraPose(-2, 0, 0),
            CameraModel(math.pi / 3, .1, 5, math.pi / 2),
            MotionModel(1, 1, .1, .2, 12),
            (Circle(0, 0, .5),),
            (SurfacePatch("a", 3, 0, math.pi, 1),),
            (CameraPose(0, 2, math.pi / 2), CameraPose(2, 0, 0)),
        )
        sim = PlanarSimulator(scene)
        self.assertEqual(sim.visible_patches(scene.route[0]), ())
        self.assertEqual(sim.acquire(scene.route[1]).failure_reason,
                         "path_collision")
        result = exact_oracle(scene)
        self.assertTrue(result["full_feasible"])
        self.assertEqual(result["full_route"], [1, 2])

    def test_reject_inconsistent_trial(self):
        scene = self.fixture()
        trial = evaluate_simulation_policy(scene, "greedy_coverage")
        self.assertEqual(diagnose_trials(scene, [trial])["methods"][0]
                         ["classification"], "success")
        for changes in (
            {"covered_patch_ids": ["a"], "missing_patch_ids": ["b"]},
            {"covered_patch_ids": ["a", "b", "unknown"]},
            {"missing_patch_ids": ["a"]},
            {"sampled_surface_coverage": .5},
            {"sampled_surface_coverage": math.nan},
            {"status": "algorithm_failure", "failure_reason": "timeout"},
            {"failure_reason": "timeout"},
        ):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, "inconsistent"):
                    diagnose_trials(scene, [dict(trial, **changes)])

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
