"""Presentation graph checks: 3D anchors and explicit alternate branches."""
import copy
import json
import unittest

from tools.compile_jade_navigation_v5 import (MANIFEST, NEW_BRANCHES,
                                              compile_navigation,
                                              matching_walkway)


class NavigationV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_main_and_seven_alternates_in_one_reachable_graph(self):
        result = compile_navigation(self.manifest)
        self.assertEqual(result["summary"]["route_count"], 8)
        self.assertEqual(result["summary"]["alternate_count"], 7)
        self.assertEqual(result["summary"]["walkway_count"], 27)
        self.assertEqual(len(result["summary"]["new_supported_branches"]), 5)
        self.assertIn(result["goal"],
                      {e["to"] for e in result["edges"]})
        self.assertTrue(all(not node["collision_verified"]
                            for node in result["nodes"]))
        self.assertTrue(all(not edge["collision_verified"]
                            for edge in result["edges"]))
        self.assertGreater(result["summary"]["supported_edges"], 12)

    def test_branch_segments_touch_geometry_at_both_endpoints(self):
        data = self.manifest
        required = set(NEW_BRANCHES) | {"lower_islands"}
        for route in data["routes"]:
            if route["id"] not in required:
                continue
            for a, b in zip(route["points"], route["points"][1:]):
                support = matching_walkway(a, b, data["walkways"])
                self.assertIsNotNone(support, (route["id"],a,b))
                self.assertIn(support["kind"], {"rope","stairs","checker"})

    def test_forks_rejoin_main_forward_with_real_off_main_waypoint(self):
        main = self.manifest["routes"][0]["points"]
        for route in self.manifest["routes"]:
            if route["id"] not in NEW_BRANCHES:
                continue
            self.assertLess(main.index(route["points"][0]),
                            main.index(route["points"][-1]))
            self.assertTrue(any(p not in main for p in route["points"][1:-1]))

    def test_missing_high_or_mid_walkway_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["walkways"] = [
            w for w in bad["walkways"] if w["id"] != "sky_mid_checker_b"
        ]
        with self.assertRaisesRegex(ValueError, "unsupported"):
            compile_navigation(bad)

    def test_route_without_collision_flag_rejected(self):
        bad = copy.deepcopy(self.manifest)
        next(r for r in bad["routes"]
             if r["id"] == "village_north_decks").pop("visual_only")
        with self.assertRaisesRegex(ValueError, "collision readiness"):
            compile_navigation(bad)

    def test_missing_island_segment_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["walkways"] = [
            w for w in bad["walkways"] if w["id"] != "sky_lower_checker_bc"
        ]
        with self.assertRaisesRegex(ValueError, "unsupported"):
            compile_navigation(bad)


if __name__ == "__main__":
    unittest.main()
