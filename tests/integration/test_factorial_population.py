"""Exploratory crossed-factor P01 generation, balancing and QA."""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from rvi.adapters.simulator import PlanarSimulator, load_scene
from rvi.benchmark import run_benchmark
from rvi.perception import load_sensor_config, simulate_sensor
from rvi.population import generate_population

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "simulation/conditions/study01_factorial_pilot.json"


class FactorialPopulationTests(unittest.TestCase):
    def test_crossed_cells_hashes_and_group_balance(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "first", Path(tmp) / "repeat"
            first = generate_population(SPEC, a)
            second = generate_population(SPEC, b)
            self.assertEqual(first, second)
            self.assertEqual(first["design"], "sampled_factorial_v1")
            self.assertEqual(first["stage"], "exploratory_not_confirmatory")
            self.assertEqual(first["holdout_state"], "generated_not_blinded_or_frozen")
            self.assertEqual(len(first["cells"]), 12)
            self.assertEqual(len(first["scenes"]), 216)
            self.assertEqual(len(first["sensor_configs"]), 2)
            self.assertEqual(len({r["scene_id"] for r in first["scenes"]}), 216)
            self.assertEqual(len({r["pair_id"] for r in first["scenes"]}), 18)
            members = [set(x) for x in first["partitions"].values()]
            self.assertFalse(any(members[i] & members[j]
                                 for i in range(3) for j in range(i)))
            buckets = Counter((row["partition"], row["cell_id"],
                               row["geometry_patch_count"])
                              for row in first["scenes"])
            self.assertEqual(len(buckets), 3 * 12 * 3)
            self.assertEqual(set(buckets.values()), {2})
            groupings = defaultdict(list)
            for row in first["scenes"]:
                raw = (a / row["path"]).read_bytes()
                self.assertEqual(sha256(raw).hexdigest(), row["sha256"])
                self.assertEqual(raw, (b / row["path"]).read_bytes())
                world, _ = load_scene(a / row["path"])
                PlanarSimulator(world)
                self.assertEqual(len(world.patches), row["geometry_patch_count"])
                groupings[row["pair_id"]].append((row, json.loads(raw)))
            self.assertEqual({len(v) for v in groupings.values()}, {12})
            for rows in groupings.values():
                self.assertEqual(len({r["paired_seed"] for r, _ in rows}), 1)
                for _, world in rows:
                    world.pop("scene_id")
                    world.pop("obstacles")
                self.assertTrue(all(world == rows[0][1] for _, world in rows))
            for split in ("development", "pilot", "holdout"):
                self.assertEqual(len(first["suites"][split]), 12)
                for item in first["suites"][split].values():
                    self.assertEqual(sha256((a / item["path"]).read_bytes()).hexdigest(),
                                     item["sha256"])
                    self.assertTrue((a / item["sensor_config"]).is_file())

    def test_factor_changes_are_separated_and_monotone_in_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "data"
            manifest = generate_population(SPEC, out)
            rows = [r for r in manifest["scenes"]
                    if r["partition"] == "pilot"
                    and r["pair_id"] == manifest["scenes"][72]["pair_id"]]
            self.assertEqual(len(rows), 12)
            by_factor = {tuple(r["factors"][name] for name in (
                "occlusion", "illumination", "clutter")): r for r in rows}
            geometries = {}
            for key, record in by_factor.items():
                world, _ = load_scene(out / record["path"])
                geometries[key] = world
            none = geometries[("none", "reference", "none")]
            medium = geometries[("moderate", "reference", "none")]
            strong = geometries[("strong", "reference", "none")]
            cluttered = geometries[("none", "reference", "dense")]
            self.assertEqual([len(x.obstacles) for x in
                              (none, medium, strong, cluttered)], [0, 1, 1, 2])
            self.assertLess(medium.obstacles[0].radius_m,
                            strong.obstacles[0].radius_m)
            self.assertEqual(none.patches, strong.patches)
            self.assertEqual(none.route, strong.route)
            self.assertEqual(none.camera, strong.camera)
            self.assertEqual(none.motion, strong.motion)
            self.assertEqual(
                [(x.x, x.y, x.radius_m) for x in
                 geometries[("moderate", "low", "dense")].obstacles],
                [(x.x, x.y, x.radius_m) for x in
                 geometries[("moderate", "reference", "dense")].obstacles])
            self.assertIn("surface_01",
                          PlanarSimulator(none).visible_patches(none.route[0]))
            self.assertNotIn("surface_01",
                             PlanarSimulator(medium).visible_patches(medium.route[0]))

    def test_factor_sensor_and_pilot_benchmark_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "data"
            manifest = generate_population(SPEC, out)
            low_cfg = out / manifest["sensor_configs"]["low"]["path"]
            high_cfg = out / manifest["sensor_configs"]["reference"]["path"]
            low, _ = load_sensor_config(low_cfg)
            high, _ = load_sensor_config(high_cfg)
            self.assertLess(low.illumination_relative, high.illumination_relative)
            same = {k: v for k, v in vars(low).items()
                    if k != "illumination_relative"}
            self.assertEqual(same, {k: v for k, v in vars(high).items()
                                    if k != "illumination_relative"})
            cell = "o_none__i_reference__c_none"
            suite = out / manifest["suites"]["pilot"][cell]["path"]
            report = run_benchmark(suite, high_cfg)
            self.assertEqual(report, run_benchmark(suite, high_cfg))
            self.assertEqual(len(report["scenes"]), 6)
            self.assertEqual(len(report["trials"]), 18)
            self.assertEqual(report["visibility_access"], "observations_only")
            self.assertEqual({x["trial_count"] for x in report["summary"]}, {6})
            world, _ = load_scene(out / manifest["scenes"][72]["path"])
            p_low, _ = simulate_sensor(world, world.start, low)
            p_high, _ = simulate_sensor(world, world.start, high)
            self.assertEqual(len(p_low["detections"]), len(p_high["detections"]))
            self.assertEqual([d["u_px"] for d in p_low["detections"]],
                             [d["u_px"] for d in p_high["detections"]])
            self.assertNotEqual([d["brightness_gray_8bit"] for d in p_low["detections"]],
                                [d["brightness_gray_8bit"] for d in p_high["detections"]])

    def test_invalid_factorial_specs_and_existing_output_are_nondestructive(self):
        template = json.loads(SPEC.read_text(encoding="utf-8"))
        variants = [
            {"master_seed": True}, {"master_seed": -1},
            {"replicates_per_family": 0}, {"replicates_per_family": 5},
            {"family_counts": {"development": 3, "pilot": 4, "holdout": 3}},
            {"family_counts": {"development": 48, "pilot": 48, "holdout": 48}},
            {"family_counts": {"development": True, "pilot": 6, "holdout": 6}},
            {"factors": {"occlusion": ["none"], "illumination": ["low", "reference"],
                         "clutter": ["none", "dense"]}},
            {"unexpected": 7}, {"design": "sampled_factorial_bogus"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for idx, change in enumerate(variants):
                spec = root / f"bad_{idx}.json"
                spec.write_text(json.dumps(template | change), encoding="utf-8")
                destination = root / f"generated_{idx}"
                with self.subTest(index=idx), self.assertRaises(ValueError):
                    generate_population(spec, destination)
                self.assertFalse(destination.exists())
            existing = root / "existing"
            existing.mkdir()
            (existing / "sentinel").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                generate_population(SPEC, existing)
            self.assertEqual((existing / "sentinel").read_text(), "keep")

    def test_failed_write_rolls_back_without_orphaned_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "output"
            old_open = Path.open

            def fail(path, mode="r", *args, **kwargs):
                if path.name.endswith("__c_dense.json") and mode == "xb":
                    raise OSError("simulated disk failure")
                return old_open(path, mode, *args, **kwargs)

            with mock.patch.object(Path, "open", fail):
                with self.assertRaisesRegex(OSError, "simulated disk failure"):
                    generate_population(SPEC, target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
