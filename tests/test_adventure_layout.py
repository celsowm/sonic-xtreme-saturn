import copy
import json
import unittest
from pathlib import Path
from tools.validate_adventure_layout import DEFAULT,validate,ROOT

class AdventureLayoutTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(DEFAULT.read_text())

    def test_connected_branches_and_capacity(self):
        result=validate(self.data)
        self.assertEqual(result["routes"],4)
        self.assertEqual(result["path_segments"],22)
        self.assertEqual(result["props"],18)
        self.assertEqual(result["walkable_clearings"],2)
        self.assertEqual(result["face_budget_total"],511)
        self.assertEqual(result["landmass_triangles"],120)
        self.assertEqual(result["branch_terrace_triangles"],24)
        self.assertEqual(result["prop_triangle_budget"],232)
        self.assertEqual(result["near_render_tile_extra_triangles"],34)
        self.assertEqual(result["far_lod_triangles"],35)
        self.assertEqual(result["palm_lod_instances"],7)
        self.assertLessEqual(result["face_budget_total"],512)

    def test_overlook_has_real_curated_landmarks(self):
        props={p["id"]:p for p in self.data["set_dressing"]}
        for name in ("palm_overlook_left","palm_overlook_right","bush_overlook"):
            self.assertIn(name,props)
            self.assertGreaterEqual(props[name]["triangles_max"],7)
        self.assertGreaterEqual(sum(p["asset"].startswith("nature-kit/tree") for p in props.values()),7)

    def test_visual_tiling_budget_bounds(self):
        changed=copy.deepcopy(self.data)
        changed["visual_tiling"]["valley_prefix_segments"]=100
        with self.assertRaises(ValueError):
            validate(changed)
        changed=copy.deepcopy(self.data)
        changed["visual_tiling"]["valley_bands"].append("proprietary")
        with self.assertRaises(ValueError):
            validate(changed)
        changed=copy.deepcopy(self.data)
        changed["budgets"]["far_palm_lod_faces_per_instance"]=12
        with self.assertRaises(ValueError):
            validate(changed)

    def test_natural_prop_snap_validation(self):
        snap=[p for p in self.data["set_dressing"] if p.get("snap_to_valley")]
        self.assertEqual(len(snap),14)
        changed=copy.deepcopy(self.data)
        changed["set_dressing"][0]["snap_to_valley"]="yes"
        with self.assertRaises(ValueError):
            validate(changed)
        changed=copy.deepcopy(self.data)
        changed["set_dressing"][5]["snap_to_valley"]=True
        with self.assertRaises(ValueError):
            validate(changed)

    def test_branches_cannot_be_disconnected(self):
        changed=copy.deepcopy(self.data)
        changed["routes"][1]["stations"][0][0]=99
        with self.assertRaises(ValueError):
            validate(changed)

    def test_asset_path_is_local_and_registered(self):
        changed=copy.deepcopy(self.data)
        changed["set_dressing"][0]["asset"]="../../secret.glb"
        with self.assertRaises(ValueError):
            validate(changed)

    def test_model_budget_enforced(self):
        changed=copy.deepcopy(self.data)
        changed["set_dressing"][0]["triangles_max"]=25
        with self.assertRaises(ValueError):
            validate(changed)

    def test_spawn_goal_and_pacing_contract(self):
        changed=copy.deepcopy(self.data)
        changed["target_visual_fps"]=60
        with self.assertRaises(ValueError):
            validate(changed)
        changed=copy.deepcopy(self.data)
        changed["entities"]=[e for e in changed["entities"] if e["kind"]!="goal"]
        with self.assertRaises(ValueError):
            validate(changed)

if __name__=="__main__":
    unittest.main()
