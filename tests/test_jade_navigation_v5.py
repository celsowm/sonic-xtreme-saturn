"""Presentation graph checks: 3D anchors and explicit alternate branches."""
import copy
import json
import unittest

from tools.compile_jade_navigation_v5 import (MANIFEST, NEW_BRANCHES,
                                              compile_navigation,
                                              matching_walkway, matching_transfer)


class NavigationV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_main_and_seven_alternates_in_one_reachable_graph(self):
        result = compile_navigation(self.manifest)
        self.assertEqual(result["summary"]["route_count"], 8)
        self.assertEqual(result["summary"]["alternate_count"], 7)
        self.assertEqual(result["summary"]["walkway_count"], 19)
        self.assertEqual(result["summary"]["aerial_transfer_definitions"], 15)
        self.assertEqual(result["summary"]["cloud_landing_platforms"], 6)
        self.assertGreaterEqual(result["summary"]["long_unverified_drop_edges"], 1)
        self.assertEqual(result["summary"]["aerial_transfer_edges"], 15)
        self.assertEqual(len(result["summary"]["new_supported_branches"]), 5)
        self.assertIn(result["goal"],
                      {e["to"] for e in result["edges"]})
        self.assertTrue(all(not node["collision_verified"]
                            for node in result["nodes"]))
        self.assertTrue(all(not edge["collision_verified"]
                            for edge in result["edges"]))
        self.assertGreaterEqual(result["summary"]["supported_edges"], 7)
        self.assertTrue(all(not edge["physics_verified"]
                            for edge in result["edges"]))

    def test_branch_edges_are_either_landed_decks_or_explicit_aerial_transfers(self):
        data = self.manifest
        required = set(NEW_BRANCHES) | {"lower_islands"}
        for route in data["routes"]:
            if route["id"] not in required:
                continue
            for a, b in zip(route["points"], route["points"][1:]):
                support = matching_walkway(a, b, data["walkways"])
                transfer = matching_transfer(a, b, route["id"],
                                             data["navigation_transfers"])
                self.assertNotEqual(support is None, transfer is None,
                                    (route["id"], a, b))
                if route["id"].startswith("village_"):
                    self.assertIsNotNone(support)
                    self.assertIn(support["kind"], {"rope","stairs"})
                else:
                    self.assertIsNotNone(transfer)
                    self.assertIn(transfer["mode"], {"spring","drop","jump"})
                    self.assertFalse(transfer["physics_verified"])

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
            w for w in bad["walkways"] if w["id"] != "village_trunk_ramp_b"
        ]
        with self.assertRaisesRegex(ValueError, "unsupported"):
            compile_navigation(bad)

    def test_route_without_collision_flag_rejected(self):
        bad = copy.deepcopy(self.manifest)
        next(r for r in bad["routes"]
             if r["id"] == "village_north_decks").pop("visual_only")
        with self.assertRaisesRegex(ValueError, "collision readiness"):
            compile_navigation(bad)

    def test_missing_aerial_transfer_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["navigation_transfers"] = [
            t for t in bad["navigation_transfers"] if t["id"] != "low_b_cloud_east_spring"
        ]
        with self.assertRaisesRegex(ValueError, "unsupported"):
            compile_navigation(bad)

    def test_unlanded_aerial_transfer_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["navigation_transfers"][0]["landing"] = "sky_b"
        with self.assertRaisesRegex(ValueError, "misses its landing"):
            compile_navigation(bad)

    def test_aerial_transfer_never_claims_physics_is_ready(self):
        bad = copy.deepcopy(self.manifest)
        bad["navigation_transfers"][0]["physics_verified"] = True
        with self.assertRaisesRegex(ValueError, "tested physics"):
            compile_navigation(bad)

    def test_six_cloud_landing_pads_reduce_long_aerial_leaps(self):
        stages = {item["id"]: item for item in self.manifest["sky_cloud_landings"]}
        self.assertEqual(len(stages), 6)
        self.assertEqual({x["tier"] for x in stages.values()}, {"high","middle","low"})
        arrivals = [t for t in self.manifest["navigation_transfers"] if t["landing"] in stages]
        self.assertEqual(len(arrivals), 6)
        for t in arrivals:
            self.assertEqual(t["to"][:2], stages[t["landing"]]["center"][:2])
            self.assertAlmostEqual(t["to"][2], stages[t["landing"]]["center"][2]+.6)
        for t in self.manifest["navigation_transfers"]:
            if t["mode"] != "drop":
                planar = ((t["to"][0]-t["from"][0])**2 +
                          (t["to"][1]-t["from"][1])**2)**.5
                self.assertLessEqual(planar, 34)

    def test_cloud_landings_must_exist_and_have_sufficient_surface(self):
        bad = copy.deepcopy(self.manifest)
        bad["sky_cloud_landings"][0]["radius"] = 1.0
        with self.assertRaisesRegex(ValueError, "visible platform radius"):
            compile_navigation(bad)
        bad = copy.deepcopy(self.manifest)
        bad["sky_cloud_landings"][0]["center"][2] = 99
        with self.assertRaisesRegex(ValueError, "misses its landing cloud"):
            compile_navigation(bad)

    def test_new_sky_routes_have_multiple_distinct_arrival_patches(self):
        for name, needed in (("sky_high_e", 4), ("sky_middle_d", 5),
                             ("lower_islands", 9)):
            points = next(r["points"] for r in self.manifest["routes"] if r["id"] == name)
            self.assertEqual(len(points), needed)
        used_stages = {t["landing"] for t in self.manifest["navigation_transfers"]}
        self.assertEqual({p["id"] for p in self.manifest["sky_cloud_landings"]}, (
            used_stages & {p["id"] for p in self.manifest["sky_cloud_landings"]}))

    def test_no_fabricated_walkways_over_lower_cloud_islands(self):
        self.assertFalse(any(w["id"].startswith("sky_lower_")
                             or w["id"].startswith("sky_high_")
                             or w["id"].startswith("sky_mid_")
                             for w in self.manifest["walkways"]))
        self.assertEqual(len(self.manifest["navigation_transfers"]), 15)


if __name__ == "__main__":
    unittest.main()
