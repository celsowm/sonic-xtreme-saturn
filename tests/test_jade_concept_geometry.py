"""Pure-Python regression tests for scenic geometry; no Blender required."""
import unittest
from tools.jade_concept_geometry import mesa_mesh, ribbon_mesh, halfpipe_mesh


class ScenicGeometryTests(unittest.TestCase):
    def assert_indexed_mesh(self, vertices, faces):
        self.assertTrue(vertices)
        self.assertTrue(faces)
        for polygon in faces:
            self.assertGreaterEqual(len(polygon), 3)
            self.assertTrue(all(0 <= index < len(vertices) for index in polygon))
            self.assertEqual(len(polygon), len(set(polygon)))

    def test_checker_mesa_has_cap_and_two_tone_cliff_tiers(self):
        vertices, faces, materials = mesa_mesh(-50, 120, 12, 19, 23)
        self.assertEqual(len(vertices), 32)
        self.assertEqual(len(faces), 17)
        self.assertEqual(len(materials), len(faces))
        self.assertEqual(materials[0], 0)
        self.assertTrue({1, 2}.issubset(set(materials)))
        self.assert_indexed_mesh(vertices, faces)

    def test_broad_river_is_continuous(self):
        source = [(0, 0, 3), (2, 12, 3), (5, 21, 4)]
        vertices, faces = ribbon_mesh(source, 5)
        self.assertEqual(len(vertices), 6)
        self.assertEqual(len(faces), 2)
        self.assert_indexed_mesh(vertices, faces)
        self.assertEqual((vertices[-1][2], vertices[0][2]), (4, 3))

    def test_halfpipe_has_u_section_and_thickness(self):
        vertices, faces, materials = halfpipe_mesh((0,0,4),(0,35,12),6)
        self.assertEqual(len(vertices), 15*8)
        self.assertEqual(len(faces), 14*7)
        self.assertEqual(len(materials), len(faces))
        self.assertAlmostEqual(vertices[0][2], 10)
        self.assertAlmostEqual(vertices[3][2], 4+6*(1-__import__('math').cos(-__import__('math').pi/2+3*__import__('math').pi/7)))
        self.assert_indexed_mesh(vertices, faces)

    def test_reject_invalid_geometry(self):
        with self.assertRaises(ValueError):
            mesa_mesh(0,0,0,0,10)
        with self.assertRaises(ValueError):
            ribbon_mesh([(0,0,0)], 2)
        with self.assertRaises(ValueError):
            halfpipe_mesh((0,0,0),(0,1,0),0)


if __name__ == '__main__':
    unittest.main()
