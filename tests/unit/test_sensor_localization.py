"""Study02 sensor-based proxy association: paired inputs, no oracle leakage."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rvi.cli import main
from rvi.localization import run_sensor_localization, select_instance

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "simulation/suites/localization_sensor_demo.json"
SENSOR = ROOT / "simulation/conditions/sensor_exploratory.json"
SCENE = ROOT / "simulation/worlds/localization_2d.json"


def study_files(directory: Path) -> Path:
    for folder in ("suites", "conditions", "worlds"):
        (directory / folder).mkdir()
    (directory / "worlds/localization_2d.json").write_bytes(SCENE.read_bytes())
    config = json.loads(SENSOR.read_text(encoding="utf-8"))
    for key in ("pixel_noise_sd", "range_noise_sd_m", "brightness_noise_sd",
                "frame_dropout", "detection_dropout"):
        config[key] = 0
    (directory / "conditions/sensor_exploratory.json").write_text(
        json.dumps(config), encoding="utf-8")
    location = directory / "suites/study.json"
    location.write_bytes(SUITE.read_bytes())
    return location


class SensorLocalizationTests(unittest.TestCase):
    def test_paired_bearing_range_and_absent_target_denominators(self):
        with tempfile.TemporaryDirectory() as folder:
            spec = study_files(Path(folder))
            output = run_sensor_localization(spec)
            self.assertEqual(output, run_sensor_localization(spec))
            self.assertEqual(output["evidence_type"], "simulation")
            self.assertEqual(output["status"], "exploratory_not_confirmatory")
            self.assertEqual(output["visibility_access"], "evaluator_only_geometry")
            self.assertEqual(len(output["trials"]), 9)
            self.assertEqual(len(output["observations"]), 3)
            for obs in output["observations"]:
                self.assertNotIn("patch_id", json.dumps(obs["policy"]))
                self.assertNotIn("ground_truth", json.dumps(obs["policy"]))
                self.assertEqual(len(obs["policy"]["detections"]), 3)
            by_key = {(r["request_id"], r["method"]): r for r in output["trials"]}
            self.assertEqual(by_key[("centre_request", "bearing_proxy")]["status"],
                             "correct_selection")
            self.assertEqual(by_key[("left_request", "bearing_proxy")]["status"],
                             "correct_selection")
            self.assertEqual(by_key[("left_request", "range_proxy")]["status"],
                             "abstained")
            for method, summary in output["summary"].items():
                self.assertEqual(summary["eligible_requests"], 3)
                self.assertEqual(sum(summary[k] for k in (
                    "correct_selection", "correct_rejection", "wrong_selection",
                    "abstained")), 3)
                self.assertEqual(summary["wrong_selection"], 1)
                self.assertAlmostEqual(summary["wrong_selection_rate"], 1 / 3)
                self.assertEqual(summary["missing_frames"], 0)
            self.assertTrue(all(by_key[("absent_distractor", method)]["wrong_selection"]
                                for method in output["summary"]))

    def test_truth_changes_only_evaluation_not_policy_predictions(self):
        with tempfile.TemporaryDirectory() as folder:
            spec = study_files(Path(folder))
            observed = []
            original_selector = select_instance

            def inspect(candidates, method, threshold, ambiguity_margin):
                self.assertEqual(len(candidates), 3)
                for candidate in candidates:
                    self.assertEqual(set(candidate),
                                     {"id", "visual_distance", "spatial_distance"})
                    self.assertNotIn("left", json.dumps(candidate))
                    self.assertNotIn("centre", json.dumps(candidate))
                observed.append(method)
                return original_selector(candidates, method, threshold,
                                         ambiguity_margin)

            with patch("rvi.localization.select_instance", side_effect=inspect):
                normal = run_sensor_localization(spec)
            self.assertEqual(len(observed), 9)
            changed = json.loads(spec.read_text(encoding="utf-8"))
            changed["requests"][0]["ground_truth_patch_id"] = "left"
            spec.write_text(json.dumps(changed), encoding="utf-8")
            swapped = run_sensor_localization(spec)
            self.assertNotEqual(normal["input_sha256"], swapped["input_sha256"])
            self.assertEqual([r["selected_id"] for r in normal["trials"]],
                             [r["selected_id"] for r in swapped["trials"]])
            self.assertEqual([x["policy"] for x in normal["observations"]],
                             [x["policy"] for x in swapped["observations"]])
            self.assertNotEqual(normal["trials"][0]["status"],
                                swapped["trials"][0]["status"])

    def test_full_frame_dropout_retains_missing_and_abstentions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            spec = study_files(root)
            config_path = root / "conditions/sensor_exploratory.json"
            data = json.loads(config_path.read_text(encoding="utf-8"))
            data["frame_dropout"] = 1
            config_path.write_text(json.dumps(data), encoding="utf-8")
            report = run_sensor_localization(spec)
            for summary in report["summary"].values():
                self.assertEqual(summary["wrong_selection"], 0)
                self.assertEqual(summary["correct_rejection"], 1)
                self.assertEqual(summary["abstained"], 2)
                self.assertEqual(summary["missing_frames"], 3)
            self.assertTrue(all(r["measurement_status"] == "measurement_missing"
                                for r in report["trials"]))

    def test_invalid_study_fields_and_file_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            spec = study_files(root)
            template = json.loads(spec.read_text(encoding="utf-8"))
            variants = [
                {"stage": "confirmatory_frozen"},
                {"evidence_type": "physical"},
                {"threshold": True},
                {"ambiguity_margin": float("nan")},
                {"scene": "../../../../etc/passwd"},
                {"sensor": "../missing.json"},
                {"requests": []},
                {"requests": template["requests"] * 100},
                {"requests": [template["requests"][0]] * 2},
                {"requests": [template["requests"][0] |
                              {"ground_truth_patch_id": "unknown"}]},
                {"requests": [template["requests"][0] | {"capture_index": True}]},
                {"requests": [template["requests"][0] | {"expected_u_px": -1}]},
                {"requests": [template["requests"][0] |
                              {"expected_range_m": float("inf")}]},
            ]
            for i, change in enumerate(variants):
                with self.subTest(index=i):
                    spec.write_text(json.dumps(template | change), encoding="utf-8")
                    with self.assertRaises((ValueError, OSError)):
                        run_sensor_localization(spec)

    def test_cli_exclusive_output_and_fixture_backward_compatibility(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report_path = root / "localization.json"
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["localize", "--sensor-study", str(SUITE),
                                       "--output", str(report_path)]), 0)
            original = report_path.read_bytes()
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as err:
                main(["localize", "--sensor-study", str(SUITE),
                      "--output", str(report_path)])
            self.assertEqual(err.exception.code, 2)
            self.assertEqual(report_path.read_bytes(), original)
            with redirect_stdout(StringIO()):
                self.assertEqual(main([
                    "localize", "--fixture",
                    str(ROOT / "simulation/suites/localization_fixture.json"),
                    "--output", str(root / "fixture.json"),
                ]), 0)
            fixture = json.loads((root / "fixture.json").read_text())
            self.assertEqual(fixture["evidence_type"], "fixture")


if __name__ == "__main__":
    unittest.main()
