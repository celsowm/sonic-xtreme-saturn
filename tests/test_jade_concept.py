"""Pure-Python contract tests: can run on CI without Blender."""
import copy
import json
import unittest
from tools.validate_jade_concept import DEFAULT, validate


class JadeConceptTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DEFAULT.read_text(encoding='utf-8'))

    def test_five_regions_and_visual_landmarks(self):
        self.assertEqual(validate(self.data)['sectors'], 5)
        self.assertEqual(validate(self.data)['routes'], 6)
        self.assertEqual(validate(self.data)['landmarks'], 12)

    def test_every_optional_route_rejoins(self):
        modified = copy.deepcopy(self.data)
        modified['routes'][1]['points'][-1][0] += 1
        with self.assertRaisesRegex(ValueError, 'connect'):
            validate(modified)

    def test_sectors_cannot_overlap(self):
        modified = copy.deepcopy(self.data)
        modified['sectors'][2]['y_range'][0] -= 5
        with self.assertRaisesRegex(ValueError, 'gap or overlap'):
            validate(modified)

    def test_landmarks_in_correct_sector(self):
        modified = copy.deepcopy(self.data)
        modified['landmarks'][0]['sector'] = 'summit'
        with self.assertRaisesRegex(ValueError, 'wrong sector'):
            validate(modified)

    def test_route_monotonicity(self):
        modified = copy.deepcopy(self.data)
        modified['routes'][0]['points'][3][1] = 1
        with self.assertRaisesRegex(ValueError, 'strictly'):
            validate(modified)

    def test_out_of_bounds_rejected(self):
        modified = copy.deepcopy(self.data)
        modified['landmarks'][0]['position'][0] = 1000
        with self.assertRaisesRegex(ValueError, 'outside'):
            validate(modified)


if __name__ == '__main__':
    unittest.main()
