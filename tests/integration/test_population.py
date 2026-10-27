"""Synthetic family sampling tests; these are not physical validation data."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest import mock

from rvi.adapters.simulator import load_scene, PlanarSimulator
from rvi.benchmark import run_benchmark
from rvi.pilot import analyze_pilot
from rvi.population import generate_population

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "simulation/conditions/study01_population_pilot.json"


class PopulationGenerationTests(unittest.TestCase):
    def test_replay_hashes_family_splits_and_pairing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initial_rng = random.getstate()
            first = generate_population(SPEC, root / "first")
            self.assertEqual(random.getstate(), initial_rng)
            second = generate_population(SPEC, root / "second")
            self.assertEqual(first, second)
            self.assertEqual(first["design"], "sampled_geometry_v1")
            self.assertEqual({k: len(v) for k, v in first["partitions"].items()},
                             {"development": 8, "pilot": 12, "holdout": 12})
            self.assertEqual(len(first["scenes"]), 128)
            self.assertEqual(len({x["scene_id"] for x in first["scenes"]}), 128)
            members = list(first["partitions"].values())
            for i in range(len(members)):
                for j in range(i):
                    self.assertFalse(set(members[i]) & set(members[j]))
            pairs = {}
            family_layouts = {}
            for row in first["scenes"]:
                scene_path = root / "first" / row["path"]
                raw = scene_path.read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
                self.assertEqual(raw, (root / "second" / row["path"]).read_bytes())
                data = json.loads(raw)
                scene, _ = load_scene(scene_path)
                simulator = PlanarSimulator(scene)
                self.assertEqual(scene.identifier, row["scene_id"])
                first_view = simulator.visible_patches(scene.route[0])
                if row["condition"] == "nominal":
                    self.assertIn("surface_01", first_view)
                else:
                    self.assertNotIn("surface_01", first_view)
                pairs.setdefault(row["pair_id"], []).append((row, data))
                family_layouts.setdefault(row["family"], []).append(
                    tuple(round(p["area_m2"], 8) for p in data["patches"]))
            self.assertEqual(len(pairs), 64)
            for items in pairs.values():
                self.assertEqual(len(items), 2)
                a, b = [item[1] for item in items]
                for data in (a, b):
                    data.pop("scene_id")
                    data.pop("obstacles")
                self.assertEqual(a, b)
                self.assertEqual({item[0]["condition"] for item in items}, {"nominal", "occluded"})
                self.assertEqual(len({item[0]["paired_seed"] for item in items}), 1)
            # Replicates share family latent areas; different family draws are not
            # repetitions of the same fixed six hand-authored templates.
            self.assertTrue(all(len(set(layouts)) == 1 for layouts in family_layouts.values()))
            self.assertGreater(len({layouts[0] for layouts in family_layouts.values()}), 25)

    def test_pilot_reports_independent_family_count_without_opening_holdout(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "scenes"
            generated = generate_population(SPEC, output)
            report = run_benchmark(output / generated["suites"]["pilot"]["path"])
            self.assertEqual(len(report["scenes"]), 48)
            self.assertEqual(len(report["trials"]), 144)
            self.assertEqual(report["visibility_access"], "known_geometry_oracle")
            summary = analyze_pilot(output / "manifest.json")
            self.assertEqual(summary["families"], 12)
            self.assertEqual(summary["pairs"], 24)
            self.assertEqual(summary["uncertainty"]["status"], "exploratory_cluster_bootstrap")
            self.assertEqual(len(summary["uncertainty"]["confidence_intervals"]["completion_loss_difference"]), 2)
            holdout = next((output / "scenes/holdout").glob("*.json"))
            holdout.write_text("not a valid scene")
            self.assertEqual(analyze_pilot(output / "manifest.json")["estimated_effects"],
                             summary["estimated_effects"])

    def test_invalid_specs_do_not_create_output(self):
        specification = json.loads(SPEC.read_text(encoding="utf-8"))
        changes = [
            {"design": "unknown"}, {"conditions": ["occluded", "nominal"]},
            {"master_seed": -1}, {"master_seed": True},
            {"replicates_per_family": 0}, {"replicates_per_family": 9},
            {"family_counts": {"development": 8, "pilot": 0, "holdout": 12}},
            {"family_counts": {"development": 64, "pilot": 64, "holdout": 64}},
            {"family_counts": {"development": 8, "pilot": True, "holdout": 12}},
            {"unexpected": 0},
        ]
        with tempfile.TemporaryDirectory() as temp:
            for index, override in enumerate(changes):
                with self.subTest(index=index):
                    path = Path(temp) / f"spec_{index}.json"
                    path.write_text(json.dumps(specification | override), encoding="utf-8")
                    destination = Path(temp) / f"data_{index}"
                    with self.assertRaises(ValueError):
                        generate_population(path, destination)
                    self.assertFalse(destination.exists())
            path = Path(temp) / "duplicate.json"
            path.write_text('{"master_seed":1,"master_seed":2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                generate_population(path, Path(temp) / "duplicate_output")

    def test_existing_directory_and_write_error_are_non_destructive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "data"
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("keep")
            with self.assertRaisesRegex(ValueError, "already exists"):
                generate_population(SPEC, output)
            self.assertEqual(sentinel.read_text(), "keep")
            original_open = Path.open

            def fail(path, mode="r", *args, **kwargs):
                if path.name == "pilot.json" and path.parent.name == "suites" and mode == "xb":
                    raise OSError("synthetic disk failure")
                return original_open(path, mode, *args, **kwargs)

            with mock.patch.object(Path, "open", fail):
                with self.assertRaisesRegex(OSError, "synthetic disk failure"):
                    generate_population(SPEC, root / "created")
            self.assertFalse((root / "created").exists())
            self.assertEqual(sentinel.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
