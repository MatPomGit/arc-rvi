"""View selection correctness and deterministic failure cases."""

import unittest

from rvi.models import Viewpoint
from rvi.viewpoints import PlanningError, plan_viewpoints


class ViewpointTests(unittest.TestCase):
    def setUp(self):
        self.views = [
            Viewpoint("first", 1.0, 0.0, ("front", "left")),
            Viewpoint("second", 3.0, 1.0, ("right", "rear")),
            Viewpoint("alternative", 9.0, 9.0, ("front",)),
        ]

    def test_covers_all_regions_in_deterministic_order(self):
        plan = plan_viewpoints(self.views, ["front", "rear", "left", "right"])
        self.assertEqual(plan.viewpoint_ids, ("first", "second"))
        self.assertEqual(plan.covered_regions, ("front", "left", "rear", "right"))
        self.assertGreater(plan.travel_distance_m, 0)

    def test_missing_coverage_fails(self):
        with self.assertRaises(PlanningError):
            plan_viewpoints(self.views, ["roof"])

    def test_duplicate_viewpoint_identifier_fails(self):
        with self.assertRaises(ValueError):
            plan_viewpoints([self.views[0], self.views[0]], ["front"])

    def test_duplicate_required_region_fails(self):
        with self.assertRaises(ValueError):
            plan_viewpoints(self.views, ["front", "front"])

    def test_nonfinite_coordinates_fail(self):
        with self.assertRaises(ValueError):
            Viewpoint("bad", float("nan"), 0.0, ("front",))

    def test_invalid_start_fails(self):
        with self.assertRaises(ValueError):
            plan_viewpoints(self.views, ["front"], (float("inf"), 0.0))


if __name__ == "__main__":
    unittest.main()
