import unittest
from tools.prop_materials import split_palm_faces
from tools.read_kenney_glb import read_glb_triangles
from tools.validate_adventure_layout import ROOT


class PalmPaletteTests(unittest.TestCase):
    def test_material_groups_preserve_source_triangles(self):
        faces=[(0,1,2),(3,4,5),(6,7,8)]
        wood,leaves=split_palm_faces(faces,[0,1,1],["woodBark","leafsGreen"])
        self.assertEqual(wood,[(0,1,2)])
        self.assertEqual(leaves,[(3,4,5),(6,7,8)])
        self.assertEqual(len(wood)+len(leaves),len(faces))

    def test_real_curated_kenney_glbs_have_both_materials(self):
        for name in ("tree-palm.glb","tree-palmbend.glb"):
            source=ROOT/"assets/kenney/nature-kit"/name
            verts,faces,ids,materials=read_glb_triangles(source,with_materials=True)
            wood,leaves=split_palm_faces(faces,ids,materials)
            self.assertTrue(verts)
            self.assertGreater(len(wood),3)
            self.assertGreater(len(leaves),3)

    def test_reject_invalid_materials(self):
        with self.assertRaises(ValueError):
            split_palm_faces([(0,1,2)],[2],["woodBark","leafsGreen"])
        with self.assertRaises(ValueError):
            split_palm_faces([(0,1,2),(3,4,5)],[0,0],["woodBark"])


if __name__=="__main__":
    unittest.main()
