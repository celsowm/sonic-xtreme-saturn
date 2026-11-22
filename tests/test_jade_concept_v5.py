"""Deterministic checks for the V5 visual landmass shape (no Blender)."""
import math
import unittest

from tools.jade_concept_v4_geometry import (
    bridge_deck, canyon_rim_wall, organic_footprint, polygon_area, stratified_plateau,
    village_branch_paths,
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


    def test_hex_entry_and_exit_decks_have_real_connected_surface(self):
        stations = [(0, 0, 12), (0, 15, 13.5), (7, 26, 16)]
        vertices, faces, materials = bridge_deck(stations, 8, 3)
        self.assertEqual(len(vertices), 12)
        self.assertEqual(len(faces), 10)
        self.assertEqual(len(faces), len(materials))
        self.assertEqual(materials.count(0), 2)   # two top quads
        self.assertEqual(materials.count(2), 2)   # two underside quads
        for k, station in enumerate(stations):
            left, right = vertices[2*k], vertices[2*k+1]
            self.assertAlmostEqual((left[0] + right[0]) / 2, station[0])
            self.assertAlmostEqual((left[1] + right[1]) / 2, station[1])
            self.assertAlmostEqual(left[2], station[2])
            self.assertAlmostEqual(right[2], station[2])
        self.assertGreater(self._normal_z(vertices, faces[0]), 0)

    @staticmethod
    def _normal_z(vertices, face):
        a, b, c = (vertices[i] for i in face[:3])
        return ((b[0]-a[0])*(c[1]-a[1])
                - (b[1]-a[1])*(c[0]-a[0]))

    def test_living_branches_reach_each_deck(self):
        base = (-113, 187, 10)
        huts = [('main', (-104, 161, 50)), ('west', (-153, 143, 32))]
        paths = village_branch_paths(base, huts)
        self.assertEqual(list(paths), ['main', 'west'])
        for name, deck in huts:
            path = paths[name]
            self.assertEqual(len(path), 4)
            self.assertEqual(path[0][:2], base[:2])
            self.assertEqual(path[-1][:2], deck[:2])
            self.assertAlmostEqual(path[-1][2], deck[2] - 1.4)
            self.assertTrue(all(b[2] > a[2] for a, b in zip(path, path[1:])))

    def test_bad_bridge_and_duplicate_huts_rejected(self):
        with self.assertRaises(ValueError):
            bridge_deck([(0, 0, 0)], 5, 2)
        with self.assertRaises(ValueError):
            bridge_deck([(0, 0, 0), (0, 0, 7)], 5, 2)
        with self.assertRaises(ValueError):
            village_branch_paths((0, 0, 0), [
                ('hut', (2, 3, 20)), ('hut', (4, 5, 22))])


    def test_canyon_wall_is_continuous_across_stations(self):
        stations = [(222, 132, 31), (224, 153, 38), (228, 176, 51),
                    (231, 196, 62), (230, 216, 68)]
        verts, faces, mats = canyon_rim_wall(stations)
        self.assertEqual(len(verts), 9 * len(stations))
        self.assertEqual(len(faces), 8 * (len(stations) - 1))
        self.assertEqual(len(mats), len(faces))
        self.assertEqual(set(mats), {0, 1, 2})
        for face in faces:
            self.assertEqual(len(face), 4)
            self.assertTrue(all(0 <= i < len(verts) for i in face))
        # The same vertex from each station is shared across adjacent faces.
        self.assertEqual(faces[0][1], faces[1][0])
        self.assertAlmostEqual(min(p[2] for p in verts), -52)

    def test_canyon_wall_rejects_disconnected_or_invalid_profiles(self):
        with self.assertRaisesRegex(ValueError, 'three'):
            canyon_rim_wall([(220, 130, 31), (220, 150, 32)])
        with self.assertRaisesRegex(ValueError, 'progress'):
            canyon_rim_wall([(220, 150, 40), (221, 140, 45),
                             (222, 160, 42)])
        with self.assertRaisesRegex(ValueError, 'foot'):
            canyon_rim_wall([(220, 130, 31), (221, 150, 40),
                             (222, 170, 51)], bottom=18)


if __name__ == '__main__':
    unittest.main()
