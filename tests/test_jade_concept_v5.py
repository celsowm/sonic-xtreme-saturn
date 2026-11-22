"""Deterministic checks for the V5 visual landmass shape (no Blender)."""
import copy
import json
import math
import unittest

from tools.validate_jade_concept_v4 import DEFAULT, validate

from tools.jade_concept_v4_geometry import (
    bridge_deck, canyon_rim_wall, organic_footprint, polygon_area, river_ribbon,
    layered_leaf_canopies, scenic_walkway_stations, stratified_plateau, treehouse_thatch_roof,
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


    def test_layered_treehouse_roof_is_broad_low_and_irregular(self):
        a = treehouse_thatch_roof(-100, 150, 46, 16, seed=42)
        b = treehouse_thatch_roof(-100, 150, 46, 16, seed=42)
        c = treehouse_thatch_roof(-100, 150, 46, 16, seed=53)
        self.assertEqual(a, b)
        self.assertNotEqual(a[0], c[0])
        vertices, faces, mats = a
        self.assertEqual(len(vertices), 5 * 16 + 1)
        self.assertEqual(len(faces), 5 * 16)
        self.assertEqual(set(mats), {0, 1, 2})
        self.assertTrue(all(len(face) in (3, 4) for face in faces))
        self.assertGreater(max(v[0] for v in vertices) - min(v[0] for v in vertices), 30)
        self.assertLess(max(v[2] for v in vertices) - min(v[2] for v in vertices), 9)
        self.assertGreater(self._normal_z(vertices, faces[18]), 0)

    def test_meandering_canyon_river_shared_edges_and_widths(self):
        stations = [(166, 130), (164, 147), (178, 165), (174, 188),
                    (181, 211), (191, 234)]
        widths = [13, 15, 20, 17, 19, 22]
        vertices, faces, mats = river_ribbon(stations, widths, 10)
        self.assertEqual(len(vertices), len(stations) * 2)
        self.assertEqual(len(faces), len(stations) - 1)
        self.assertTrue(all(mat == 0 for mat in mats))
        self.assertTrue(all(abs(v[2] - 10) < 1e-9 for v in vertices))
        for i, face in enumerate(faces):
            self.assertGreater(self._normal_z(vertices, face), 0)
            if i < len(faces) - 1:
                self.assertEqual(face[2], faces[i+1][1])
                self.assertEqual(face[3], faces[i+1][0])

    def test_new_organic_shapes_reject_invalid_inputs(self):
        with self.assertRaises(ValueError):
            treehouse_thatch_roof(0, 0, 3, 0)
        with self.assertRaises(ValueError):
            river_ribbon([(0, 0), (0, 10), (0, 20)], [2, 2], 1)
        with self.assertRaises(ValueError):
            river_ribbon([(0, 0), (0, 10), (0, 5)], [2, 2, 2], 1)

    def test_manifest_keeps_river_narrow_and_away_from_ridge(self):
        data = json.loads(DEFAULT.read_text(encoding='utf-8'))
        validate(data)
        self.assertGreaterEqual(len(data['canyon_river']['stations']), 5)
        bad = copy.deepcopy(data)
        bad['canyon_river']['widths'][1] = 80
        with self.assertRaisesRegex(ValueError, 'too wide'):
            validate(bad)
        bad = copy.deepcopy(data)
        bad['canyon_river']['stations'][2][1] = 140
        with self.assertRaisesRegex(ValueError, 'continuous'):
            validate(bad)


    def test_layered_canopy_has_jagged_lowpoly_silhouette(self):
        clusters = [(0, 0, 30, 8, 1.2, 1.0, .85, 0),
                    (25, 4, 35, 7, 1.0, 1.1, .70, 1)]
        verts, faces, mats = layered_leaf_canopies(clusters, segments=9)
        self.assertEqual(len(verts), 2 * (3*9+2))
        self.assertEqual(len(faces), 2 * 4*9)
        self.assertEqual(len(faces), len(mats))
        self.assertEqual(set(mats), {0, 1})
        self.assertEqual((verts, faces, mats),
                         layered_leaf_canopies(clusters, segments=9))
        for face in faces:
            self.assertTrue(all(0 <= i < len(verts) for i in face))
            self.assertEqual(len(face), len(set(face)))
        # Crown rims vary by angle and height rather than having sphere rings.
        r = [math.hypot(v[0], v[1]) for v in verts[:9]]
        self.assertGreater(max(r) - min(r), 1.1)
        top = verts[3*9]
        self.assertGreater(top[2], max(v[2] for v in verts[:9]))
        # Front upper walls have upward/outward facing normals.
        self.assertGreater(self._normal_z(verts, faces[9]), 0)

    def test_foliage_rejects_invalid_meshes(self):
        with self.assertRaisesRegex(ValueError, 'range'):
            layered_leaf_canopies([], segments=4)
        with self.assertRaisesRegex(ValueError, 'positive'):
            layered_leaf_canopies([(0,0,0,-2,1,1,1,0)])
        with self.assertRaisesRegex(ValueError, 'parameters'):
            layered_leaf_canopies([(0,0,0,2,1,1,1)])

    def test_canyon_shelves_stay_bounded_and_staggered(self):
        data = json.loads(DEFAULT.read_text(encoding='utf-8'))
        self.assertEqual(len(data['canyon_shelves']), 6)
        self.assertEqual(len({r['top'] for r in data['canyon_shelves']}), 6)
        validate(data)
        bad = copy.deepcopy(data)
        bad['canyon_shelves'][0]['size'] = [100, 15]
        with self.assertRaisesRegex(ValueError, 'narrow'):
            validate(bad)
        bad = copy.deepcopy(data)
        bad['canyon_shelves'][1]['center'] = [240, 140]
        with self.assertRaises(ValueError):
            validate(bad)

    def test_curved_walkway_connects_real_decks_at_exact_endpoints(self):
        a, b = (-121, 153, 40), (-114, 184, 49)
        points = scenic_walkway_stations(a, b, 'stairs', curvature=3.8)
        self.assertEqual(points[0], a)
        self.assertEqual(points[-1], b)
        self.assertEqual(len(points), 13)
        self.assertNotAlmostEqual(points[6][0], a[0] + (b[0]-a[0])*.5)
        self.assertTrue(all(x[2] < y[2] for x, y in zip(points, points[1:])))
        v, f, m = bridge_deck(points, 5.4, 1.4)
        self.assertEqual(len(faces := f), len(m))
        self.assertGreater(len(v), 40)
        self.assertTrue(all(len(face) == 4 for face in faces))

    def test_bounded_curvature_prevents_spaghetti_ramps(self):
        with self.assertRaisesRegex(ValueError, 'curvature too large'):
            scenic_walkway_stations((0,0,0),(10,0,2),'stairs',curvature=5)
        with self.assertRaisesRegex(ValueError, 'solid surface'):
            scenic_walkway_stations((0,0,0),(10,0,2),'jump')
        with self.assertRaisesRegex(ValueError, 'too close'):
            scenic_walkway_stations((0,0,0),(0,0,20),'stairs')


if __name__ == '__main__':
    unittest.main()
