"""Dependency-free checks for the five-sector Jade Gully concept blockout.

Do not conflate this concept manifest with the shipping Adventure gameplay map.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'assets/levels/jade_gully_concept_v1.json'
SECTOR_IDS = ('base', 'ridges', 'bamboo', 'current', 'summit')
SECTOR_TITLES = ("SONIC'S BASE", 'JADE RIDGES', 'BAMBOO HEIGHTS',
                 'GULLY CURRENT', 'JADE SUMMIT / EXIT')
LANDMARK_KINDS = {'dome', 'tower', 'hex_loop', 'treehouse', 'waterfall', 'goal'}


def validate(data):
    if data.get('schema_version') != 1:
        raise ValueError('unsupported concept schema')
    bounds = data['world_bounds']

    def point(coords):
        if len(coords) != 3 or any(type(v) not in (float, int) or not math.isfinite(v)
                                   for v in coords):
            raise ValueError('nonfinite or non-XYZ point')
        if any(not (bounds[axis][0] <= coords[i] <= bounds[axis][1])
               for i, axis in enumerate('xyz')):
            raise ValueError('point outside concept bounds')
        return tuple(coords)

    sectors = data['sectors']
    if tuple(s['id'] for s in sectors) != SECTOR_IDS or \
            tuple(s['title'] for s in sectors) != SECTOR_TITLES:
        raise ValueError('concept must keep the five approved areas in order')
    for i, sector in enumerate(sectors):
        low, high = sector['y_range']
        if high <= low or not (bounds['y'][0] <= low < high <= bounds['y'][1]):
            raise ValueError('invalid sector span')
        if i and low != sectors[i-1]['y_range'][1]:
            raise ValueError('gap or overlap between sectors')
        if not 40 <= sector['width'] <= 100:
            raise ValueError('sector width')

    routes = data['routes']
    if not routes or routes[0]['id'] != 'main' or \
            len({r['id'] for r in routes}) != len(routes):
        raise ValueError('distinct routes with main first required')
    main = {tuple(p) for p in routes[0]['points']}
    for route in routes:
        positions = [point(p) for p in route['points']]
        if len(positions) < 3 or any(b[1] <= a[1] for a, b in zip(positions, positions[1:])):
            raise ValueError('routes must advance strictly on +Y')
        if route is not routes[0] and (positions[0] not in main or positions[-1] not in main):
            raise ValueError('optional route must connect to main at both ends')
        if route['kind'] not in ('main','risk','explore'):
            raise ValueError('invalid route kind')
    if routes[0]['points'][0][1] != sectors[0]['y_range'][0] or \
            routes[0]['points'][-1][1] != sectors[-1]['y_range'][1]:
        raise ValueError('main route must cover the full level')

    landmarks = data['landmarks']
    if len({m['id'] for m in landmarks}) != len(landmarks):
        raise ValueError('duplicate landmark')
    for item in landmarks:
        point(item['position'])
        if item['kind'] not in LANDMARK_KINDS or item['size'] <= 0:
            raise ValueError('unsupported landmark type/scale')
        sector = next((s for s in sectors if s['id'] == item['sector']), None)
        if sector is None or not sector['y_range'][0] <= item['position'][1] <= sector['y_range'][1]:
            raise ValueError('landmark placed in the wrong sector')
    if sum(m['kind'] == 'hex_loop' for m in landmarks) < 3 or \
            sum(m['kind'] == 'treehouse' for m in landmarks) < 3 or \
            sum(m['kind'] == 'waterfall' for m in landmarks) < 2:
        raise ValueError('missing approved concept signatures')
    if sum(m['kind'] == 'goal' for m in landmarks) != 1:
        raise ValueError('exactly one goal landmark required')
    settings = data['render']
    if not (6 <= settings['terrain_x_steps'] <= 24 and
            6 <= settings['terrain_y_steps_per_sector'] <= 32):
        raise ValueError('unbounded terrain mesh resolution')
    return {'sectors': len(sectors), 'routes': len(routes),
            'landmarks': len(landmarks), 'main_stations': len(routes[0]['points']),
            'mode': 'offline-art-concept-only'}


if __name__ == '__main__':
    print(json.dumps(validate(json.loads(DEFAULT.read_text())), indent=2))
