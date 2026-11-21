import unittest
from tools.prop_materials import split_palm_faces


class PalmPaletteTests(unittest.TestCase):
    def test_two_tone_faces_preserve_budget(self):
        v=[(0,0,0),(1,0,0),(0,1,0),
           (0,0,5),(1,0,5),(0,1,5)]
        faces=[(0,1,2),(3,4,5)]
        wood,leaves=split_palm_faces(v,faces,0,6)
        self.assertEqual(wood,[(0,1,2)])
        self.assertEqual(leaves,[(3,4,5)])
        self.assertEqual(len(wood)+len(leaves),len(faces))

    def test_reject_invalid_mesh(self):
        with self.assertRaises(ValueError):
            split_palm_faces([(0,0,0)],[(0,1,2)],0,3)
        with self.assertRaises(ValueError):
            split_palm_faces([(0,0,0)],[(0,0,0)],0,0)


if __name__=="__main__":
    unittest.main()
