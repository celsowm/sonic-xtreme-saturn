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
        self.assertEqual(result["props"],10)
        self.assertEqual(result["face_budget_total"],212)
        self.assertLessEqual(result["face_budget_total"],256)

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
        changed["set_dressing"][0]["triangles_max"]=20
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
