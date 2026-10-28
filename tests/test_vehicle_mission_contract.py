"""Fail-closed contract tests for vehicle-level and part-level photo missions."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from rvi.vehicle_mission import assess_mission

_FIXTURES = Path(__file__).resolve().parents[1] / "simulation" / "suites"


def fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


class VehicleMissionTests(unittest.TestCase):
    def setUp(self):
        self.bumper = fixture("vehicle_photo_mission_bumper_fixture.json")
        self.whole = fixture("vehicle_photo_mission_whole_car_fixture.json")

    def test_mission_sources_are_session_and_capture_bound(self):
        bad = deepcopy(self.bumper)
        bad["target_grounding"]["decision"]["observation_ids"] = ["unknown-frame"]
        self.assertEqual(assess_mission(bad)["verdict"], "blocked_target")
        bad = deepcopy(self.bumper)
        bad["photo_attempts"][1]["observation_id"] = "nonexistent-frame"
        result = assess_mission(bad)
        self.assertEqual(result["verdict"], "invalid_trace")
        self.assertIn("capture_not_bound_to_matching_source", result["rejected_attempts"][1]["reasons"])
        bad = deepcopy(self.bumper)
        bad["photo_attempts"][1]["independent_qc"]["observation_id"] = "missing-qc"
        self.assertEqual(assess_mission(bad)["verdict"], "invalid_trace")
        bad = deepcopy(self.bumper)
        bad["observations"][0]["session_id"] = "another-session"
        with self.assertRaisesRegex(ValueError, "another mission session"):
            assess_mission(bad)
        bad = deepcopy(self.bumper)
        bad["return_evidence"]["observation_id"] = "wrong-handoff"
        self.assertEqual(assess_mission(bad)["verdict"], "invalid_trace")

    def test_chronology_identity_and_part_binding(self):
        bad = deepcopy(self.bumper)
        # Capture is associated with a different vehicle than its photo record.
        capture = next(x for x in bad["observations"] if x["kind"] == "capture")
        capture["vehicle_instance_id"] = "another-car"
        self.assertEqual(assess_mission(bad)["verdict"], "invalid_trace")
        bad = deepcopy(self.bumper)
        capture = next(x for x in bad["observations"] if x["kind"] == "capture")
        capture["timestamp_s"] = 0  # before target and part were identified
        self.assertIn("capture_not_after_grounding",
                      assess_mission(bad)["rejected_attempts"][0]["reasons"])
        bad = deepcopy(self.bumper)
        qc = next(x for x in bad["observations"] if x["kind"] == "independent_quality")
        qc["timestamp_s"] = 0  # reference result predates the photograph
        self.assertIn("qc_not_after_capture",
                      assess_mission(bad)["rejected_attempts"][0]["reasons"])
        bad = deepcopy(self.bumper)
        handoff = next(x for x in bad["observations"] if x["kind"] == "handoff")
        handoff["timestamp_s"] = 0
        report = assess_mission(bad)
        self.assertEqual(report["verdict"], "invalid_trace")
        self.assertIn("handoff_not_after_photo_and_qc", report["trace_violations"])
        bad = deepcopy(self.bumper)
        part = next(x for x in bad["observations"] if x["kind"] == "part_detection")
        part["vehicle_instance_id"] = "different-car"
        self.assertEqual(assess_mission(bad)["verdict"], "blocked_part")
        bad = deepcopy(self.bumper)
        bad["observations"][0]["timestamp_s"] = float("nan")
        with self.assertRaisesRegex(ValueError, "timestamp"):
            assess_mission(bad)

    def test_optional_capture_file_hash_verification(self):
        from tempfile import TemporaryDirectory
        from hashlib import sha256
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = deepcopy(self.bumper)
            photos = {p["observation_id"]: p for p in data["photo_attempts"]}
            for record in data["observations"]:
                if record["kind"] != "capture":
                    continue
                filename = record["id"] + ".txt"
                raw = record["id"].encode("utf-8")
                (root / filename).write_bytes(raw)
                checksum = sha256(raw).hexdigest()
                record.update(artifact_path=filename, source_sha256=checksum)
                photos[record["id"]]["image_sha256"] = checksum
                for qc in data["observations"]:
                    if qc["kind"] == "independent_quality" and qc["capture_observation_id"] == record["id"]:
                        qc["image_sha256"] = checksum
            report = assess_mission(data, artifact_root=root)
            self.assertEqual(report["verdict"], "fixture_complete")
            self.assertTrue(report["capture_bytes_verified"])
            (root / (data["photo_attempts"][0]["observation_id"] + ".txt")).write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                assess_mission(data, artifact_root=root)

    def test_bumper_recapture_after_specular_failure(self):
        r = assess_mission(self.bumper)
        self.assertEqual(r["verdict"], "fixture_complete")
        self.assertEqual((r["assigned_slots"], r["accepted_slots"]), (2, 2))
        self.assertEqual(len(r["rejected_attempts"]), 1)
        self.assertIn("specular_glare", r["rejected_attempts"][0]["reasons"])
        self.assertFalse(r["physical_robot_success"])

    def test_whole_vehicle_approved_eight_views_with_confirmed_target(self):
        r = assess_mission(self.whole)
        self.assertEqual(r["verdict"], "fixture_complete")
        self.assertEqual(r["accepted_slots"], 8)
        self.assertEqual(r["missing_slots"], [])

    def test_ambiguous_two_cars_never_choose_first_automatically(self):
        bad = deepcopy(self.whole)
        bad["target_grounding"]["decision"]["clarification_confirmed"] = False
        r = assess_mission(bad)
        self.assertEqual(r["verdict"], "blocked_target")
        self.assertFalse(r["target_grounded"])
        self.assertIn("unresolved_multi_car_ambiguity", r["trace_violations"])
        self.assertEqual(r["accepted_slots"], 0)

    def test_target_absent_does_not_produce_success(self):
        bad = deepcopy(self.bumper)
        bad["target_grounding"]["candidates"] = []
        bad["target_grounding"]["decision"] = {
            "status": "absent", "selected_instance_id": None,
            "clarification_confirmed": False, "observation_ids": [],
        }
        bad["photo_attempts"] = []
        self.assertEqual(assess_mission(bad)["verdict"], "blocked_target")

    def test_wrong_car_never_counts_as_accepted(self):
        bad = deepcopy(self.bumper)
        bad["photo_attempts"][1]["vehicle_instance_id"] = "car-02"
        r = assess_mission(bad)
        self.assertIn("bumper-centre", r["missing_slots"])
        self.assertIn("wrong_vehicle_identity", r["rejected_attempts"][1]["reasons"])

    def test_part_must_belong_to_selected_vehicle(self):
        bad = deepcopy(self.bumper)
        bad["part_grounding"]["parent_instance_id"] = "car-02"
        r = assess_mission(bad)
        self.assertEqual(r["verdict"], "blocked_part")
        self.assertEqual(r["accepted_slots"], 0)

    def test_glare_uncorrected_is_missing_evidence(self):
        bad = deepcopy(self.bumper)
        bad["photo_attempts"] = bad["photo_attempts"][:1] + bad["photo_attempts"][2:]
        r = assess_mission(bad)
        self.assertEqual(r["verdict"], "partial_coverage")
        self.assertIn("bumper-centre", r["missing_slots"])

    def test_return_requires_handoff_not_just_odometry(self):
        bad = deepcopy(self.whole)
        bad["return_evidence"]["operator_handoff_confirmed"] = False
        self.assertEqual(assess_mission(bad)["verdict"], "return_unverified")
        bad["return_evidence"]["operator_handoff_confirmed"] = True
        bad["return_evidence"]["anchor_id"] = "wrong_place"
        self.assertEqual(assess_mission(bad)["verdict"], "return_unverified")
        bad["return_evidence"]["anchor_id"] = "staging_operator_1"
        bad["return_evidence"]["safe_route_verified"] = False
        self.assertEqual(assess_mission(bad)["verdict"], "return_unverified")

    def test_unrelated_part_is_not_an_inspection_photo(self):
        bad = deepcopy(self.bumper)
        bad["photo_attempts"][1]["part"] = "front_bumper"
        r = assess_mission(bad)
        self.assertIn("wrong_part_or_view", r["rejected_attempts"][1]["reasons"])
        self.assertEqual(r["verdict"], "partial_coverage")

    def test_duplicate_photo_not_allowed_to_satisfy_multiple_views(self):
        bad = deepcopy(self.whole)
        bad["photo_attempts"][1]["image_sha256"] = bad["photo_attempts"][0]["image_sha256"]
        self.assertEqual(assess_mission(bad)["verdict"], "invalid_trace")

    def test_quality_cannot_be_assessed_by_same_planner(self):
        bad = deepcopy(self.whole)
        bad["photo_attempts"][0]["independent_qc"]["reference_separate_from_policy"] = False
        self.assertIn("vehicle-front", assess_mission(bad)["missing_slots"])

    def test_unapproved_or_empty_capture_plan_rejected(self):
        bad = deepcopy(self.whole)
        bad["shot_plan"]["approval_kind"] = "unapproved_model_guess"
        with self.assertRaisesRegex(ValueError, "approved or versioned"):
            assess_mission(bad)
        bad = deepcopy(self.whole)
        bad["shot_plan"]["required"] = []
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            assess_mission(bad)

    def test_nonfixture_and_invalid_image_hash_rejected(self):
        bad = deepcopy(self.whole)
        bad["execution_mode"] = "physical"
        with self.assertRaisesRegex(ValueError, "non-fixture"):
            assess_mission(bad)
        bad = deepcopy(self.whole)
        bad["photo_attempts"][0]["image_sha256"] = "not-a-sha"
        with self.assertRaisesRegex(ValueError, "64-character"):
            assess_mission(bad)

    def test_no_scope_leak_between_vehicle_and_component(self):
        bad = deepcopy(self.bumper)
        bad["shot_plan"]["required"][0]["part"] = "whole_vehicle"
        with self.assertRaisesRegex(ValueError, "another part"):
            assess_mission(bad)
        bad = deepcopy(self.whole)
        bad["part_grounding"] = self.bumper["part_grounding"]
        with self.assertRaisesRegex(ValueError, "unexpected part_grounding"):
            assess_mission(bad)

    def test_cli_rejects_duplicate_json_fields_and_nonfinite(self):
        from tempfile import TemporaryDirectory
        from contextlib import redirect_stderr
        from io import StringIO
        from unittest.mock import patch
        from scripts.assess_vehicle_mission import main
        with TemporaryDirectory() as temp:
            path = Path(temp) / "trace.json"
            for raw in ('{"schema_version":1,"schema_version":2}',
                        '{"schema_version": NaN}'):
                path.write_text(raw, encoding="utf-8")
                with patch("sys.argv", ["assess_vehicle_mission.py", str(path)]), redirect_stderr(StringIO()):
                    self.assertEqual(main(), 2)

    def test_nan_quality_rejected(self):
        bad = deepcopy(self.whole)
        bad["photo_attempts"][0]["independent_qc"]["glare_fraction"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite fraction"):
            assess_mission(bad)


if __name__ == "__main__":
    unittest.main()
