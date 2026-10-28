import unittest

from rvi.mission import Mission, MissionState


class MissionTests(unittest.TestCase):
    def test_normal_cycle(self):
        mission = Mission(handoff_anchor_id="operator-1")
        for state in (MissionState.TARGET_CONFIRMED, MissionState.PLANNED,
                      MissionState.ACQUIRING, MissionState.QUALITY_CHECKED):
            mission.advance(state)
        mission.advance(MissionState.RETURNING, evidence={
            "all_required_slots_accepted": True, "independent_qc_complete": True})
        mission.advance(MissionState.RETURN_VERIFIED, evidence={
            "anchor_id": "operator-1", "status": "arrived", "safe_route_verified": True})
        mission.advance(MissionState.HANDOFF_CONFIRMED, evidence={
            "anchor_id": "operator-1", "operator_handoff_confirmed": True})
        mission.advance(MissionState.COMPLETE)
        self.assertEqual(mission.state, MissionState.COMPLETE)

    def test_completion_requires_quality_return_and_handoff(self):
        mission = Mission(handoff_anchor_id="operator-1")
        for state in (MissionState.TARGET_CONFIRMED, MissionState.PLANNED,
                      MissionState.ACQUIRING, MissionState.QUALITY_CHECKED):
            mission.advance(state)
        with self.assertRaises(ValueError):
            mission.advance(MissionState.COMPLETE)
        with self.assertRaises(ValueError):
            mission.advance(MissionState.RETURNING)
        with self.assertRaises(ValueError):
            mission.advance(MissionState.RETURNING, evidence={
                "all_required_slots_accepted": True, "independent_qc_complete": False})
        mission.advance(MissionState.RETURNING, evidence={
            "all_required_slots_accepted": True, "independent_qc_complete": True})
        with self.assertRaises(ValueError):
            mission.advance(MissionState.RETURN_VERIFIED, evidence={
                "anchor_id": "wrong-operator", "status": "arrived", "safe_route_verified": True})
        mission.advance(MissionState.RETURN_VERIFIED, evidence={
            "anchor_id": "operator-1", "status": "arrived", "safe_route_verified": True})
        with self.assertRaises(ValueError):
            mission.advance(MissionState.HANDOFF_CONFIRMED, evidence={
                "anchor_id": "operator-1", "operator_handoff_confirmed": False})
        self.assertEqual(mission.state, MissionState.RETURN_VERIFIED)

    def test_quality_retry_is_supported(self):
        mission = Mission(MissionState.QUALITY_CHECKED)
        mission.advance(MissionState.ACQUIRING)
        self.assertEqual(mission.state, MissionState.ACQUIRING)

    def test_invalid_transition_fails(self):
        with self.assertRaises(ValueError):
            Mission().advance(MissionState.COMPLETE)

    def test_aborted_is_terminal(self):
        mission = Mission()
        mission.advance(MissionState.ABORTED)
        with self.assertRaises(ValueError):
            mission.advance(MissionState.CREATED)


if __name__ == "__main__":
    unittest.main()
