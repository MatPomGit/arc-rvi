"""Numerical checks for illustrative, non-confirmatory family Monte Carlo."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import math
from pathlib import Path
import tempfile
import unittest

from rvi.cli import main
from rvi.power_mc import _t_critical, analyze_cluster_monte_carlo

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "simulation/conditions/study01_cluster_mc.json"


class ClusterMonteCarloTests(unittest.TestCase):
    def test_deterministic_null_alternative_and_family_denominators(self):
        result = analyze_cluster_monte_carlo(SPEC)
        self.assertEqual(result, analyze_cluster_monte_carlo(SPEC))
        self.assertEqual(result["independent_unit"], "geometry_family")
        self.assertEqual(result["evidence_type"], "simulation")
        self.assertEqual(len(result["scenarios"]), 4)
        self.assertEqual(len(result["results"]), 8)
        self.assertEqual({r["effect_condition"] for r in result["results"]},
                         {"null", "alternative"})
        self.assertEqual({r["requested_repetitions"] for r in result["results"]}, {400})
        for r in result["results"]:
            self.assertEqual(r["non_estimable_repetitions"] +
                             r["estimable_repetitions"], 400)
            self.assertGreaterEqual(r["mean_observed_families"], 0)
            self.assertLessEqual(r["mean_observed_families"],
                                 next(s["families"] for s in result["scenarios"]
                                      if s["id"] == r["scenario_id"]))
            for method in r["interval_methods"].values():
                if r["estimable_repetitions"]:
                    for key in ("rejection_probability", "confidence_interval_coverage",
                                "coverage_mcse", "rejection_probability_mcse"):
                        self.assertTrue(math.isfinite(method[key]))
                        self.assertGreaterEqual(method[key], 0)
                        self.assertLessEqual(method[key], 1)

    def test_small_sample_t_critical_and_wider_intervals(self):
        self.assertGreater(_t_critical(2, .95), 1.959)
        self.assertGreater(_t_critical(7, .95), 1.959)
        self.assertLess(_t_critical(39, .95), _t_critical(7, .95))
        result = analyze_cluster_monte_carlo(SPEC)
        for row in result["results"]:
            if row["estimable_repetitions"]:
                normal = row["interval_methods"]["normal_z"]
                small_t = row["interval_methods"]["t_approx"]
                self.assertGreaterEqual(small_t["mean_interval_width"],
                                        normal["mean_interval_width"])

    def test_invalid_input_and_bounded_runtime(self):
        source = json.loads(SPEC.read_text(encoding="utf-8"))
        mutations = [
            {"status": "frozen"},
            {"repetitions": True},
            {"repetitions": 99},
            {"replicates_per_family": 17},
            {"confidence_level": float("nan")},
            {"alternative_effect": 0},
            {"scenarios": []},
            {"scenarios": [source["scenarios"][0], source["scenarios"][0]]},
            {"scenarios": [source["scenarios"][0] | {"between_family_sd": 0}]},
            {"scenarios": [source["scenarios"][0] | {"family_distribution": "unknown"}]},
            {"scenarios": [source["scenarios"][0] | {"families": True}]},
            {"scenarios": [source["scenarios"][0] | {"missing_family_fraction": 1.0}]},
            {"scenarios": [source["scenarios"][0] | {"missingness_mechanism": "unknown"}]},
            {"scenarios": [source["scenarios"][0] | {"id": "../bad"}]},
            {"scenarios": [source["scenarios"][0] | {"families": 256}],
             "repetitions": 5000, "replicates_per_family": 16},
        ]
        with tempfile.TemporaryDirectory() as temp:
            for i, change in enumerate(mutations):
                with self.subTest(i=i):
                    path = Path(temp) / f"bad_{i}.json"
                    path.write_text(json.dumps(source | change), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        analyze_cluster_monte_carlo(path)
            duplicate = Path(temp) / "duplicate.json"
            duplicate.write_text('{"repetitions":100,"repetitions":200}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                analyze_cluster_monte_carlo(duplicate)

    def test_family_dropout_is_not_interpreted_as_trial_success(self):
        report = analyze_cluster_monte_carlo(SPEC)
        normal = next(r for r in report["results"] if r["scenario_id"] == "normal_low"
                      and r["effect_condition"] == "null")
        self.assertEqual(normal["non_estimable_repetitions"], 0)
        self.assertEqual(normal["mean_observed_families"], 8)
        dropped = next(r for r in report["results"] if r["scenario_id"] == "dependent_missing"
                       and r["effect_condition"] == "null")
        self.assertLess(dropped["mean_observed_families"], 40)
        self.assertEqual(dropped["interval_methods"]["normal_z"]["evaluated"],
                         dropped["estimable_repetitions"])

    def test_cli_writes_once(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report.json"
            args = ["power-mc", "--spec", str(SPEC), "--output", str(output)]
            with redirect_stdout(StringIO()):
                self.assertEqual(main(args), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(report["results"]), 8)
            previous = output.read_bytes()
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as e:
                main(args)
            self.assertEqual(e.exception.code, 2)
            self.assertEqual(output.read_bytes(), previous)


if __name__ == "__main__":
    unittest.main()
