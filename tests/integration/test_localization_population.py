"""End-to-end checks for synthetic P02 family populations; no physical inference."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from rvi.adapters.simulator import PlanarSimulator, load_scene
from rvi.cli import main
from rvi.localization_population import (
    analyze_localization_population, generate_localization_population,
)

ROOT = Path(__file__).resolve().parents[2]
SENSOR = ROOT / "simulation/conditions/sensor_exploratory.json"


class LocalizationPopulationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sensor = self.root / "sensor.json"
        shutil.copyfile(SENSOR, self.sensor)
        self.spec = self.root / "spec.json"
        self.spec.write_text(json.dumps({
            "schema_version": "1.0.0", "study_id": "02",
            "design": "planar_association_families_v1", "master_seed": 20261027,
            "family_counts": {"development": 1, "pilot": 1, "holdout": 1},
            "replicates_per_cell": 1, "sensor": "sensor.json",
        }), encoding="utf-8")

    def generate(self, name="output"):
        target = self.root / name
        manifest = generate_localization_population(self.spec, target)
        return target, manifest

    def test_deterministic_disjoint_factorial_design(self):
        first, manifest = self.generate("first")
        second, other = self.generate("second")
        self.assertEqual(manifest, other)
        paths = [r["study"] for r in manifest["records"]]
        self.assertEqual(len(paths), 12)
        self.assertEqual(len(paths), len(set(paths)))
        for rel in ["manifest.json", "data/sensor.json", *paths]:
            self.assertEqual((first / rel).read_bytes(), (second / rel).read_bytes())
        split_families = {
            partition: {r["family"] for r in manifest["records"]
                        if r["partition"] == partition}
            for partition in ("development", "pilot", "holdout")
        }
        self.assertTrue(all(len(x) == 1 for x in split_families.values()))
        self.assertEqual(len(set.union(*split_families.values())), 3)
        pilot = [r for r in manifest["records"] if r["partition"] == "pilot"]
        self.assertEqual({(r["separation"], r["occlusion"]) for r in pilot},
                         {("near", "clear"), ("near", "blocked"),
                          ("far", "clear"), ("far", "blocked")})
        sample = pilot[0]
        obj = json.loads((first / sample["study"]).read_text())
        self.assertEqual({x["ground_truth_patch_id"] for x in obj["requests"]},
                         {None, "target"})

    def test_occlusion_and_evaluator_separation(self):
        out, manifest = self.generate()
        cases = [r for r in manifest["records"] if r["partition"] == "pilot"
                 and r["separation"] == "near"]
        by_state = {r["occlusion"]: load_scene(out / r["scene"])[0] for r in cases}
        self.assertIn("target", PlanarSimulator(by_state["clear"])
                      .visible_patches(by_state["clear"].start))
        self.assertNotIn("target", PlanarSimulator(by_state["blocked"])
                         .visible_patches(by_state["blocked"].start))

    def test_descriptive_family_level_run(self):
        out, _ = self.generate()
        report = analyze_localization_population(out / "manifest.json")
        self.assertEqual(report["family_count"], 1)
        self.assertEqual(report["study_count"], 4)
        self.assertEqual(report["inference"], "descriptive_only_no_ci_no_p_value")
        self.assertEqual(len(report["factor_strata"]), 8)
        self.assertEqual(set(report["mean_family_wrong_risk"]),
                         {"bearing_proxy", "range_proxy", "joint_proxy"})
        for method in report["mean_family_wrong_risk"]:
            total = sum(r[method]["eligible_requests"]
                        for r in report["factor_strata"].values())
            self.assertEqual(total, 8)
        self.assertNotIn("holdout", json.dumps(report))

    def test_refuses_overwrite_holdout_and_tampered_inputs(self):
        out, manifest = self.generate()
        with self.assertRaisesRegex(ValueError, "already exists"):
            generate_localization_population(self.spec, out)
        with self.assertRaisesRegex(ValueError, "holdout"):
            analyze_localization_population(out / "manifest.json", "holdout")
        holdout = next(r for r in manifest["records"] if r["partition"] == "holdout")
        (out / holdout["scene"]).write_text("invalid json")
        self.assertEqual(analyze_localization_population(
            out / "manifest.json")["study_count"], 4)
        pilot = next(r for r in manifest["records"] if r["partition"] == "pilot")
        (out / pilot["scene"]).write_text("{}")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            analyze_localization_population(out / "manifest.json")

    def test_invalid_design_and_duplicate_spec_key(self):
        broken = json.loads(self.spec.read_text())
        for mutation in (
            {"replicates_per_cell": 0},
            {"family_counts": {"development": 1, "pilot": 0, "holdout": 1}},
            {"master_seed": True},
            {"sensor": "../outside.json"},
            {"design": "physical_validation"},
        ):
            self.spec.write_text(json.dumps(broken | mutation))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.generate("bad")
        self.spec.write_text('{"study_id":"02","study_id":"02"}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            self.generate("bad2")

    def test_cli_generate_and_replay(self):
        directory = self.root / "cli_population"
        self.assertEqual(main(["localize-population", "--spec", str(self.spec),
                               "--output-dir", str(directory)]), 0)
        output = self.root / "pilot.json"
        self.assertEqual(main(["localize", "--population-manifest",
                               str(directory / "manifest.json"), "--partition", "pilot",
                               "--output", str(output)]), 0)
        self.assertEqual(json.loads(output.read_text())["study_count"], 4)
        raw = output.read_bytes()
        with self.assertRaises(SystemExit) as exc:
            main(["localize", "--population-manifest",
                  str(directory / "manifest.json"), "--output", str(output)])
        self.assertEqual(exc.exception.code, 2)
        self.assertEqual(raw, output.read_bytes())


if __name__ == "__main__":
    unittest.main()
