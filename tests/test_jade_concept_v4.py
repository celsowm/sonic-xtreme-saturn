"""Host tests for the painting-faithful Jade Gully concept v4 (no Blender)."""
import copy
import json
import math
import unittest

from tools.validate_jade_concept_v4 import DEFAULT, validate
from tools.jade_concept_v4_geometry import (
    arch, catmull_rom, floating_island, grass_mound, hex_tube, mountain_range,
    polygon_area, prism, rounded_rect, sample_along, slope, spiral_steps,
    star_prism)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DEFAULT.read_text(encoding='utf-8'))

    def test_painting_regions_and_signatures(self):
        report = validate(self.data)
        self.assertEqual(report['regions'], 5)
        self.assertGreaterEqual(report['waterfalls'], 8)
        self.assertGreaterEqual(report['huts'], 5)
        self.assertEqual([r['title'] for r in self.data['regions']],
                         ['ENTRY HILLS', 'TREE VILLAGE', 'SKY BRIDGES',
                          'HEX LOOP', 'CANYON BASIN'])

    def test_old_invented_names_are_rejected(self):
        bad = copy.deepcopy(self.data)
        bad['regions'][0]['title'] = "SONIC'S BASE"
        with self.assertRaisesRegex(ValueError, 'painting labels'):
            validate(bad)

    def test_main_route_order(self):
        bad = copy.deepcopy(self.data)
        bad['routes'][0]['points'].insert(3, [140, 200, 20])
        with self.assertRaisesRegex(ValueError, 'in order'):
            validate(bad)

    def test_alternates_rejoin_main(self):
        bad = copy.deepcopy(self.data)
        bad['routes'][1]['points'][-1][0] += 1
        with self.assertRaisesRegex(ValueError, 'connect'):
            validate(bad)

    def test_landmark_region(self):
        bad = copy.deepcopy(self.data)
        bad['huts'][0]['region'] = 'canyon_basin'
        with self.assertRaisesRegex(ValueError, 'outside its region'):
            validate(bad)

    def test_painted_details_are_validated(self):
        report = validate(self.data)
        self.assertGreaterEqual(report['hills'], 5)
        self.assertGreaterEqual(report['channels'], 3)
        bad = copy.deepcopy(self.data)
        bad['spiral']['radius'] = 5            # inside the trunk
        with self.assertRaises(ValueError):
            validate(bad)
        bad = copy.deepcopy(self.data)
        bad['regions'][0]['label_uv'] = [1.4, .5]
        with self.assertRaises(ValueError):
            validate(bad)
        bad = copy.deepcopy(self.data)
        bad['hills'][0]['center'] = [150, 200]  # canyon, not entry hills
        with self.assertRaises(ValueError):
            validate(bad)

    def test_hex_loop_stays_massive(self):
        bad = copy.deepcopy(self.data)
        bad['hex_loop']['radius'] = 8
        with self.assertRaisesRegex(ValueError, 'massive'):
            validate(bad)


