"""Dependency-free validation of the painting-faithful Jade Gully concept v4.

The approved painting (docs/concepts/jade-gully-act1-concept.png) labels five
regions: 1 ENTRY HILLS, 2 TREE VILLAGE, 3 SKY BRIDGES, 4 HEX LOOP and
5 CANYON BASIN. The v1-v3 manifest used invented names (Sonic's Base, Jade
Ridges, Bamboo Heights, Gully Current, Jade Summit) and a single +Y strip;
this contract pins the painting's names, order and screen-space layout.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'assets/levels/jade_gully_concept_v4.json'
REGIONS = (
    ('entry_hills', 'ENTRY HILLS'),
    ('tree_village', 'TREE VILLAGE'),
    ('sky_bridges', 'SKY BRIDGES'),
    ('hex_loop', 'HEX LOOP'),
    ('canyon_basin', 'CANYON BASIN'),
)
WALKWAY_KINDS = {'stairs', 'rope', 'checker', 'plank'}


def region_of(xy, regions):
    """First region (in painting order) whose rectangle holds the XY point."""
    for region in regions:
        x0, y0, x1, y1 = region['rect']
        if x0 <= xy[0] <= x1 and y0 <= xy[1] <= y1:
            return region['id']
    return None


def validate(data):
    if data.get('schema_version') != 4:
        raise ValueError('unsupported concept schema (expected 4)')
    bounds = data['world_bounds']

    def point(coords, size=3):
        if len(coords) != size or any(type(v) not in (int, float) or not math.isfinite(v)
                                      for v in coords):
            raise ValueError('nonfinite or malformed point')
        for i, axis in enumerate('xyz'[:size]):
            if not bounds[axis][0] <= coords[i] <= bounds[axis][1]:
                raise ValueError('point outside concept bounds')
        return tuple(coords)

    regions = data['regions']
    if tuple((r['id'], r['title']) for r in regions) != REGIONS:
        raise ValueError('regions must match the painting labels 1-5 in order')
    if [r['number'] for r in regions] != [1, 2, 3, 4, 5]:
        raise ValueError('region numbers must be 1-5')
    ids = {r['id'] for r in regions}
    for r in regions:
        x0, y0, x1, y1 = r['rect']
        if x1 <= x0 or y1 <= y0:
            raise ValueError('empty region rectangle')
        point((x0, y0), 2)
        point((x1, y1), 2)
    # Painting composition: the route reads left-to-right overall.
    centres = [(r['rect'][0] + r['rect'][2]) / 2 for r in regions]
    if not (centres[0] < centres[2] < centres[3] < centres[4] and
            centres[1] < centres[2]):
        raise ValueError('regions must progress left-to-right like the painting')
    if not regions[1]['rect'][1] >= regions[0]['rect'][1]:
        raise ValueError('tree village must sit behind entry hills')

    # The V5 art-only far canyon rim must remain a continuous ordered profile
    # on the outside edge of Canyon Basin, rather than another detached block.
    rim = data.get('canyon_rim_stations')
    if not isinstance(rim, list) or len(rim) < 5:
        raise ValueError('missing continuous canyon rim profile')
    rim_points = [point(p) for p in rim]
    if any(b[1] <= a[1] or math.dist(a, b) > 45
           for a, b in zip(rim_points, rim_points[1:])):
        raise ValueError('canyon rim must progress continuously along Y')
    if any(x < 210 or x > 238 for x, y, z in rim_points):
        raise ValueError('canyon rim must stay on the far bank')

    # The canyon's blue water must be a narrow continuous stream, not the
    # old full-size blue rectangle concealing all of the terraced landings.
    river = data.get('canyon_river')
    if not isinstance(river, dict):
        raise ValueError('missing winding canyon river')
    river_points = [point(p, 2) for p in river.get('stations', [])]
    widths = river.get('widths', [])
    if len(river_points) < 5 or len(widths) != len(river_points):
        raise ValueError('canyon river stations and widths must match')
    if any(type(w) not in (int, float) or not math.isfinite(w) or
           not 6 <= w <= 28 for w in widths):
        raise ValueError('canyon river is too wide or invalid')
    if any(b[1] <= a[1] or math.dist(a, b) > 35
           for a, b in zip(river_points, river_points[1:])):
        raise ValueError('canyon river must be continuous and progress along Y')
    if any(x < 140 or x > 210 or y < 120 or y > 290
           for x, y in river_points):
        raise ValueError('canyon river must stay within the basin')

    # Staggered ledges in the canyon must stay inside the painted valley
    # and must not become full-width flat slabs that conceal the river.
    ledges = data.get('canyon_shelves')
    if not isinstance(ledges, list) or len(ledges) < 6:
        raise ValueError('canyon needs at least six authored shelf ledges')
    ledge_ids = set()
    for ledge in ledges:
        name = ledge.get('id')
        if not name or name in ledge_ids:
            raise ValueError('canyon ledge IDs must be unique')
        ledge_ids.add(name)
        x, y = point(ledge['center'], 2)
        if not (134 <= x <= 219 and 130 <= y <= 276):
            raise ValueError('canyon ledge outside painted valley')
        if len(ledge['size']) != 2 or not all(
                type(v) in (int, float) and math.isfinite(v)
                and 12 <= v <= 30 for v in ledge['size']):
            raise ValueError('canyon ledges must be narrow')
        if type(ledge['top']) not in (int, float) or not 18 <= ledge['top'] <= 75:
            raise ValueError('canyon ledges must be stepped above the river')

    routes = data['routes']
    if not routes or routes[0]['id'] != 'main' or routes[0]['kind'] != 'main' or \
            len({r['id'] for r in routes}) != len(routes):
        raise ValueError('distinct routes with main first required')
    main = [point(p) for p in routes[0]['points']]
    order = [region_of(p, regions) for p in main]
    if None in order:
        raise ValueError('main route leaves the painted regions')
    rank = [[r['id'] for r in regions].index(o) for o in order]
    if any(b < a for a, b in zip(rank, rank[1:])) or set(rank) != {0, 1, 2, 3, 4}:
        raise ValueError('main route must visit regions 1-5 in order')
    if math.dist(main[0][:2], data['start'][:2]) > 3 or \
            math.dist(main[-1][:2], data['goal'][:2]) > 3:
        raise ValueError('main route must run from START to GOAL')
    main_set = set(main)
    for route in routes[1:]:
        pts = [point(p) for p in route['points']]
        if route['kind'] != 'alternate' or len(pts) < 3:
            raise ValueError('optional routes are alternate shortcuts with 3+ points')
        if pts[0] not in main_set or pts[-1] not in main_set:
            raise ValueError('alternate route must connect to main at both ends')

    def check_region(item, xy):
        if item['region'] not in ids:
            raise ValueError('unknown region for ' + item['id'])
        x0, y0, x1, y1 = next(r['rect'] for r in regions if r['id'] == item['region'])
        if not (x0 <= xy[0] <= x1 and y0 <= xy[1] <= y1):
            raise ValueError(item['id'] + ' placed outside its region')

    seen = set()

    def unique(item):
        if item['id'] in seen:
            raise ValueError('duplicate id ' + item['id'])
        seen.add(item['id'])

    for item in data['terraces']:
        unique(item); check_region(item, item['center'])
        if min(item['size']) <= 0 or item['corner'] < 0:
            raise ValueError('bad terrace size')
        point((*item['center'], item['top']))
    for item in data['islands']:
        unique(item); check_region(item, item['center'])
        if min(item['size']) <= 0 or item['depth'] <= 4:
            raise ValueError('bad island size')
        point((*item['center'], item['top']))
    hexl = data['hex_loop']
    unique(hexl); check_region(hexl, hexl['center'])
    point(hexl['center'])
    if not (hexl['radius'] >= 20 and 0.5 <= hexl['inner_ratio'] < 0.95):
        raise ValueError('the hex loop must stay massive')
    for item in data['arches']:
        unique(item); check_region(item, item['center'])
    for item in data['pools']:
        unique(item); check_region(item, item['center'])
    for item in data['waterfalls']:
        unique(item); check_region(item, item['top'])
        point(item['top'])
        if item['height'] <= 0 or item['width'] <= 0:
            raise ValueError('bad waterfall')
    tree = data['giant_tree']
    unique(tree); check_region(tree, tree['base'])
    for item in data['huts']:
        unique(item); check_region(item, item['deck']); point(item['deck'])
    canyon_steep = {'canyon_stairs_mid', 'canyon_stairs_high',
                    'canyon_stairs_goal'}
    for item in data['walkways']:
        unique(item)
        if item['kind'] not in WALKWAY_KINDS:
            raise ValueError('unknown walkway kind')
        if math.dist(point(item['from']), point(item['to'])) < 4:
            raise ValueError('walkway too short')
        via = item.get('via', [])
        if item['id'] in canyon_steep and len(via) < 2:
            raise ValueError('canyon ascent needs switchback landings')
        if via and item['kind'] != 'stairs':
            raise ValueError('switchback requires stair walkway')
        stations = [point(item['from'])] + [point(v) for v in via] + [point(item['to'])]
        for a, b in zip(stations, stations[1:]):
            planar = math.hypot(b[0]-a[0], b[1]-a[1])
            angle = math.degrees(math.atan2(abs(b[2]-a[2]),planar))
            if item['kind'] == 'stairs' and (planar < 5 or angle > 32):
                raise ValueError('stair flight too steep or short: ' + item['id'])
    for item in data['clouds']:
        unique(item); check_region(item, item['center'])
    for spring in data['springs']:
        point(spring)

    counts = {
        'waterfalls': len(data['waterfalls']),
        'huts': len(data['huts']),
        'floating_islands': len(data['islands']),
    }
    # Signature density visible in the painting.
    if counts['waterfalls'] < 8 or counts['huts'] < 5 or counts['floating_islands'] < 8:
        raise ValueError('missing painting signatures (waterfalls/huts/islands)')
    if not any(r['kind'] == 'alternate' for r in routes):
        raise ValueError('painting shows alternate shortcut routes')

    # Painted details added after the first v4 review (rolling hills, spiral
    # walkway, canyon channels/decks, items and the map overlay).
    def uv(pair):
        if len(pair) != 2 or not all(0 <= v <= 1 for v in pair):
            raise ValueError('overlay positions are 0..1 image coordinates')
    for r in regions:
        uv(r['label_uv'])
    uv(data['overlay']['title_uv'])
    uv(data['overlay']['legend_uv'])
    for item in data['hills']:
        unique(item); check_region(item, item['center'])
        if min(item['radii']) <= 0 or item['height'] <= 0:
            raise ValueError('bad hill')
        point((*item['center'], item['base_z'] + item['height']))
    for item in data['slopes']:
        unique(item); check_region(item, item['from']); check_region(item, item['to'])
        if item['width'] <= 0 or math.dist(point(item['from']), point(item['to'])) < 4:
            raise ValueError('bad slope')
    spiral = data['spiral']
    unique(spiral); check_region(spiral, spiral['center'])
    if not (spiral['radius'] > tree['radius'] * 1.5 and spiral['z0'] < spiral['z1'] and
            spiral['turns'] > 0):
        raise ValueError('spiral walkway must wrap outside the trunk and climb')
    for item in data['platforms']:
        unique(item); check_region(item, item['deck']); point(item['deck'])
    for item in data['channels']:
        unique(item); check_region(item, item['from']); check_region(item, item['to'])
        point(item['from']); point(item['to'])
        if item['width'] <= 0 or item['from'][2] != item['to'][2]:
            raise ValueError('channels are level water troughs')
    for p in data['monitors'] + data['stars']:
        point(p)
    counts['hills'] = len(data['hills'])
    counts['channels'] = len(data['channels'])
    return {'regions': len(regions), 'routes': len(routes),
            'main_stations': len(main), **counts,
            'mode': 'offline-art-concept-only'}


if __name__ == '__main__':
    print(json.dumps(validate(json.loads(DEFAULT.read_text(encoding='utf-8'))), indent=2))
