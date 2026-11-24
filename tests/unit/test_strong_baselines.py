"""Analytical and negative-path checks for the strong baseline policies."""

from dataclasses import replace
import math
import unittest
from unittest.mock import patch

from rvi.adapters.simulator import CameraModel, Circle, MotionModel, PlanarScene, SurfacePatch
from rvi.interfaces import CameraPose
from rvi.oracle import diagnose_trials
from rvi.strong_baselines import STRONG_METHODS, evaluate_strong_policy


class StrongBaselineTests(unittest.TestCase):
    def scene(self):
        return PlanarScene(
            "strong_fixture", CameraPose(0, 0, 0),
            CameraModel(math.pi / 2, .1, 5, math.pi / 2),
            MotionModel(1, 1, .1, .2, 2.3), (),
            (SurfacePatch("a", 3, 0, math.pi, 1),
             SurfacePatch("b", 3, 4, math.pi, 2)),
            (CameraPose(0, 0, 0), CameraPose(0, 2, 0)),
        )

    def test_horizon_and_feasibility_semantics(self):
        scene = self.scene()
        with patch("rvi.oracle.exact_oracle",
                   side_effect=AssertionError("policy accessed oracle")):
            trials = [evaluate_strong_policy(scene, m) for m in STRONG_METHODS]
        by_method = {r["method"]: r for r in trials}
        for m in ("feasible_greedy", "receding_horizon_2",
                  "receding_horizon_3"):
            self.assertEqual(by_method[m]["status"], "completed")
            self.assertEqual(by_method[m]["observations"][0]["candidate_id"],
                             "view_000002")
        self.assertEqual(by_method["gain_per_cost"]["status"], "algorithm_failure")
        self.assertAlmostEqual(by_method["gain_per_cost"]["sampled_surface_coverage"],
                               1 / 3)
        self.assertEqual(diagnose_trials(scene, trials)["full_min_time_s"], 2.2)

    def test_collision_and_empty_remaining(self):
        scene = replace(self.scene(), obstacles=(Circle(0, 1, .2),))
        for m in STRONG_METHODS:
            trial = evaluate_strong_policy(scene, m)
            self.assertEqual(trial["status"], "algorithm_failure")
            self.assertTrue(all(e["failure_reason"] is None
                                for e in trial["observations"]))
            self.assertAlmostEqual(trial["sampled_surface_coverage"], 1 / 3)
            self.assertEqual(trial["decisions"][-1]["selected"], None)
            empty = evaluate_strong_policy(replace(scene, route=()), m)
            self.assertEqual(empty["sampled_surface_coverage"], 0)
            self.assertEqual(empty["expanded_transitions"], 0)

    def test_determinism_and_zero_duration(self):
        scene = self.scene()
        scene = replace(scene, motion=replace(scene.motion, capture_duration_s=0))
        for m in STRONG_METHODS:
            first = evaluate_strong_policy(scene, m)
            self.assertEqual(first, evaluate_strong_policy(scene, m))
            self.assertEqual(first["expanded_transitions"],
                             sum(d["expanded_transitions"] for d in first["decisions"]))
        result = evaluate_strong_policy(scene, "gain_per_cost")
        self.assertEqual(result["observations"][0]["candidate_id"], "view_000001")
        with self.assertRaisesRegex(ValueError, "unknown"):
            evaluate_strong_policy(scene, "invalid")


if __name__ == "__main__":
    unittest.main()
