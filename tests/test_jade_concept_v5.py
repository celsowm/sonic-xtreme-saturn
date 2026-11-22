"""Deterministic checks for the V5 visual landmass shape (no Blender)."""
import math
import unittest

from tools.jade_concept_v4_geometry import (
    organic_footprint, polygon_area, stratified_plateau,
)


class OrganicTerrainTests(unittest.TestCase):
    def test_outline_is_ccw_bounded_irregular_and_reproducible(self):
        a = organic_footprint(11, 5, 80, 52, seed=731)
        b = organic_footprint(11, 5, 80, 52, seed=731)
        c = organic_footprint(11, 5, 80, 52, seed=732)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(len(a), 28)
        self.assertGreater(polygon_area(a), 0)
        self.assertTrue(all(-29 <= x <= 51 and -21 <= y <= 31 for x, y in a))
        self.assertGreater(len({round(math.hypot(x - 11, y - 5), 3)
                                for x, y in a}), 10)

    def test_stratified_plateau_tapers_instead_of_vertical_wall(self):
        outline = organic_footprint(0, 0, 60, 40, seed=123)
        vertices, faces, materials = stratified_plateau(outline, 26, -62)
        n = len(outline)
        self.assertEqual(len(vertices), 4 * n)
        self.assertEqual(len(faces), 2 + 3 * n)
        self.assertEqual(len(materials), len(faces))
        self.assertEqual(set(materials), {0, 1, 2})
        self.assertEqual({v[2] for v in vertices}, {26, 24.6, 9.0, -62})
        for ring in range(4):
            self.assertEqual(len({v[2] for v in vertices[ring*n:(ring+1)*n]}), 1)
        def radius(index):
            return sum(math.hypot(x, y) for x, y, _ in vertices[index*n:(index+1)*n]) / n
        self.assertGreater(radius(1), radius(0))
        self.assertLess(radius(2), radius(0))
        self.assertLess(radius(3), radius(2))
        for face in faces:
            self.assertTrue(all(0 <= v < len(vertices) for v in face))

    def test_top_and_bottom_face_normals(self):
        outline = organic_footprint(0, 0, 60, 40, seed=42)
        vertices, faces, _ = stratified_plateau(outline, 10, -40)
        def normal_z(face):
            a, b, c = (vertices[i] for i in face[:3])
            u = tuple(b[k] - a[k] for k in range(3))
            v = tuple(c[k] - a[k] for k in range(3))
            return u[0]*v[1] - u[1]*v[0]
        self.assertGreater(normal_z(faces[0]), 0)
        self.assertLess(normal_z(faces[1]), 0)

    def test_invalid_outlines_and_strata_rejected(self):
        with self.assertRaises(ValueError):
            organic_footprint(0, 0, 0, 10)
        with self.assertRaises(ValueError):
            organic_footprint(0, 0, 10, 10, segments=5)
        with self.assertRaises(ValueError):
            organic_footprint(0, 0, 10, 10, roughness=.5)
        with self.assertRaises(ValueError):
            stratified_plateau([(0,0),(1,0),(1,1)], 10, -10)
        with self.assertRaises(ValueError):
            stratified_plateau(organic_footprint(0, 0, 10, 10), 1, 0)


if __name__ == '__main__':
    unittest.main()
