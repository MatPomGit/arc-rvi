import unittest

from rvi.mission import Mission, MissionState


class MissionTests(unittest.TestCase):
    def test_normal_cycle(self):
        mission = Mission()
        for state in (
            MissionState.TARGET_CONFIRMED,
            MissionState.PLANNED,
            MissionState.ACQUIRING,
            MissionState.QUALITY_CHECKED,
            MissionState.COMPLETE,
        ):
            mission.advance(state)
        self.assertEqual(mission.state, MissionState.COMPLETE)

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