class GeometryTests(unittest.TestCase):
    def assert_mesh(self, verts, faces, mats=None):
        self.assertTrue(verts and faces)
        for f in faces:
            self.assertGreaterEqual(len(f), 3)
            self.assertEqual(len(f), len(set(f)))
            self.assertTrue(all(0 <= i < len(verts) for i in f))
        if mats is not None:
            self.assertEqual(len(mats), len(faces))

    @staticmethod
    def normal(verts, face):
        a, b, c = (verts[i] for i in face[:3])
        u = [b[k] - a[k] for k in range(3)]
        v = [c[k] - a[k] for k in range(3)]
        return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0])

    def test_rounded_rect_is_ccw_and_bounded(self):
        poly = rounded_rect(10, 20, 30, 16, 4)
        self.assertGreater(polygon_area(poly), 0)
        self.assertTrue(all(-5 - 1e-9 <= x <= 25 + 1e-9 and 12 - 1e-9 <= y <= 28 + 1e-9
                            for x, y in poly))

    def test_prism_faces_point_outward(self):
        verts, faces, mats = prism(rounded_rect(0, 0, 10, 10, 2), 6, -20)
        self.assert_mesh(verts, faces, mats)
        self.assertGreater(self.normal(verts, faces[0])[2], 0)   # grass cap up
        self.assertLess(self.normal(verts, faces[1])[2], 0)      # base down
        for face, mat in zip(faces, mats):
            if mat == 1:
                n = self.normal(verts, face)
                c = [sum(verts[i][k] for i in face) / len(face) for k in range(2)]
                self.assertGreater(n[0] * c[0] + n[1] * c[1], 0)

    def test_floating_island_ends_in_point_below(self):
        verts, faces, mats = floating_island(rounded_rect(0, 0, 12, 10, 2), 40, 4, 20)
        self.assert_mesh(verts, faces, mats)
        self.assertAlmostEqual(min(v[2] for v in verts), 20)
        self.assertIn(3, mats)

    def test_hex_tube_rims_face_camera(self):
        verts, faces, mats = hex_tube(0, 0, 50, 30, .8, 16)
        self.assert_mesh(verts, faces, mats)
        self.assertEqual(len(faces), 24)
        front = [f for f, m in zip(faces, mats) if m == 2
                 and all(verts[i][1] < 0 for i in f)]
        self.assertEqual(len(front), 6)
        self.assertTrue(all(self.normal(verts, f)[1] < 0 for f in front))
        radii = {round(math.hypot(v[0], v[2] - 50), 6) for v in verts}
        self.assertEqual(radii, {30.0, 24.0})

    def test_arch_spans_and_rises(self):
        verts, faces, mats = arch(0, 0, 8, 18, 5, 9)
        self.assert_mesh(verts, faces, mats)
        self.assertAlmostEqual(max(v[2] for v in verts), 26)
        self.assertAlmostEqual(min(v[0] for v in verts), -18)

    def test_curve_keeps_stations(self):
        pts = [(0, 0, 0), (10, 0, 0), (10, 10, 5)]
        curve = catmull_rom(pts, 5)
        self.assertEqual(curve[0], pts[0])
        self.assertEqual(curve[-1], pts[-1])
        self.assertIn(pts[1], curve)
        marks = sample_along(curve, 3)
        self.assertGreater(len(marks), 5)

    def test_mountains_have_snow(self):
        verts, faces, mats = mountain_range(-400, 400, 600, 0, 9)
        self.assert_mesh(verts, faces, mats)
        self.assertIn(1, mats)

    def test_grass_mound_rolls_up_from_terrace(self):
        verts, faces, mats = grass_mound(5, 7, 6, 10, 8, 4)
        self.assert_mesh(verts, faces, mats)
        self.assertAlmostEqual(max(v[2] for v in verts), 10)
        self.assertAlmostEqual(min(v[2] for v in verts), 4)       # skirt sinks 2
        self.assertTrue(all(abs(v[0] - 5) <= 10 + 1e-9 and abs(v[1] - 7) <= 8 + 1e-9
                            for v in verts))
        for face in faces:                 # every face points up or outward
            n = self.normal(verts, face)
            c = [sum(verts[i][k] for i in face) / len(face) for k in range(3)]
            self.assertGreater(n[0] * (c[0] - 5) + n[1] * (c[1] - 7) + n[2], 0)

    def test_slope_joins_levels(self):
        verts, faces, mats = slope((0, 0, 6), (0, 20, 12), 10, -30)
        self.assert_mesh(verts, faces, mats)
        self.assertGreater(self.normal(verts, faces[0])[2], 0)
        self.assertEqual({v[2] for v in verts}, {6, 12, -30})

    def test_spiral_climbs_around_trunk(self):
        steps = spiral_steps(0, 0, 20, 10, 50, 1.25, 30)
        self.assertEqual(len(steps), 30)
        self.assertAlmostEqual(steps[0][0][2], 10)
        self.assertAlmostEqual(steps[-1][0][2], 50)
        for pos, tangent in steps:
            self.assertAlmostEqual(math.hypot(pos[0], pos[1]), 20)
            self.assertAlmostEqual(math.sqrt(sum(c * c for c in tangent)), 1)

    def test_star_faces_viewer(self):
        verts, faces, mats = star_prism(0, 0, 10, 3, 1.3, .6)
        self.assert_mesh(verts, faces, mats)
        front = [f for f in faces if len(f) == 3 and all(verts[i][1] < 0 for i in f)]
        self.assertEqual(len(front), 10)
        self.assertTrue(all(self.normal(verts, f)[1] < 0 for f in front))
        for face in faces:
            if len(face) == 4:
                n = self.normal(verts, face)
                c = [sum(verts[i][k] for i in face) / 4 for k in range(3)]
                self.assertGreater(n[0] * c[0] + n[2] * (c[2] - 10), 0)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            grass_mound(0, 0, 0, 5, 5, 0)
        with self.assertRaises(ValueError):
            slope((0, 0, 1), (0, 0, 5), 4, -10)
        with self.assertRaises(ValueError):
            prism([(0, 0), (0, 1), (1, 0)], 1, 0)   # clockwise
        with self.assertRaises(ValueError):
            hex_tube(0, 0, 0, 10, 1.2, 5)
        with self.assertRaises(ValueError):
            floating_island(rounded_rect(0, 0, 4, 4, 1), 10, 5, 3)


if __name__ == '__main__':
    unittest.main()
