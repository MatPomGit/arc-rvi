"""Structural population contracts, without evaluating any policy."""

from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rvi.adapters.simulator import load_scene
from rvi.decision_population import (
    BUDGET_RATIOS, base_scenes, characterize_base, structural_features,
)


class DecisionPopulationTests(unittest.TestCase):
    def test_balanced_nested_reproducible_families(self):
        rows = list(base_scenes())
        self.assertEqual(rows, list(base_scenes()))
        self.assertEqual(len(rows), 64)
        self.assertEqual(len({r[4].identifier for r in rows}), 64)
        self.assertEqual(set(Counter(r[0] for r in rows).values()), {8})
        mapping = {(f, n, v, o): s for f, n, v, o, s in rows}
        for f, n, v, o, s in rows:
            self.assertEqual(len(s.route), n)
            self.assertEqual(len(s.patches), 6)
            if n == 6:
                large = mapping[f, 8, v, o]
                self.assertEqual(s.patches, large.patches)
                self.assertEqual(s.start, large.start)
                self.assertEqual(s.route, tuple(p for p in large.route
                                               if p in s.route))

    def test_structural_factors_and_oracle_witnesses(self):
        rows = list(base_scenes())
        scene = next(s for _, n, f, o, s in rows if n == 6 and f == 55 and o)
        clear = next(s for _, n, f, o, s in rows if n == 6 and f == 55 and not o)
        self.assertGreater(structural_features(scene)["blocked_direct_edge_fraction"], 0)
        self.assertEqual(structural_features(clear)["blocked_direct_edge_fraction"], 0)
        # Generation and characterization never call an evaluated policy.
        with patch("rvi.benchmark.evaluate_simulation_policy",
                   side_effect=AssertionError("policy called")):
            result = characterize_base(scene)
        self.assertTrue(result["reference_oracle"]["full_feasible"])
        cases = result["cases"]
        self.assertEqual([c["budget_ratio"] for c in cases], list(BUDGET_RATIOS))
        self.assertEqual([c["oracle"]["full_feasible"] for c in cases],
                         [False, True, True])
        self.assertIsNone(cases[0]["first_action_dead_end_fraction"])
        for case in cases:
            self.assertTrue(set(case["completion_feasible_first_views"]) <=
                            set(case["immediately_feasible_first_views"]))
            with tempfile.TemporaryDirectory() as root:
                path = Path(root) / "scene.json"
                path.write_text(json.dumps(case["scene"]))
                loaded, _ = load_scene(path)
                self.assertEqual(loaded.identifier, case["scene"]["scene_id"])

    def test_retain_structurally_impossible_base(self):
        scene = next(s for _, n, f, o, s in base_scenes()
                     if n == 6 and f == 18 and not o
                     and structural_features(s)["minimum_cover_views_without_motion"] is None)
        result = characterize_base(scene)
        self.assertFalse(result["reference_oracle"]["full_feasible"])
        self.assertEqual(len(result["cases"]), 3)
        for case in result["cases"]:
            self.assertFalse(case["oracle"]["full_feasible"])
            self.assertEqual(case["budget_reference_type"],
                             "fallback_max_edge_times_candidate_count")
            self.assertIsNone(case["first_action_dead_end_fraction"])


if __name__ == "__main__":
    unittest.main()
