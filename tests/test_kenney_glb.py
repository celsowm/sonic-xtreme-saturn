"""Host tests for tracked Kenney CC0 GLBs without bpy/numpy."""
import struct
import unittest
from pathlib import Path
from tools.read_kenney_glb import read_glb_triangles,read_accessor,open_glb,node_matrix

ROOT=Path(__file__).resolve().parents[1]/"assets/kenney"
FILES=[
    "nature-kit/tree-palm.glb",
    "nature-kit/tree-palmbend.glb",
    "nature-kit/rock-largea.glb",
    "nature-kit/cliff-waterfall-rock.glb",
    "nature-kit/plant-bush.glb",
    "nature-kit/bridge-wood.glb",
    "nature-kit/platform-grass.glb",
    "castle-kit/wall-pillar.glb",
    "castle-kit/wall-doorway.glb",
]

class KenneyGLBTests(unittest.TestCase):
    def test_nine_source_assets_are_valid_geometry(self):
        for asset in FILES:
            with self.subTest(asset=asset):
                vertices,faces=read_glb_triangles(ROOT/asset)
                self.assertGreater(len(vertices),3)
                self.assertGreater(len(faces),1)
                self.assertTrue(all(min(t)>=0 and max(t)<len(vertices) for t in faces))

    def test_palm_has_two_triangle_primitives(self):
        vertices,faces=read_glb_triangles(ROOT/"nature-kit/tree-palm.glb")
        self.assertEqual(len(vertices),592)
        self.assertEqual(len(faces),186)
        self.assertGreater(max(p[2] for p in vertices)-min(p[2] for p in vertices),0.1)

    def test_rigless_castle_prop(self):
        obj,raw=open_glb(ROOT/"castle-kit/wall-doorway.glb")
        self.assertEqual(obj["asset"]["version"],"2.0")
        vertices,faces=read_glb_triangles(ROOT/"castle-kit/wall-doorway.glb")
        self.assertEqual(len(faces),500)
        self.assertEqual(len(vertices),684)

    def test_header_and_transform_rejection(self):
        with self.assertRaises(ValueError):
            node_matrix({"matrix":[0]})
        self.assertEqual(node_matrix({"translation":[2,3,4]})[0][3],2)

if __name__=="__main__":
    unittest.main()
