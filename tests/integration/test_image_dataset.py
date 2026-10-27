"""PGM image input and independent annotation regression for Study 02."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from rvi.cli import main
from rvi.image_dataset import (
    _predictions, _score, _summary, evaluate_image_manifest, read_pgm,
)

SAMPLES = {
    "template": bytes((35, 10, 0, 255)),
    "target": bytes((35, 10, 0, 255)),
    "distractor": bytes((255, 255, 255, 255)),
    "absent": bytes((128, 128, 128, 128)),
}


class ImageDatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "images").mkdir()
        (self.root / "sessions").mkdir()
        self.images = {}
        for name, pixels in SAMPLES.items():
            path = self.root / "images" / (name + ".pgm")
            path.write_bytes(b"P5\n# 8-bit experimental crop\n2 2\n255\n" + pixels)
            self.images[name] = self.pointer(path)
        self.manifest_path = self.root / "manifest.json"
        self.manifest = {
            "schema_version": "1.0.0",
            "study_id": "02", "evidence_type": "image_observation",
            "stage": "exploratory_not_confirmatory",
            "data_origin": "synthetic_test",
            "data_rights": "operator_declared_authorized",
            "threshold": 1.0, "ambiguity_margin": 0.0, "max_range_m": 10.0,
            "records": [],
        }
        for part, family, session in (
            ("development", "family_dev", "session_dev"),
            ("pilot", "family_pilot", "session_01"),
            ("pilot", "family_pilot", "session_02"),
            ("holdout", "family_holdout", "session_holdout"),
        ):
            observations = {
                "schema_version": "1.0.0", "session_id": session,
                "requests": [
                    {
                        "request_id": "target_request",
                        "timestamp_utc": "2026-10-27T10:00:00Z",
                        "status": "captured", "template": self.images["template"],
                        "expected_range_m": 2.0,
                        "candidates": [
                            {"id": "anon_a", "range_m": 3.0,
                             "image": self.images["target"]},
                            {"id": "anon_b", "range_m": 2.0,
                             "image": self.images["distractor"]},
                        ],
                    },
                    {
                        "request_id": "absent_request",
                        "timestamp_utc": "2026-10-27T10:00:01+00:00",
                        "status": "captured", "template": self.images["absent"],
                        "expected_range_m": 2.0,
                        "candidates": [
                            {"id": "anon_a", "range_m": 3.0,
                             "image": self.images["target"]},
                            {"id": "anon_b", "range_m": 2.0,
                             "image": self.images["distractor"]},
                        ],
                    },
                    {
                        "request_id": "missing_request",
                        "timestamp_utc": "2026-10-27T10:00:02Z",
                        "status": "missing_frame", "template": self.images["template"],
                        "expected_range_m": 2.0, "candidates": [],
                    },
                ],
            }
            reference = {
                "schema_version": "1.0.0", "session_id": session,
                "labels": [
                    {"request_id": "target_request", "target_present": True,
                     "target_candidate_id": "anon_a"},
                    {"request_id": "absent_request", "target_present": False,
                     "target_candidate_id": None},
                    {"request_id": "missing_request", "target_present": True,
                     "target_candidate_id": None},
                ],
            }
            obs_path = self.root / "sessions" / (session + ".observations.json")
            ref_path = self.root / "sessions" / (session + ".reference.json")
            self.write_json(obs_path, observations)
            self.write_json(ref_path, reference)
            self.manifest["records"].append({
                "partition": part, "object_family_id": family, "session_id": session,
                "observations": self.pointer(obs_path),
                "reference": self.pointer(ref_path),
            })
        self.save_manifest()

    def write_json(self, path, data):
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def pointer(self, path):
        return {"path": path.relative_to(self.root).as_posix(),
                "sha256": sha256(path.read_bytes()).hexdigest()}

    def save_manifest(self):
        self.write_json(self.manifest_path, self.manifest)

    def mutate_session(self, session, *, reference=False, action=None):
        kind = "reference" if reference else "observations"
        record = next(r for r in self.manifest["records"]
                      if r["session_id"] == session)
        path = self.root / record[kind]["path"]
        contents = json.loads(path.read_text())
        action(contents)
        self.write_json(path, contents)
        record[kind] = self.pointer(path)
        self.save_manifest()

    def test_binary_and_text_pgm_parsers(self):
        path = self.root / "images" / "target.pgm"
        self.assertEqual(read_pgm(path), (2, 2, SAMPLES["target"]))
        text = self.root / "images" / "ascii.pgm"
        text.write_bytes(b"P2\n# sample\n2 2\n255\n 35 10 # inline\n0 255\n")
        self.assertEqual(read_pgm(text), (2, 2, SAMPLES["target"]))
        for broken in (
            b"P5\n2 2\n255\n" + bytes((1, 2, 3)),
            b"P5\n2 2\n65535\n" + bytes((1, 2, 3, 4)),
            b"P2\n2 2\n255\n0 1 2 256\n",
            b"P2\n2 2\n255\n0 1 2 3 4\n",
            b"P5\n0 2\n255\n",
        ):
            text.write_bytes(broken)
            with self.subTest(broken=broken[:20]), self.assertRaises(ValueError):
                read_pgm(text)

    def test_paired_outcomes_and_denominators(self):
        report = evaluate_image_manifest(self.manifest_path)
        self.assertEqual((report["family_count"], report["session_count"]), (1, 2))
        self.assertEqual(len(report["session_summary"]), 2)
        self.assertEqual(len(report["trials"]), 18)
        image = report["family_summary"]["family_pilot"]["image_mae"]
        range_only = report["family_summary"]["family_pilot"]["range_only"]
        self.assertEqual(image["eligible_requests"], 6)
        self.assertEqual(image["correct_selection"], 2)
        self.assertEqual(range_only["wrong_selection"], 4)
        self.assertEqual(image["missing_frames"], 2)
        self.assertEqual(image["abstained"], 2)
        self.assertEqual(image["correct_rejection"], 0)
        self.assertEqual(report["inference"], "descriptive_only_no_ci_no_p_value")
        self.assertEqual(set(report["target_strata"]), {"absent", "present"})
        self.assertEqual(report["data_rights"],
                         "operator_declaration_not_independently_verified")
        self.assertNotIn("gray8", json.dumps(report))

    def test_truth_change_does_not_change_predictions(self):
        before = evaluate_image_manifest(self.manifest_path)
        self.mutate_session("session_01", reference=True,
                            action=lambda ref: ref["labels"][0].update(
                                {"target_candidate_id": "anon_b"}))
        after = evaluate_image_manifest(self.manifest_path)
        a = [r["selected_id"] for r in before["trials"]]
        b = [r["selected_id"] for r in after["trials"]]
        self.assertEqual(a, b)
        self.assertNotEqual(
            before["family_summary"]["family_pilot"]["image_mae"]["wrong_selection"],
            after["family_summary"]["family_pilot"]["image_mae"]["wrong_selection"])

    def test_reference_is_not_a_policy_input(self):
        observed = json.loads((self.root / "sessions/session_01.observations.json").read_text())
        decisions, candidate_ids = _predictions(self.root, observed, 1, 0, 10)
        ref_path = self.root / "sessions/session_01.reference.json"
        original = json.loads(ref_path.read_text())
        changed = json.loads(ref_path.read_text())
        changed["labels"][0]["target_candidate_id"] = "anon_b"
        first = _score(decisions, original, candidate_ids, "session_01", "family_pilot")
        second = _score(decisions, changed, candidate_ids, "session_01", "family_pilot")
        self.assertEqual([r["selected_id"] for r in first],
                         [r["selected_id"] for r in second])
        self.assertNotEqual([r["status"] for r in first],
                            [r["status"] for r in second])

    def test_exploratory_holdout_is_unopened(self):
        holdout = self.root / "sessions/session_holdout.observations.json"
        holdout.write_text("intentionally corrupted")
        self.assertEqual(evaluate_image_manifest(self.manifest_path)["session_count"], 2)
        with self.assertRaisesRegex(ValueError, "holdout"):
            evaluate_image_manifest(self.manifest_path, "holdout")

    def test_tampered_image_and_reference_fail_closed(self):
        image = self.root / "images/target.pgm"
        image.write_bytes(image.read_bytes() + b"\x00")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            evaluate_image_manifest(self.manifest_path)
        # Manifest verifies observation bytes before reference; restore image first.
        image.write_bytes(image.read_bytes()[:-1])
        ref = self.root / "sessions/session_01.reference.json"
        ref.write_text('{"tampered":true}')
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            evaluate_image_manifest(self.manifest_path)

    def test_family_splits_and_session_duplicates(self):
        self.manifest["records"][1]["object_family_id"] = "family_dev"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "crossing partitions"):
            evaluate_image_manifest(self.manifest_path)
        self.manifest["records"][1]["object_family_id"] = "family_pilot"
        self.manifest["records"][2]["session_id"] = "session_01"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "duplicate session"):
            evaluate_image_manifest(self.manifest_path)

    def test_invalid_timestamp_and_ground_truth(self):
        self.mutate_session("session_01", action=lambda obs:
                            obs["requests"][1].update(
                                {"timestamp_utc": "2026-10-27T09:00:00Z"}))
        with self.assertRaisesRegex(ValueError, "monotonic"):
            evaluate_image_manifest(self.manifest_path)
        self.mutate_session("session_01", action=lambda obs:
                            obs["requests"][1].update(
                                {"timestamp_utc": "2026-10-27T10:00:01Z"}))
        self.mutate_session("session_01", reference=True,
                            action=lambda ref: ref["labels"][0].update(
                                {"target_candidate_id": "unknown_id"}))
        with self.assertRaisesRegex(ValueError, "unknown detection"):
            evaluate_image_manifest(self.manifest_path)

    def test_bad_paths_and_invalid_capture(self):
        self.mutate_session("session_01", action=lambda obs:
                            obs["requests"][0]["candidates"][0]["image"].update(
                                {"path": "../../private.pgm"}))
        with self.assertRaisesRegex(ValueError, "relative path"):
            evaluate_image_manifest(self.manifest_path)
        self.mutate_session("session_01", action=lambda obs:
                            obs["requests"][0]["candidates"][0]["image"].update(
                                {"path": "images/target.pgm"}))
        self.mutate_session("session_01", action=lambda obs:
                            obs["requests"][2].update({"status": "captured"}))
        self.assertEqual(evaluate_image_manifest(
            self.manifest_path)["session_count"], 2)

    def test_cli_and_exclusive_output(self):
        output = self.root / "result.json"
        args = ["localize", "--image-manifest", str(self.manifest_path),
                "--partition", "pilot", "--output", str(output)]
        self.assertEqual(main(args), 0)
        self.assertEqual(json.loads(output.read_text())["family_count"], 1)
        original = output.read_bytes()
        with self.assertRaises(SystemExit) as exc:
            main(args)
        self.assertEqual(exc.exception.code, 2)
        self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
