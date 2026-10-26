"""Correctness checks for exploratory scene generation, not scientific results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest import mock

from rvi.conditions import generate_conditions

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "simulation/conditions/study01_pilot.json"


class ConditionGenerationTests(unittest.TestCase):
    def test_deterministic_hashes_pairing_splits_and_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / "run_a", Path(temp) / "run_b"
            before = random.getstate()
            manifest = generate_conditions(SPEC, a)
            self.assertEqual(before, random.getstate())
            self.assertEqual(manifest, generate_conditions(SPEC, b))
            self.assertEqual(len(manifest["scenes"]), 36)
            self.assertEqual(len({row["scene_id"] for row in manifest["scenes"]}), 36)
            groups = {}
            for row in manifest["scenes"]:
                groups.setdefault(row["pair_id"], []).append(row)
                contents = (a / row["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(contents).hexdigest(), row["sha256"])
                self.assertEqual(contents, (b / row["path"]).read_bytes())
            self.assertEqual(len(groups), 18)
            for rows in groups.values():
                self.assertEqual({row["condition"] for row in rows}, {"nominal", "occluded"})
                self.assertEqual(len({row["paired_seed"] for row in rows}), 1)
                scenes = [json.loads((a / row["path"]).read_bytes()) for row in rows]
                for scene in scenes:
                    scene.pop("scene_id")
                    scene.pop("obstacles")
                self.assertEqual(scenes[0], scenes[1])
            splits = manifest["partitions"]
            for left in splits:
                for right in splits:
                    if left != right:
                        self.assertFalse(set(splits[left]) & set(splits[right]))
            for split, info in manifest["suites"].items():
                suite_path = a / info["path"]
                raw = suite_path.read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), info["sha256"])
                suite = json.loads(raw)
                self.assertEqual(len(suite["scenes"]), 12)
                for relative in suite["scenes"]:
                    self.assertTrue((suite_path.parent / relative).is_file())

    def test_invalid_specs_leave_no_artifacts(self):
        original = json.loads(SPEC.read_text())
        variants = [
            {"master_seed": -1}, {"master_seed": True}, {"master_seed": 2**64},
            {"replicates_per_family": 0}, {"replicates_per_family": 17},
            {"replicates_per_family": 2.0}, {"study_id": "02"},
            {"conditions": ["nominal"]},
            {"partitions": original["partitions"] | {"pilot": ["parallel_pair"]}},
            {"partitions": original["partitions"] | {"pilot": []}},
            {"extra": 1},
        ]
        with tempfile.TemporaryDirectory() as temp:
            for index, change in enumerate(variants):
                with self.subTest(index=index):
                    spec = Path(temp) / f"bad_{index}.json"
                    spec.write_text(json.dumps(original | change))
                    output = Path(temp) / f"out_{index}"
                    with self.assertRaises(ValueError):
                        generate_conditions(spec, output)
                    self.assertFalse(output.exists())
            dup = Path(temp) / "duplicate.json"
            dup.write_text('{"schema_version":"1.0.0","schema_version":"1.0.0"}')
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                generate_conditions(dup, Path(temp) / "dup_output")

    def test_write_failure_removes_only_new_artifacts(self):
        original_open = Path.open

        def fail_after_partial_generation(path, mode="r", *args, **kwargs):
            if path.name == "pilot.json" and path.parent.name == "suites" and mode == "xb":
                raise OSError("simulated storage failure")
            return original_open(path, mode, *args, **kwargs)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "generated"
            sentinel = root / "keep.txt"
            sentinel.write_text("unrelated")
            with mock.patch.object(Path, "open", fail_after_partial_generation):
                with self.assertRaisesRegex(OSError, "simulated storage failure"):
                    generate_conditions(SPEC, output)
            self.assertFalse(output.exists())
            self.assertEqual(sentinel.read_text(), "unrelated")
            # The same target can be safely used after the failure.
            self.assertEqual(len(generate_conditions(SPEC, output)["scenes"]), 36)

    def test_existing_output_is_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "results"
            output.mkdir()
            sentinel = output / "keep"
            sentinel.write_text("unchanged")
            with self.assertRaisesRegex(ValueError, "already exists"):
                generate_conditions(SPEC, output)
            self.assertEqual(sentinel.read_text(), "unchanged")


if __name__ == "__main__":
    unittest.main()
