"""End-to-end generated raster-image P02 study with sealed exploratory holdout."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from rvi.cli import main
from rvi.localization import run_sensor_localization
from rvi.localization_population import (
    analyze_localization_population, generate_localization_population,
)
from rvi.image_features import pixel_distance

ROOT = Path(__file__).resolve().parents[2]
SENSOR = ROOT / "simulation/conditions/sensor_exploratory.json"


class ImagePopulationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        shutil.copyfile(SENSOR, self.root / "sensor.json")
        self.spec = self.root / "spec.json"
        self.spec.write_text(json.dumps({
            "schema_version": "1.0.0", "study_id": "02",
            "design": "planar_grayscale_association_v1",
            "master_seed": 20261027,
            "family_counts": {"development": 1, "pilot": 1, "holdout": 1},
            "replicates_per_cell": 1,
            "sensor": "sensor.json",
            "appearance_levels": ["distinct", "similar"],
        }), encoding="utf-8")

    def generated(self, name="population"):
        root = self.root / name
        result = generate_localization_population(self.spec, root)
        return root, result

    def test_pairs_are_disjoint_and_images_are_not_identity_labels(self):
        root, manifest = self.generated()
        self.assertEqual(len(manifest["records"]), 24)
        self.assertEqual(len({r["study"] for r in manifest["records"]}), 24)
        family_splits = {}
        for record in manifest["records"]:
            if record["family"] in family_splits:
                self.assertEqual(family_splits[record["family"]],
                                 record["partition"])
            family_splits[record["family"]] = record["partition"]
        self.assertEqual(len(family_splits), 3)
        pilot = [r for r in manifest["records"] if r["partition"] == "pilot"]
        self.assertEqual(len(pilot), 8)
        self.assertEqual({r["similarity"] for r in pilot}, {"distinct", "similar"})
        self.assertEqual(len({r["session_id"] for r in pilot}), 1)
        present = next(r for r in pilot if r["similarity"] == "similar")
        spec = json.loads((root / present["study"]).read_text())
        report = run_sensor_localization(root / present["study"])
        self.assertEqual(report["selection_modes"],
                         ["grayscale_mae", "range_proxy", "grayscale_range"])
        self.assertEqual(len(report["trials"]), 6)
        self.assertEqual(report["session_id"], present["session_id"])
        policy = report["observations"][0]["policy"]
        self.assertNotIn("ground_truth_patch_id", json.dumps(policy))
        self.assertNotIn("patch_id", json.dumps(policy))
        self.assertTrue(all(len(d["gray8_8x8"]) == 64
                            for d in policy["detections"]))
        self.assertEqual(len(spec["requests"][0]["template_pixels"]), 64)
        # Physical image data would require an actual capture, not this model.
        self.assertEqual(policy["image_model"], "synthetic_grayscale_patch_v1")

    def test_replay_provenance_and_descriptive_denominators(self):
        root, _ = self.generated()
        original = analyze_localization_population(root / "manifest.json")
        replay = analyze_localization_population(root / "manifest.json")
        self.assertEqual(original["family_results"], replay["family_results"])
        self.assertEqual(original["mean_family_wrong_risk"],
                         replay["mean_family_wrong_risk"])
        self.assertEqual(original["family_count"], 1)
        self.assertEqual(original["study_count"], 8)
        self.assertEqual(len(original["factor_strata"]), 16)
        self.assertEqual(original["inference"], "descriptive_only_no_ci_no_p_value")
        for method in ("grayscale_mae", "range_proxy", "grayscale_range"):
            total = sum(row[method]["eligible_requests"]
                        for row in original["factor_strata"].values())
            self.assertEqual(total, 16)
        self.assertIn("paired_difference_grayscale_range_minus_grayscale", original)

    def test_reference_identity_not_used_for_selection(self):
        root, manifest = self.generated()
        record = next(r for r in manifest["records"]
                      if r["partition"] == "pilot" and r["occlusion"] == "clear")
        study_path = root / record["study"]
        before = run_sensor_localization(study_path)
        changed = json.loads(study_path.read_text())
        changed["requests"][0]["ground_truth_patch_id"] = None
        study_path.write_text(json.dumps(changed))
        after = run_sensor_localization(study_path)
        self.assertEqual([r["selected_id"] for r in before["trials"]],
                         [r["selected_id"] for r in after["trials"]])
        self.assertEqual([o["policy"] for o in before["observations"]],
                         [o["policy"] for o in after["observations"]])
        self.assertNotEqual(before["input_sha256"], after["input_sha256"])

    def test_holdout_protection_and_corrupt_pilot(self):
        root, manifest = self.generated()
        with self.assertRaisesRegex(ValueError, "holdout"):
            analyze_localization_population(root / "manifest.json", "holdout")
        holdout = next(r for r in manifest["records"] if r["partition"] == "holdout")
        (root / holdout["study"]).write_text("corrupt holdout")
        self.assertEqual(analyze_localization_population(
            root / "manifest.json")["study_count"], 8)
        pilot = next(r for r in manifest["records"] if r["partition"] == "pilot")
        (root / pilot["study"]).write_text("corrupt pilot")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            analyze_localization_population(root / "manifest.json")

    def test_invalid_appearance_levels(self):
        invalid = json.loads(self.spec.read_text())
        invalid["appearance_levels"] = ["same", "different"]
        self.spec.write_text(json.dumps(invalid))
        with self.assertRaisesRegex(ValueError, "appearance levels"):
            self.generated()

    def test_cli_end_to_end(self):
        dest = self.root / "generated"
        self.assertEqual(main(["localize-population", "--spec", str(self.spec),
                               "--output-dir", str(dest)]), 0)
        report_path = self.root / "report.json"
        self.assertEqual(main(["localize", "--population-manifest",
                               str(dest / "manifest.json"), "--output",
                               str(report_path)]), 0)
        result = json.loads(report_path.read_text())
        self.assertEqual(result["family_count"], 1)
        self.assertEqual(result["study_count"], 8)
        with self.assertRaises(SystemExit) as exc:
            main(["localize", "--population-manifest", str(dest / "manifest.json"),
                  "--partition", "holdout", "--output", str(self.root / "no.json")])
        self.assertEqual(exc.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
