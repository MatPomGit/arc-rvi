"""Conservative synthetic reflection-aware viewpoint candidate tests."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from rvi.photometric_view import select_view

PATH = Path(__file__).resolve().parents[1] / "simulation/suites/vehicle_glare_viewpoint_fixture.json"


class PhotometricViewTest(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(PATH.read_text(encoding="utf-8"))

    def test_safe_lower_glare_view_selected_with_return_reserve(self):
        r = select_view(self.spec)
        self.assertEqual(r["status"], "candidate_selected")
        self.assertEqual(r["selected_pose_id"], "offset_lower_glare")
        self.assertFalse(r["certifies_robot_safety"])
        self.assertEqual(r["evidence_class"], "software_fixture_only")
        codes = {d["pose_id"]: d["reason_codes"] for d in r["candidate_diagnostics"]}
        self.assertIn("predicted_specular_glare", codes["front_direct_reflection"])
        self.assertIn("support_proxy_reject", codes["dangerous_kerb_edge"])
        self.assertIn("return_time_budget_exceeded", codes["too_far_to_return"])

    def test_no_safe_alternate_yields_abstention_not_unsafe_motion(self):
        s = deepcopy(self.spec)
        s["candidates"] = [s["candidates"][0], s["candidates"][2], s["candidates"][3]]
        r = select_view(s)
        self.assertEqual(r["status"], "no_feasible_candidate")
        self.assertIsNone(r["selected_pose_id"])

    def test_no_hidden_extension_of_deadline(self):
        s = deepcopy(self.spec)
        s["remaining_time_s"] = 50
        r = select_view(s)
        self.assertIsNone(r["selected_pose_id"])

    def test_tie_break_is_deterministic(self):
        s = deepcopy(self.spec)
        s["candidates"] = [deepcopy(s["candidates"][1]), deepcopy(s["candidates"][1])]
        s["candidates"][0]["pose_id"] = "z"
        s["candidates"][1]["pose_id"] = "a"
        self.assertEqual(select_view(s)["selected_pose_id"], "a")
        s["candidates"].reverse()
        self.assertEqual(select_view(s)["selected_pose_id"], "a")

    def test_false_feasibility_flag_is_rejected(self):
        s = deepcopy(self.spec)
        s["candidates"][1]["collision_proxy_ok"] = False
        r = select_view(s)
        self.assertEqual(r["status"], "no_feasible_candidate")
        self.assertIn("collision_proxy_reject", r["candidate_diagnostics"][1]["reason_codes"])

    def test_nan_probability_and_unscored_pose_fail_closed(self):
        s = deepcopy(self.spec)
        s["candidates"][1]["predicted_glare_fraction"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            select_view(s)
        s = deepcopy(self.spec)
        del s["candidates"][1]["predicted_glare_fraction"]
        with self.assertRaisesRegex(ValueError, "finite"):
            select_view(s)

    def test_duplicate_pose_cannot_weight_vote(self):
        s = deepcopy(self.spec)
        s["candidates"][1]["pose_id"] = s["candidates"][0]["pose_id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            select_view(s)

    def test_refuses_nonfixture_execution(self):
        s = deepcopy(self.spec)
        s["execution_mode"] = "physical_robot"
        with self.assertRaisesRegex(ValueError, "fixture_only"):
            select_view(s)

    def test_impossible_return_buffer_rejected(self):
        s = deepcopy(self.spec)
        s["return_buffer_s"] = 200
        with self.assertRaisesRegex(ValueError, "return buffer"):
            select_view(s)


if __name__ == "__main__":
    unittest.main()
