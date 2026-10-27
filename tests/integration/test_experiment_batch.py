"""Offline experiment batch contract: no holdout access, no overwrites."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from rvi.cli import main
from rvi.conditions import generate_conditions
from rvi.experiment import run_experiment
from rvi.population import generate_population

ROOT = Path(__file__).resolve().parents[2]
CONDITIONS = ROOT / "simulation/conditions/study01_pilot.json"
POPULATION = ROOT / "simulation/conditions/study01_population_pilot.json"
FIXTURE = ROOT / "simulation/suites/fixture_smoke.json"


class ExperimentBatchTests(unittest.TestCase):
    def test_simulation_paired_trials_receipt_and_resume_never_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "generated"
            source = generate_conditions(CONDITIONS, generated)
            output = root / "output"
            first = run_experiment(manifest=generated / "manifest.json", output_dir=output)
            self.assertEqual({p.name for p in output.iterdir()},
                             {"receipt.json", "summary.json", "trials.json"})
            rows = json.loads((output / "trials.json").read_text())
            stats = json.loads((output / "summary.json").read_text())
            self.assertEqual(stats["independent_unit"], "geometry_family")
            self.assertEqual(stats["evidence_type"], "simulation")
            self.assertEqual(stats["families"], 2)
            self.assertEqual(stats["scenarios"], 12)
            self.assertEqual(stats["trials"], 36)
            self.assertEqual(len(rows), 36)
            self.assertEqual({r["method"] for r in rows},
                             {"fixed_order", "greedy_distance", "greedy_coverage"})
            self.assertEqual({r["condition"] for r in rows}, {"nominal", "occluded"})
            self.assertTrue(any(r["status"] == "algorithm_failure" for r in rows))
            self.assertEqual({r["seeds"]["sensor"] for r in rows}, {None})
            self.assertEqual(len({r["trial_id"] for r in rows}), 36)
            self.assertTrue(all(r["independent_unit"] in source["partitions"]["pilot"]
                                for r in rows))
            before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                      for p in output.iterdir()}
            self.assertEqual(run_experiment(manifest=generated / "manifest.json",
                                            output_dir=output, resume=True), first)
            self.assertEqual({p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                              for p in output.iterdir()}, before)
            with self.assertRaisesRegex(ValueError, "already exists"):
                run_experiment(manifest=generated / "manifest.json", output_dir=output)

    def test_fixture_suite_smoke_is_distinct_from_simulation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "fixture"
            r = run_experiment(suite=FIXTURE, output_dir=output)
            stats = json.loads((output / "summary.json").read_text())
            rows = json.loads((output / "trials.json").read_text())
            self.assertEqual(stats["evidence_type"], "fixture")
            self.assertEqual(stats["trials"], 9)
            self.assertEqual(stats["families"], 3)
            self.assertEqual(stats["partition"], "fixture_smoke")
            self.assertEqual(r, run_experiment(suite=FIXTURE, output_dir=output, resume=True))
            with self.assertRaisesRegex(ValueError, "exactly one"):
                run_experiment(output_dir=root / "neither")
            with self.assertRaisesRegex(ValueError, "fixture-only"):
                run_experiment(suite=ROOT / "simulation/suites/geometric_smoke.json",
                               output_dir=root / "wrong_type")
            with self.assertRaisesRegex(ValueError, "partition selector"):
                run_experiment(suite=FIXTURE, partition="development",
                               output_dir=root / "bad_partition")

    def test_holdout_bytes_never_opened_and_holdout_partition_forbidden(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "generated"
            generate_population(POPULATION, generated)
            manifest = generated / "manifest.json"
            holdout = next((generated / "scenes/holdout").glob("*.json"))
            holdout.write_bytes(b"intentionally unread hidden contents")
            receipt = run_experiment(manifest=manifest, output_dir=root / "pilot")
            self.assertEqual(json.loads((root / "pilot/summary.json").read_text())["families"], 12)
            self.assertEqual(json.loads((root / "pilot/summary.json").read_text())["trials"], 144)
            self.assertEqual(run_experiment(manifest=manifest, output_dir=root / "pilot",
                                            resume=True), receipt)
            with self.assertRaisesRegex(ValueError, "holdout"):
                run_experiment(manifest=manifest, partition="holdout",
                               output_dir=root / "forbidden")
            with self.assertRaisesRegex(ValueError, "holdout"):
                run_experiment(manifest=manifest, partition="confirmation",
                               output_dir=root / "forbidden2")

    def test_corrupt_receipt_outputs_manifest_and_selected_scene_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "generated"
            generate_conditions(CONDITIONS, generated)
            manifest = generated / "manifest.json"
            output = root / "run"
            run_experiment(manifest=manifest, output_dir=output)
            original = (output / "trials.json").read_bytes()
            (output / "trials.json").write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, "corrupted"):
                run_experiment(manifest=manifest, output_dir=output, resume=True)
            (output / "trials.json").write_bytes(original)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["partitions"]["holdout"][0] = data["partitions"]["pilot"][0]
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "leaked"):
                run_experiment(manifest=manifest, output_dir=root / "bad_split")
            # No newly created outputs from invalid inputs.
            self.assertFalse((root / "bad_split").exists())

    def test_changed_selected_scene_blocks_replay_even_if_receipt_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "generated"
            generate_conditions(CONDITIONS, generated)
            manifest = generated / "manifest.json"
            run_experiment(manifest=manifest, output_dir=root / "result")
            selected = next((generated / "scenes/pilot").glob("*.json"))
            selected.write_bytes(selected.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                run_experiment(manifest=manifest, output_dir=root / "result", resume=True)

    def test_cross_run_deterministic_artifacts_except_utc_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "generated"
            generate_conditions(CONDITIONS, generated)
            run_experiment(manifest=generated / "manifest.json", output_dir=root / "a")
            run_experiment(manifest=generated / "manifest.json", output_dir=root / "b")
            for filename in ("trials.json", "summary.json"):
                self.assertEqual((root / "a" / filename).read_bytes(),
                                 (root / "b" / filename).read_bytes())
            report = json.loads((root / "a" / "receipt.json").read_text())
            for name, meta in report["artifacts"].items():
                data = (root / "a" / name).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), meta["sha256"])
                self.assertEqual(len(data), meta["size_bytes"])

    def test_cli_batch_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "batch"
            args = ["batch", "--suite", str(FIXTURE), "--output-dir", str(output)]
            with redirect_stdout(StringIO()):
                self.assertEqual(main(args), 0)
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as e:
                main(args)
            self.assertEqual(e.exception.code, 2)
            with redirect_stdout(StringIO()):
                self.assertEqual(main(args + ["--resume"]), 0)


if __name__ == "__main__":
    unittest.main()
