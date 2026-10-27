"""Pre-confirmatory, assumption-only precision and power arithmetic tests."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import math
from pathlib import Path
import tempfile
import unittest

from rvi.cli import main
from rvi.planning import plan_family_sample, _power

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "simulation/conditions/study01_precision_sensitivity.json"


class FamilyPlanningTests(unittest.TestCase):
    def test_wald_arithmetic_and_enrollment(self):
        outcome = plan_family_sample(SPEC)
        self.assertEqual(outcome["evidence_type"], "planning_only")
        self.assertEqual(outcome["independent_unit"], "geometry_family")
        self.assertEqual(outcome["status"], "illustrative_sensitivity_not_preregistered")
        rows = {row["id"]: row for row in outcome["scenario_results"]}
        self.assertEqual(rows["low_variability"]["required_complete_families"], 8)
        self.assertEqual(rows["low_variability"]["planned_enrolled_families"], 9)
        self.assertEqual(rows["moderate_variability"]["families_for_normal_ci_precision"], 16)
        self.assertEqual(rows["moderate_variability"]["required_complete_families"], 16)
        self.assertEqual(rows["moderate_variability"]["planned_enrolled_families"], 18)
        self.assertEqual(rows["high_variability"]["families_for_normal_ci_precision"], 40)
        self.assertEqual(rows["high_variability"]["required_complete_families"], 40)
        self.assertEqual(rows["high_variability"]["planned_enrolled_families"], 50)
        for row in rows.values():
            self.assertGreaterEqual(row["estimated_two_sided_normal_power_at_complete_n"], 0.8)
            self.assertLessEqual(row["estimated_ci_half_width_at_complete_n"], 0.1)
            self.assertGreaterEqual(row["planned_enrolled_families"], row["required_complete_families"])
        self.assertEqual(outcome, plan_family_sample(SPEC))

    def test_two_sided_power_formula(self):
        self.assertAlmostEqual(_power(4, 1.0, 0.0, 1.959963984540054), 0.05, places=10)
        self.assertGreater(_power(16, .2, .15, 1.959963984540054),
                           _power(8, .2, .15, 1.959963984540054))

    def test_sensitivity_ordering_is_not_pilot_driven(self):
        report = {
            "stage": "exploratory_not_confirmatory",
            "partition": "pilot",
            "evidence_type": "simulation",
            "visibility_access": "known_geometry_oracle",
            "independent_unit": "geometry_family",
            "families": 12,
            "family_effects": [
                {"family": f"family_{i:03d}", "completion_loss_difference": (-1) ** i * (i / 100)}
                for i in range(12)
            ],
        }
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "pilot.json"
            source.write_text(json.dumps(report), encoding="utf-8")
            base = plan_family_sample(SPEC)
            first = plan_family_sample(SPEC, source)
            self.assertEqual(first["scenario_results"], base["scenario_results"])
            self.assertEqual(first["pilot_diagnostics"]["family_count"], 12)
            self.assertGreater(first["pilot_diagnostics"]["observed_model_completion_contrast_sd"], 0)
            report["family_effects"][0]["completion_loss_difference"] = 2.0
            source.write_text(json.dumps(report), encoding="utf-8")
            second = plan_family_sample(SPEC, source)
            self.assertNotEqual(first["pilot_diagnostics"]["observed_model_completion_contrast_sd"],
                                second["pilot_diagnostics"]["observed_model_completion_contrast_sd"])
            self.assertEqual(second["scenario_results"], first["scenario_results"])

    def test_invalid_planning_specs_are_rejected(self):
        source = json.loads(SPEC.read_text(encoding="utf-8"))
        variants = [
            {"planning_status": "frozen"},
            {"confidence_level": True}, {"confidence_level": 1.0},
            {"target_power": float("nan")}, {"target_power": 0.25},
            {"effect_to_detect": 0.0}, {"target_ci_half_width": -1},
            {"minimum_complete_families": True},
            {"minimum_complete_families": 1},
            {"scenarios": []},
            {"scenarios": [source["scenarios"][0], source["scenarios"][0]]},
            {"scenarios": [source["scenarios"][0] | {"family_effect_sd": 0.0}]},
            {"scenarios": [source["scenarios"][0] | {"unusable_family_fraction": 1.0}]},
            {"scenarios": [source["scenarios"][0] | {"id": "../invalid"}]},
            {"unexpected": 1},
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index, variant in enumerate(variants):
                with self.subTest(variant=index):
                    path = root / f"invalid_{index}.json"
                    path.write_text(json.dumps(source | variant), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        plan_family_sample(path)
            duplicate = root / "duplicate.json"
            duplicate.write_text('{"study_id":"01","study_id":"01"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                plan_family_sample(duplicate)

    def test_invalid_pilot_cannot_be_used_as_design_data(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "pilot.json"
            for payload in [
                {"stage": "confirmatory", "partition": "pilot"},
                {"stage": "exploratory_not_confirmatory", "partition": "holdout"},
            ]:
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(ValueError):
                    plan_family_sample(SPEC, path)

    def test_generated_pilot_diagnostics_integration(self):
        from rvi.population import generate_population
        from rvi.pilot import analyze_pilot

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "generated"
            generate_population(
                ROOT / "simulation/conditions/study01_population_pilot.json",
                generated,
            )
            pilot = analyze_pilot(generated / "manifest.json")
            summary_path = root / "pilot_summary.json"
            summary_path.write_text(
                json.dumps(pilot, sort_keys=True, allow_nan=False),
                encoding="utf-8",
            )
            report = plan_family_sample(SPEC, summary_path)
            self.assertEqual(report["pilot_diagnostics"]["family_count"], 12)
            self.assertEqual(report["scenario_results"], plan_family_sample(SPEC)["scenario_results"])
            self.assertEqual(report["pilot_diagnostics"]["status"],
                             "diagnostic_only_not_used_to_size_confirmation")

    def test_cli_report_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "planning.json"
            args = ["precision", "--spec", str(SPEC), "--output", str(output)]
            with redirect_stdout(StringIO()):
                self.assertEqual(main(args), 0)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["scenario_results"][1]["planned_enrolled_families"], 18)
            original = output.read_bytes()
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as captured:
                main(args)
            self.assertEqual(captured.exception.code, 2)
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
