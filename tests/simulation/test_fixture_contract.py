import json
from pathlib import Path
import unittest

from rvi.models import Viewpoint
from rvi.viewpoints import plan_viewpoints


ROOT = Path(__file__).resolve().parents[2]


class FixtureContractTests(unittest.TestCase):
    def test_fixture_is_not_labeled_as_physical(self):
        path = ROOT / "simulation" / "scenarios" / "inspection_small.json"
        fixture = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(fixture["evidence_type"], "synthetic_fixture")
        self.assertEqual(len(fixture["viewpoints"]), 5)
        views = [
            Viewpoint(v["id"], v["x"], v["y"], tuple(v["regions"]))
            for v in fixture["viewpoints"]
        ]
        plan = plan_viewpoints(views, fixture["required_regions"], tuple(fixture["start_xy"]))
        self.assertEqual(set(plan.covered_regions), set(fixture["required_regions"]))


if __name__ == "__main__":
    unittest.main()
