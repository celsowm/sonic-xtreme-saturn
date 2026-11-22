#!/usr/bin/env python3
"""Audits painting-derived exploration corridors vs authored V4/V5 polylines.

This is a visual-design coverage test, not collision, navigation or gameplay.
"""
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'assets/levels/jade_gully_concept_v4.json'
INVENTORY = ROOT / 'assets/levels/jade_gully_route_audit_v5.json'
REGIONS = ('entry_hills','tree_village','sky_bridges','hex_loop','canyon_basin')
STATUS = {'main_route','partial_alternate','scenery_only','missing'}
EVIDENCE = {'gold_main','purple_shortcut','platform_ring_hint'}


def point_segment_distance(point, a, b):
    delta = tuple(v-u for u,v in zip(a,b))
    offset = tuple(v-u for u,v in zip(a,point))
    l2 = sum(v*v for v in delta)
    t = max(0., min(1., sum(delta[i]*offset[i] for i in range(3))/l2)) if l2>0 else 0.
    return math.sqrt(sum((a[i]+t*delta[i]-point[i])**2 for i in range(3)))


def nearest_route_distance(point, routes):
    return min(point_segment_distance(point,a,b)
               for route in routes
               for a,b in zip(route['points'],route['points'][1:]))


def audit(manifest, inventory, tolerance=6.):
    if inventory.get('schema_version') != 1:
        raise ValueError('unsupported route audit schema')
    routes = manifest['routes']
    if not routes or routes[0]['kind'] != 'main' or routes[0]['id'] != 'main':
        raise ValueError('first route must be the one gold main route')
    regions = tuple(x['id'] for x in manifest['regions'])
    if regions != REGIONS:
        raise ValueError('wrong painted regions')
    corridors = inventory['corridors']
    ids = [c['id'] for c in corridors]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate corridor id')
    for c in corridors:
        if c['region'] not in regions or c['status'] not in STATUS or c['evidence'] not in EVIDENCE:
            raise ValueError('bad corridor classification')
        if c['status'] == 'main_route' and c['evidence'] != 'gold_main':
            raise ValueError('main route requires drawn gold-line evidence')
    statuses = Counter(c['status'] for c in corridors)
    evidence = Counter(c['evidence'] for c in corridors)
    gaps = []
    for walkway in manifest['walkways']:
        a = nearest_route_distance(walkway['from'],routes)
        b = nearest_route_distance(walkway['to'],routes)
        if a > tolerance or b > tolerance:
            gaps.append({'id':walkway['id'],'from_distance':round(a,2),
                         'to_distance':round(b,2)})
    return {
        'interpretation':'Painting-derived corridor FEATURES, not independent playable START-to-GOAL routes',
        'main_routes':sum(r['kind']=='main' for r in routes),
        'alternate_routes':sum(r['kind']=='alternate' for r in routes),
        'decorative_walkways':len(manifest['walkways']),
        'visual_corridors':len(corridors),
        'painted_evidence':dict(evidence),
        'coverage':dict(statuses),
        'unresolved_corridors':sum(statuses[k] for k in ('partial_alternate','scenery_only','missing')),
        'walkway_endpoints_over_6_world_units_from_any_route_centerline':gaps,
        'sectors':{region:{'corridors':sum(c['region']==region for c in corridors),
                           'unresolved':sum(c['region']==region and c['status'] != 'main_route'
                                            for c in corridors)} for region in regions},
        'next_gate':'physical route graph, START/GOAL reachability, landing pads, jump/spring/gravity edges, then actual Saturn gameplay'
    }


def main():
    data=json.loads(MANIFEST.read_text(encoding='utf-8'))
    inv=json.loads(INVENTORY.read_text(encoding='utf-8'))
    print(json.dumps(audit(data,inv),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
