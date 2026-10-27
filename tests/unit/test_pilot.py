"""Hand-calculable exploratory analysis checks; no scientific results."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
import json

from rvi.pilot import _intervals, analyze_pilot, summarize_pilot

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "simulation/conditions/study01_pilot.json"


class PilotAnalysisTests(unittest.TestCase):
    @staticmethod
    def synthetic():
        records, trials, scenes = [], [], []
        for family in ("family_a", "family_b"):
            for replicate in range(2):
                pair_id = f"{family}_{replicate}"
                for condition in ("nominal", "occluded"):
                    scene_id = f"{pair_id}_{condition}"
                    sha = ("a" if condition == "nominal" else "b") * 64
                    records.append({"partition": "pilot", "family": family,
                                    "pair_id": pair_id, "condition": condition,
                                    "scene_id": scene_id, "sha256": sha})
                    scenes.append({"scene_id": scene_id, "sha256": sha})
                    for method in ("fixed_order", "greedy_coverage", "greedy_distance"):
                        complete = method != "fixed_order" or condition == "nominal"
                        trials.append({"scene_id": scene_id, "method": method,
                                       "scene_sha256": sha, "evidence_type": "simulation",
                                       "status": "completed" if complete else "algorithm_failure",
                                       "failure_reason": None if complete else "unreachable_regions",
                                       "sampled_surface_coverage": 1.0 if complete else 0.0,
                                       "elapsed_time_s": 2.0, "travel_distance_m": 1.0})
        manifest = {"scenes": records}
        report = {"suite_id": "study01_pilot", "evidence_type": "simulation",
                  "visibility_access": "known_geometry_oracle", "model": "planar_geometry_kinematics_v1",
                  "methods": ["fixed_order", "greedy_coverage", "greedy_distance"],
                  "scenes": scenes, "trials": trials}
        return manifest, report

    def test_paired_family_means_and_failure_denominators(self):
        manifest, report = self.synthetic()
        summary = summarize_pilot(manifest, report, "fixed_order", "greedy_distance")
        self.assertEqual(summary["families"], 2)
        self.assertEqual(summary["pairs"], 4)
        self.assertEqual(summary["estimated_effects"]["completion_loss_difference"], -1.0)
        self.assertEqual(summary["estimated_effects"]["coverage_loss_difference"], -1.0)
        self.assertIsNone(summary["uncertainty"]["confidence_intervals"])
        failure = next(row for row in summary["method_condition"]
                       if row["method"] == "fixed_order" and row["condition"] == "occluded")
        self.assertEqual(failure["trials"], 4)
        self.assertEqual(failure["completed"], 0)
        self.assertEqual(failure["failures"], {"unreachable_regions": 4})

    def test_missing_duplicate_and_incoherent_trials_are_rejected(self):
        manifest, report = self.synthetic()
        report["trials"].pop()
        with self.assertRaisesRegex(ValueError, "missing or extra"):
            summarize_pilot(manifest, report, "fixed_order", "greedy_distance")
        manifest, report = self.synthetic()
        report["trials"][0] = dict(report["trials"][1])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            summarize_pilot(manifest, report, "fixed_order", "greedy_distance")
        manifest, report = self.synthetic()
        report["trials"][0]["sampled_surface_coverage"] = float("nan")
        with self.assertRaisesRegex(ValueError, "invalid coverage"):
            summarize_pilot(manifest, report, "fixed_order", "greedy_distance")
        manifest, report = self.synthetic()
        report["trials"][0]["status"] = "algorithm_failure"
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            summarize_pilot(manifest, report, "fixed_order", "greedy_distance")
        manifest, report = self.synthetic()
        report["scenes"][0]["sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "hashes disagree"):
            summarize_pilot(manifest, report, "fixed_order", "greedy_distance")

    def test_bootstrap_is_family_level_and_reproducible(self):
        effects = [{"completion_loss_difference": float(i % 2),
                    "coverage_loss_difference": float(i % 2)} for i in range(8)]
        first = _intervals(effects, 42, 500)
        self.assertEqual(first, _intervals(effects, 42, 500))
        self.assertEqual(first["status"], "exploratory_cluster_bootstrap")
        self.assertEqual(len(first["confidence_intervals"]["coverage_loss_difference"]), 2)
        self.assertEqual(_intervals(effects[:7], 42, 500)["status"], "descriptive_only")

    def test_invalid_contrast_and_seed_rejected(self):
        manifest, report = self.synthetic()
        for ref, comp in (("fixed_order", "fixed_order"), ("unknown", "greedy_distance")):
            with self.assertRaisesRegex(ValueError, "different"):
                summarize_pilot(manifest, report, ref, comp)
        with self.assertRaisesRegex(ValueError, "seed"):
            summarize_pilot(manifest, report, "fixed_order", "greedy_distance", seed=True)

    def test_generated_manifest_full_pilot_replay_and_hash_integrity(self):
        from rvi.conditions import generate_conditions
        with tempfile.TemporaryDirectory() as temp:
            generated = Path(temp) / "generated"
            generate_conditions(SPEC, generated)
            summary = analyze_pilot(generated / "manifest.json")
            self.assertEqual(summary["families"], 2)
            self.assertEqual(summary["pairs"], 6)
            self.assertEqual(summary["uncertainty"]["status"], "descriptive_only")
            self.assertEqual(sum(row["trials"] for row in summary["method_condition"]), 36)
            scene_path = generated / "scenes/pilot/stacked_triple_r000_nominal.json"
            scene_path.write_bytes(scene_path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                analyze_pilot(generated / "manifest.json")

    def test_holdout_not_accessed_and_duplicate_manifest_rejected(self):
        from rvi.conditions import generate_conditions
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "generated"
            generate_conditions(SPEC, root)
            manifest = root / "manifest.json"
            baseline = analyze_pilot(manifest)
            # Holdout files must not be read by exploratory pilot analysis.
            holdout = next((root / "scenes/holdout").glob("*.json"))
            holdout.write_bytes(b"unread holdout scenario")
            self.assertEqual(analyze_pilot(manifest)["estimated_effects"], baseline["estimated_effects"])
            raw = manifest.read_text(encoding="utf-8")
            self.assertIn('"study_id": "01"', raw)
            manifest.write_text(raw.replace('"study_id": "01"', '"study_id": "01", "study_id": "01"', 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                analyze_pilot(manifest)


    def test_cli_pilot_report_is_saved_once(self):
        from rvi.conditions import generate_conditions
        from rvi.cli import main
        with tempfile.TemporaryDirectory() as temp:
            generated = Path(temp) / "generated"
            output = Path(temp) / "pilot.json"
            generate_conditions(SPEC, generated)
            args = ["pilot", "--manifest", str(generated / "manifest.json"),
                    "--output", str(output)]
            with redirect_stdout(StringIO()):
                self.assertEqual(main(args), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["families"], 2)
            previous = output.read_bytes()
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as raised:
                main(args)
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(output.read_bytes(), previous)


if __name__ == "__main__":
    unittest.main()
