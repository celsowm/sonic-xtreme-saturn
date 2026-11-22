"""Static CI sanity checks for Blender-only generator (bpy is imported on Mac)."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tools/create_tree_village_kit.py"
SCRIPT=ROOT/"scripts/build-tree-village-mac.sh"


class TreeVillageGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=SOURCE.read_text(encoding="utf-8")
        cls.shell=SCRIPT.read_text(encoding="utf-8")

    def test_blender_generator_python_syntax(self):
        ast.parse(self.source,filename=str(SOURCE))

    def test_geometry_has_separate_walkable_valley_and_house_supports(self):
        tree=ast.parse(self.source)
        funcs={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
        self.assertTrue({"valley_landmass","hut_supports","trunk","facade","cross_planes"}<=funcs)
        self.assertIn('valley_landmass()\n',self.source)
        self.assertIn('hut_supports()\n',self.source)
        self.assertIn('"JG_COLLISION","walkable",collision=True',self.source)

    def test_house_and_canopy_textures_are_alpha_cutouts(self):
        for token in ('"facade": create_image(', '"canopy": create_image(',
                      '"meadow": create_image(',
                      'name in ("palm","facade","canopy")'):
            self.assertIn(token,self.source)
        self.assertIn('"facade",item["collection"]',self.source)

    def test_mac_publisher_expects_ten_textures(self):
        self.assertIn('assert len(pngs) == 10',self.shell)
        self.assertIn('git -C "$ROOT" pull --ff-only',self.shell)
        self.assertIn('git -C "$ROOT" worktree add --detach "$TMP" origin/main',self.shell)


if __name__=="__main__":
    unittest.main()
