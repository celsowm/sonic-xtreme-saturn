"""Presentation graph checks: 3D anchors and explicit alternate branches."""
import copy
import json
import math
import unittest

from tools.compile_jade_navigation_v5 import (MANIFEST, NEW_BRANCHES,
                                              compile_navigation,
                                              matching_walkway, matching_transfer)


class NavigationV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_main_and_ten_alternates_in_one_reachable_graph(self):
        result = compile_navigation(self.manifest)
        self.assertEqual(result["summary"]["route_count"], 11)
        self.assertEqual(result["summary"]["alternate_count"], 10)
        self.assertEqual(result["summary"]["walkway_count"], 20)
        self.assertEqual(result["summary"]["aerial_transfer_definitions"], 26)
        self.assertEqual(result["summary"]["canyon_landing_platforms"], 11)
        self.assertEqual(result["summary"]["lower_canyon_branches"], 3)
        self.assertEqual(result["summary"]["cloud_landing_platforms"], 6)
        self.assertGreaterEqual(result["summary"]["long_unverified_drop_edges"], 1)
        self.assertEqual(result["summary"]["aerial_transfer_edges"], 26)
        self.assertEqual(len(result["summary"]["new_supported_branches"]), 8)
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
                elif route["id"] in ("sky_high_e", "sky_middle_d", "lower_islands"):
                    self.assertIsNotNone(transfer)
                    self.assertIn(transfer["mode"], {"spring","drop","jump"})
                    self.assertFalse(transfer["physics_verified"])
                else:
                    # Canyon and lower-Hex routes mix short structural
                    # walkways with named one-way aerial transitions.
                    if support is not None:
                        self.assertIn(support["kind"], {"plank", "stairs"})
                    else:
                        self.assertIn(transfer["mode"], {"jump", "spring", "drop"})

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

    def test_lower_hex_and_canyon_routes_rejoin_main_with_every_edge_supported(self):
        compiled = compile_navigation(self.manifest)
        for name in ("hex_lower_underpass", "canyon_mid_stairs", "canyon_lower_docks"):
            edges = [edge for edge in compiled["edges"] if edge["route"] == name]
            self.assertGreaterEqual(len(edges), 3)
            self.assertTrue(all((edge["walkway_id"] is not None) !=
                                (edge["transfer_id"] is not None) for edge in edges))
            self.assertTrue(all(not edge["physics_verified"] and
                                not edge["collision_verified"] for edge in edges))
        ids = {e["walkway_id"] for e in compiled["edges"] if e["walkway_id"]}
        self.assertTrue({"canyon_dock_walk", "canyon_dock_a", "canyon_dock_b",
                         "canyon_stairs_mid", "canyon_mid_stairs_exit"} <= ids)

    def test_canyon_dock_landings_are_named_and_not_floating_route_lines(self):
        pads = {p["id"]: p for p in self.manifest["canyon_route_landings"]}
        self.assertEqual(len(pads), 11)
        self.assertEqual(sum(p["material"] == "wood" for p in pads.values()), 4)
        for pad in pads.values():
            self.assertFalse(pad["collision_verified"])
            self.assertGreaterEqual(pad["radius"], 5)
        arrival_ids = {t["landing"] for t in self.manifest["navigation_transfers"]}
        self.assertTrue({"hex_lower_step_a", "hex_lower_step_b",
                         "hex_lower_step_d", "canyon_low_dock_south",
                         "canyon_middle_stair_start", "canyon_middle_step"} <= arrival_ids)

    def test_canyon_jump_needs_actual_named_landing_pad(self):
        bad = copy.deepcopy(self.manifest)
        bad["canyon_route_landings"] = [
            x for x in bad["canyon_route_landings"] if x["id"] != "canyon_low_dock_north"]
        with self.assertRaisesRegex(ValueError, "no named solid landing"):
            compile_navigation(bad)
        bad = copy.deepcopy(self.manifest)
        pad = next(p for p in bad["canyon_route_landings"]
                   if p["id"] == "hex_lower_step_a")
        pad["center"][0] += 8
        with self.assertRaisesRegex(ValueError, "misses its landing canyon"):
            compile_navigation(bad)

    def test_canyon_mid_graph_follows_all_three_hairpin_flights(self):
        route = next(r for r in self.manifest["routes"]
                     if r["id"] == "canyon_mid_stairs")
        stairs = next(w for w in self.manifest["walkways"]
                      if w["id"] == "canyon_stairs_mid")
        self.assertEqual(len(route["points"]), 6)
        via = stairs["via"]
        self.assertEqual(route["points"][2:4],
                         [[x,y,z+.6] for x,y,z in via])
        stair_edges = [(a,b) for a,b in zip(route["points"],route["points"][1:])
                       if matching_walkway(a,b,[stairs]) is not None]
        self.assertEqual(len(stair_edges), 3)
        for a,b in stair_edges:
            planar=((a[0]-b[0])**2+(a[1]-b[1])**2)**.5
            deg=math.degrees(math.atan2(abs(b[2]-a[2]),planar))
            self.assertLessEqual(deg,32)
        nav=compile_navigation(self.manifest)
        stair_ids=[x["walkway_id"] for x in nav["edges"]
                   if x["route"]=="canyon_mid_stairs"]
        self.assertEqual(stair_ids.count("canyon_stairs_mid"),3)

    def test_canyon_graph_rejects_shortcut_through_switchback_landing(self):
        bad=copy.deepcopy(self.manifest)
        w=next(w for w in bad["walkways"] if w["id"]=="canyon_stairs_mid")
        w["via"]=[]
        with self.assertRaisesRegex(ValueError,"unsupported segment"):
            compile_navigation(bad)

    def test_gold_main_route_follows_both_upper_rock_switchbacks(self):
        # Main previously jumped diagonally past the high and goal
        # stairs even though the Blender meshes had proper hairpins.
        nav = compile_navigation(self.manifest)
        main_edges = [e for e in nav["edges"] if e["route"] == "main"]
        self.assertEqual(len(self.manifest["routes"][0]["points"]), 40)
        for stair_name in ("canyon_stairs_high", "canyon_stairs_goal"):
            legs = [e for e in main_edges if e["walkway_id"] == stair_name]
            self.assertEqual(len(legs), 3, stair_name)
            self.assertTrue(all(e["mode"] == "stairs" for e in legs))
            self.assertTrue(all(not e["collision_verified"] for e in legs))

    def test_gold_main_route_cannot_cut_switchback_corner(self):
        bad = copy.deepcopy(self.manifest)
        stair = next(w for w in bad["walkways"]
                     if w["id"] == "canyon_stairs_high")
        point = [x if i < 2 else x+.6 for i,x in enumerate(stair["via"][0])]
        bad["routes"][0]["points"].remove(point)
        with self.assertRaisesRegex(ValueError, "bypasses physical canyon switchback"):
            compile_navigation(bad)

    def test_mid_stair_branch_rejects_missing_exit_plank(self):
        bad = copy.deepcopy(self.manifest)
        bad["walkways"] = [
            w for w in bad["walkways"] if w["id"] != "canyon_mid_stairs_exit"
        ]
        with self.assertRaisesRegex(ValueError, "unsupported segment"):
            compile_navigation(bad)

    def test_no_fabricated_walkways_over_lower_cloud_islands(self):
        self.assertFalse(any(w["id"].startswith("sky_lower_")
                             or w["id"].startswith("sky_high_")
                             or w["id"].startswith("sky_mid_")
                             for w in self.manifest["walkways"]))
        self.assertEqual(len(self.manifest["navigation_transfers"]), 26)


if __name__ == "__main__":
    unittest.main()
