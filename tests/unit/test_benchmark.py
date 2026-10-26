"""Independent arithmetic and failure accounting for paired fixture evaluation."""

import hashlib
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from rvi.benchmark import run_benchmark, software_provenance
from rvi.models import Viewpoint
from rvi.scenarios import load_scenario
from rvi.viewpoints import evaluate_viewpoints

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "simulation/suites/fixture_smoke.json"


class BenchmarkTests(unittest.TestCase):
    def test_paired_denominators_and_failures(self):
        result = run_benchmark(SUITE)
        self.assertEqual(result["evidence_type"], "fixture")
        self.assertEqual(len(result["trials"]), 9)
        self.assertEqual(len({row["trial_id"] for row in result["trials"]}), 9)
        for method in result["methods"]:
            rows = [row for row in result["trials"] if row["method"] == method]
            self.assertEqual([row["scenario_id"] for row in rows],
                             ["synthetic_asset_001", "coverage_distance_tradeoff", "unreachable_roof"])
            missing = rows[2]
            self.assertEqual(missing["status"], "algorithm_failure")
            self.assertEqual(missing["failure_reason"], "unreachable_regions")
            self.assertEqual(missing["coverage_fraction"], 0.5)
            self.assertEqual(missing["missing_regions"], ["roof"])
            self.assertEqual(missing["travel_distance_m"], 1.0)
        summaries = {row["method"]: row for row in result["summary"]}
        self.assertEqual(summaries["fixed_order"]["trial_count"], 3)
        self.assertEqual(summaries["fixed_order"]["success_count"], 1)
        self.assertEqual(summaries["fixed_order"]["mean_coverage_fraction"], 0.5)
        self.assertEqual(summaries["greedy_distance"]["success_count"], 2)
        self.assertAlmostEqual(summaries["greedy_distance"]["mean_coverage_fraction"], 5 / 6)
        self.assertEqual(summaries["greedy_coverage"]["failures"],
                         {"distance_budget_exceeded": 1, "unreachable_regions": 1})
        paired = [row for row in result["trials"]
                  if row["scenario_id"] == "coverage_distance_tradeoff"]
        self.assertEqual(len({row["scenario_sha256"] for row in paired}), 1)
        self.assertEqual(paired[2]["viewpoint_ids"], ["near_front", "near_rear"])
        self.assertEqual(paired[2]["travel_distance_m"], 2.0)
        self.assertEqual(paired[0]["viewpoint_ids"], [])
        self.assertEqual(paired[0]["coverage_fraction"], 0)

    def test_exact_replay_and_input_hash(self):
        with patch("rvi.benchmark.software_provenance", return_value={"commit_sha": "test"}):
            first = run_benchmark(SUITE)
            self.assertEqual(first, run_benchmark(SUITE))
        self.assertEqual(first["inputs"]["suite_sha256"],
                         hashlib.sha256(SUITE.read_bytes()).hexdigest())
        for entry in first["inputs"]["scenarios"]:
            raw = (SUITE.parent / entry["path"]).read_bytes()
            self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())

    def test_byte_change_affects_run_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scenario = root / "scenario.json"
            scenario.write_text(json.dumps(self.scenario()))
            suite = root / "suite.json"
            suite.write_text(json.dumps(self.suite()))
            before = run_benchmark(suite)
            scenario.write_bytes(scenario.read_bytes() + b"\n")
            after = run_benchmark(suite)
            self.assertNotEqual(before["run_id"], after["run_id"])
            self.assertEqual(before["summary"], after["summary"])

    def test_package_provenance_includes_new_modules(self):
        source = software_provenance()
        self.assertEqual(source["package_version"], tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"])
        self.assertIn("benchmark.py", source["package_files"])
        self.assertEqual(len(source["package_source_sha256"]), 64)

    @staticmethod
    def scenario():
        return {"scenario_id": "example", "evidence_type": "fixture",
                "required_regions": ["front", "rear"],
                "viewpoints": [{"id": "front", "x": 1, "y": 0, "regions": ["front"]}]}

    @staticmethod
    def suite():
        return {"schema_version": "1.0.0", "suite_id": "example", "evidence_type": "fixture",
                "max_travel_distance_m": 10, "scenarios": ["scenario.json"]}

    def test_invalid_suites_are_rejected(self):
        changes = [{"scenarios": []}, {"scenarios": "scenario.json"},
                   {"scenarios": ["scenario.json", "./scenario.json"]},
                   {"max_travel_distance_m": True}, {"max_travel_distance_m": -1},
                   {"evidence_type": "physical"}, {"schema_version": "2.0.0"},
                   {"unexpected": 1}]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scenario.json").write_text(json.dumps(self.scenario()))
            for change in changes:
                with self.subTest(change=change):
                    suite = self.suite() | change
                    path = root / "suite.json"
                    path.write_text(json.dumps(suite))
                    with self.assertRaises(ValueError):
                        run_benchmark(path)

    def test_invalid_scenarios_are_rejected(self):
        changes = [{"evidence_type": "simulation"}, {"scenario_id": ""},
                   {"required_regions": "front"}, {"required_regions": ["a", "a"]},
                   {"viewpoints": [{"id": "a", "x": True, "y": 0, "regions": ["front"]}]},
                   {"viewpoints": [{"id": "a", "x": 1, "y": 0, "regions": "front"}]},
                   {"viewpoints": [{"id": "a", "x": 1, "y": 0, "regions": ["undeclared"]}]},
                   {"start_xy": [0]}, {"start_xy": [float("nan"), 0]},
                   {"unexpected": 1}]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "scenario.json"
            for change in changes:
                with self.subTest(change=change):
                    path.write_text(json.dumps(self.scenario() | change))
                    with self.assertRaises(ValueError):
                        load_scenario(path)
            path.write_text('{"scenario_id":"one","scenario_id":"two"}')
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                load_scenario(path)

    def test_duplicate_scenario_ids_fail_even_with_different_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for file in ("one.json", "two.json"):
                (root / file).write_text(json.dumps(self.scenario()))
            path = root / "suite.json"
            path.write_text(json.dumps(self.suite() | {"scenarios": ["one.json", "two.json"]}))
            with self.assertRaisesRegex(ValueError, "duplicate scenario"):
                run_benchmark(path)


class PartialPlanningTests(unittest.TestCase):
    def test_partial_budget_and_inclusive_boundary(self):
        views = [Viewpoint("near", 1, 0, ("front",)), Viewpoint("far", 3, 0, ("rear",))]
        result = evaluate_viewpoints(views, ["front", "rear"], max_travel_distance_m=1)
        self.assertEqual(result.plan.viewpoint_ids, ("near",))
        self.assertEqual(result.plan.covered_regions, ("front",))
        self.assertEqual(result.plan.travel_distance_m, 1)
        self.assertEqual(result.failure_reason, "distance_budget_exceeded")
        complete = evaluate_viewpoints(views, ["front", "rear"], max_travel_distance_m=3)
        self.assertIsNone(complete.failure_reason)
        self.assertEqual(complete.plan.travel_distance_m, 3)

    def test_fixed_order_includes_redundant_views_greedy_skips_them(self):
        views = [Viewpoint("first", 1, 0, ("front",)),
                 Viewpoint("redundant", 2, 0, ("front",)),
                 Viewpoint("rear", 3, 0, ("rear",))]
        fixed = evaluate_viewpoints(views, ["front", "rear"], method="fixed_order")
        greedy = evaluate_viewpoints(views, ["front", "rear"], method="greedy_coverage")
        self.assertEqual(fixed.plan.viewpoint_ids, ("first", "redundant", "rear"))
        self.assertEqual(greedy.plan.viewpoint_ids, ("first", "rear"))

    def test_greedy_ties_ignore_input_order(self):
        views = [Viewpoint("z", 1, 0, ("front",)), Viewpoint("a", -1, 0, ("front",))]
        for method in ("greedy_coverage", "greedy_distance"):
            first = evaluate_viewpoints(views, ["front"], method=method)
            self.assertEqual(first.plan.viewpoint_ids, ("a",))
            self.assertEqual(first, evaluate_viewpoints(reversed(views), ["front"], method=method))

    def test_empty_candidates_retain_zero_coverage(self):
        outcome = evaluate_viewpoints([], ["front"])
        self.assertEqual(outcome.plan.covered_regions, ())
        self.assertEqual(outcome.failure_reason, "unreachable_regions")

    def test_zero_budget_accepts_a_view_at_start(self):
        outcome = evaluate_viewpoints([Viewpoint("at_start", 0, 0, ("front",))],
                                      ["front"], max_travel_distance_m=0)
        self.assertIsNone(outcome.failure_reason)

    def test_invalid_method_and_budget(self):
        for kwargs in ({"method": "unknown"}, {"max_travel_distance_m": True},
                       {"max_travel_distance_m": float("inf")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                evaluate_viewpoints([], ["front"], **kwargs)
