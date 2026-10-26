"""Fixture-level instance-assignment regression and evaluator separation."""
import json
from pathlib import Path
import tempfile
import unittest

from rvi.localization import run_localization_fixture, select_instance
from rvi.cli import main

ROOT = Path(__file__).resolve().parents[2]


class LocalizationTests(unittest.TestCase):
    def test_method_ranking_and_nonleaking_reference(self):
        candidates = [
            {"id": "a", "visual_distance": 0.1, "spatial_distance": 0.9},
            {"id": "b", "visual_distance": 0.7, "spatial_distance": 0.1},
        ]
        self.assertEqual(select_instance(candidates, "visual", 1, 0)["selected_id"], "a")
        self.assertEqual(select_instance(candidates, "spatial", 1, 0)["selected_id"], "b")
        self.assertEqual(select_instance(candidates, "fused", 1, 0)["selected_id"], "b")

    def test_ambiguous_exact_tie_abstains(self):
        candidates = [
            {"id": "b", "visual_distance": 0.2, "spatial_distance": 0.2},
            {"id": "a", "visual_distance": 0.2, "spatial_distance": 0.2},
        ]
        self.assertEqual(select_instance(candidates, "fused", .3, 0)["decision"], "ambiguous")

    def test_margin_and_inclusive_threshold(self):
        candidates = [{"id": "a", "visual_distance": .5, "spatial_distance": .5}]
        self.assertEqual(select_instance(candidates, "visual", .5, 0)["selected_id"], "a")
        self.assertEqual(select_instance(candidates, "visual", .499, 0)["selected_id"], None)

    def test_no_candidate_abstains(self):
        self.assertEqual(select_instance([], "fused", .5, 0)["decision"], "no_candidate")

    def test_reject_bad_inputs(self):
        for candidates in (
            [{"id": "x", "visual_distance": True, "spatial_distance": 0.3}],
            [{"id": "x", "visual_distance": float("nan"), "spatial_distance": 0.3}],
            [{"id": "x", "visual_distance": 1.2, "spatial_distance": 0.3}],
            [{"id": "x", "visual_distance": .1, "spatial_distance": .1}] * 2,
            [{"id": "", "visual_distance": .1, "spatial_distance": .1}],
        ):
            with self.subTest(candidates=candidates), self.assertRaises(ValueError):
                select_instance(candidates, "fused", .5, 0)
        with self.assertRaises(ValueError):
            select_instance([], "other", .5, 0)
        with self.assertRaises(ValueError):
            select_instance([], "visual", True, 0)

    def test_absent_target_and_wrong_identity_denominators(self):
        sample = ROOT / "simulation" / "suites" / "localization_fixture.json"
        report = run_localization_fixture(sample)
        self.assertEqual(report["evidence_type"], "fixture")
        self.assertEqual(len(report["trials"]), 9)
        self.assertEqual(report["summary"]["visual"]["eligible_requests"], 3)
        self.assertEqual(report["summary"]["visual"]["correct_rejection"], 1)
        self.assertEqual(report["summary"]["visual"]["wrong_selection"], 0)
        self.assertEqual(report["summary"]["visual"]["abstained"], 1)
        self.assertEqual(report["summary"]["spatial"]["correct_selection"], 2)
        self.assertEqual(report["summary"]["fused"]["correct_selection"], 2)

    def test_reject_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"schema_version": "1.0.0", "schema_version": "1.0.0"}')
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                run_localization_fixture(path)

    def test_cli_output_and_preserve_existing(self):
        sample = ROOT / "simulation" / "suites" / "localization_fixture.json"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "result.json"
            self.assertEqual(main(["localize", "--fixture", str(sample),
                                   "--output", str(target)]), 0)
            report = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["visual"]["eligible_requests"], 3)
            original = target.read_bytes()
            with self.assertRaises(SystemExit) as exc:
                main(["localize", "--fixture", str(sample), "--output", str(target)])
            self.assertEqual(exc.exception.code, 2)
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
