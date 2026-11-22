"""Regression checks for painting-first route audit; not gameplay physics."""
import copy
import json
import unittest

from tools.audit_jade_routes_v5 import (AUDIT, MANIFEST, audit,
                                         nearest_route_distance,
                                         point_segment_distance)


class RouteAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        cls.inventory = json.loads(AUDIT.read_text(encoding='utf-8'))

    def test_visual_corridor_classes_are_not_independent_start_goal_routes(self):
        result = audit(self.manifest, self.inventory)
        self.assertEqual(result['visual_corridors'], 18)
        self.assertEqual(result['main_routes'], 1)
        self.assertEqual(result['alternate_routes'], 7)
        self.assertEqual(result['decorative_walkways'], 27)
        self.assertEqual(result['painted_evidence'], {
            'gold_main': 5, 'purple_shortcut': 5, 'platform_ring_hint': 8
        })
        self.assertEqual(result['coverage'], {
            'main_route': 5, 'partial_alternate': 3,
            'scenery_only': 9, 'missing': 1
        })
        self.assertEqual(result['unresolved_corridors'], 13)

    def test_all_five_painted_sectors_have_explicit_gaps(self):
        summary = audit(self.manifest, self.inventory)['sectors']
        self.assertEqual([s['corridors'] for s in summary.values()],
                         [3, 5, 3, 3, 4])
        self.assertTrue(all(s['unresolved'] >= 2 for s in summary.values()))

    def test_decorative_walkways_do_not_count_as_route_graph(self):
        result = audit(self.manifest, self.inventory)
        far = result['walkway_endpoints_over_6_world_units_from_any_route_centerline']
        self.assertEqual(len(far), 4)
        missing = {x['id'] for x in far}
        self.assertNotIn('village_rope_north', missing)
        self.assertNotIn('village_rope_lookout', missing)
        self.assertIn('canyon_dock_walk', missing)
        self.assertIn('canyon_stairs_mid', missing)
        self.assertIn('canyon_dock_a', missing)
        self.assertIn('canyon_dock_b', missing)
        for x in far:
            self.assertTrue(x['from_distance'] > 6 or x['to_distance'] > 6)

    def test_segment_projection_is_true_distance_not_nearest_station(self):
        self.assertAlmostEqual(
            point_segment_distance((5, 3, 0), (0, 0, 0), (10, 0, 0)),
            3)
        routes = [{'points': [(0, 0, 0), (10, 0, 0)]}]
        self.assertAlmostEqual(nearest_route_distance((5, 3, 0), routes), 3)
        self.assertAlmostEqual(nearest_route_distance((20, 0, 0), routes), 10)

    def test_duplicate_ids_rejected_before_false_coverage(self):
        bad = copy.deepcopy(self.inventory)
        bad['corridors'].append(copy.deepcopy(bad['corridors'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            audit(self.manifest, bad)

    def test_purple_shortcut_cannot_be_renamed_as_gold_main(self):
        bad = copy.deepcopy(self.inventory)
        bad['corridors'][5]['status'] = 'main_route'
        with self.assertRaisesRegex(ValueError, 'gold-line'):
            audit(self.manifest, bad)


if __name__ == '__main__':
    unittest.main()
