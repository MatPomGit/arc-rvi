import json
from pathlib import Path
import tempfile
import unittest

from rvi.cli import main


ROOT = Path(__file__).resolve().parents[2]


class CliTests(unittest.TestCase):
    def test_synthetic_plan_output(self):
        scenario = ROOT / "simulation" / "scenarios" / "inspection_small.json"
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "nested" / "plan.json"
            self.assertEqual(main(["plan", "--scenario", str(scenario), "--output", str(output)]), 0)
            plan = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(plan["evidence_type"], "synthetic_fixture")
            self.assertEqual(set(plan["covered_regions"]), {"front", "left", "right", "rear"})
            self.assertEqual(plan["viewpoint_ids"], ["v_front_left", "v_rear_right"])
            self.assertGreater(plan["travel_distance_m"], 0)


if __name__ == "__main__":
    unittest.main()
