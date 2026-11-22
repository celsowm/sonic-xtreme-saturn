"""Pure source-geometry tests for the photographed v3 landmark pass.

Blender tests are executed by the concept workflow, while these checks run
without bpy to catch broken math and accidental loss of source contracts.
"""
import math
import unittest

from tools.jade_concept_presentation import hex_outline_points


class JadeConceptPresentationTests(unittest.TestCase):
    def test_six_sided_outline_is_closed_and_looks_at_positive_x_camera(self):
        pts = hex_outline_points(16,155,80,30,8.8)
        self.assertEqual(len(pts),7)
        self.assertEqual(pts[0],pts[-1])
        self.assertTrue(all(abs(p[0]-24.8)<1e-10 for p in pts))
        self.assertEqual(len({(round(p[1],5),round(p[2],5))
                              for p in pts[:-1]}),6)
        self.assertAlmostEqual(math.dist(pts[0],(24.8,155,80)),30)

    def test_nested_inner_outline_is_smaller(self):
        outer=hex_outline_points(0,0,0,30)
        inner=hex_outline_points(0,0,0,21)
        self.assertAlmostEqual(math.dist(outer[0],(0,0,0)),30)
        self.assertAlmostEqual(math.dist(inner[0],(0,0,0)),21)

    def test_invalid_radius_fails_fast(self):
        for radius in (0,-.2):
            with self.assertRaises(ValueError):
                hex_outline_points(0,0,0,radius)


if __name__ == "__main__":
    unittest.main()
