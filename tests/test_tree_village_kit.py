"""Host-only tests of the Tree Village Blender manifest (no bpy required)."""
import copy
import json
import unittest
from tools.validate_tree_village_kit import DEFAULT, validate


class TreeVillageKitTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def test_complete_hybrid_kit(self):
        result = validate(self.data)
        self.assertEqual(result["objects"], 28)
        self.assertEqual(result["entities"], 7)
        self.assertEqual(result["routes"], 2)
        self.assertEqual(result["kinds"]["palm_x"], 5)
        self.assertEqual(result["kinds"]["facade"], 5)
        self.assertEqual(result["kinds"]["spring"], 1)
        self.assertEqual(result["runtime_status"], "blender_authoring_only")

    def test_no_authoring_claims_of_runtime_features(self):
        for key in ("spring", "stream", "billboard", "fade"):
            self.assertNotIn(key+"_runtime_active", self.data)
        self.assertEqual(self.data["routes"][1]["mode"], "spring_launch_required")

    def test_missing_or_unreachable_route_fails(self):
        bad = copy.deepcopy(self.data)
        bad["routes"][1]["waypoints"][0] = [-11, 39, 4]
        with self.assertRaisesRegex(ValueError, "branch and rejoin"):
            validate(bad)
        bad = copy.deepcopy(self.data)
        bad["routes"][0]["parts"].append("missing_bridge")
        with self.assertRaisesRegex(ValueError, "nonexistent"):
            validate(bad)

    def test_nocollision_on_visual_fakes(self):
        for name in ("palm_x_01", "house_facade_01", "foliage_x_01"):
            bad = copy.deepcopy(self.data)
            next(o for o in bad["objects"] if o["id"] == name)["role"] = "walkable"
            with self.assertRaisesRegex(ValueError, "fake scenery"):
                validate(bad)

    def test_no_out_of_bounds_models(self):
        bad = copy.deepcopy(self.data)
        bad["objects"][0]["center"][1] = 270
        with self.assertRaisesRegex(ValueError, "outside bounds"):
            validate(bad)

    def test_false_spring_gameplay_claim_fails(self):
        bad = copy.deepcopy(self.data)
        next(o for o in bad["objects"] if o["kind"] == "spring")["role"] = "walkable"
        with self.assertRaisesRegex(ValueError, "spring has no active"):
            validate(bad)

    def test_capacity_cannot_be_silently_enlarged(self):
        bad = copy.deepcopy(self.data)
        bad["scene_limits"]["render_faces_max"] = 1024
        with self.assertRaisesRegex(ValueError, "ceilings"):
            validate(bad)

    def test_visual_decorations_do_not_require_collision(self):
        self.assertTrue(all(o["role"]=="decoration" for o in self.data["objects"]
                            if o["kind"] in ("palm_x","foliage_x","facade")))
        self.assertTrue(all(o["role"]=="walkable" for o in self.data["objects"]
                            if o["kind"] in ("ground","bridge","platform")))


if __name__ == "__main__":
    unittest.main()
