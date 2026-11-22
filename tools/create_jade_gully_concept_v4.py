"""Build the painting-faithful Jade Gully Act 1 concept v4 in Blender 5.2.

OFFLINE ART RECONSTRUCTION of docs/concepts/jade-gully-act1-concept.png.
Not Saturn geometry, collision or gameplay. All meshes and materials are
original and procedural (no Kenney, Sega or painting pixels are used as
textures; the painting is only loaded to build the side-by-side review).

  blender -b --factory-startup --python-exit-code 1 \\
    --python tools/create_jade_gully_concept_v4.py -- build/jade-gully-concept-v4

Target: Blender 5.2 LTS (the version installed on the project Mac).
"""
import json
import math
import sys
import warnings
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validate_jade_concept_v4 import DEFAULT, validate  # noqa: E402
from tools import jade_concept_v4_geometry as geo  # noqa: E402

CONCEPT_PNG = ROOT / 'docs/concepts/jade-gully-act1-concept.png'
OVERLAY = 'MAP_OVERLAY'
CLIFF_FOOT = -62.0      # checker cliffs rise out of the jungle like the painting
JUNGLE_Z = -48.0        # jungle canopy level around the landmass
CLOUD_SEA_Z = -40.0     # cloud sea under the sky bridges and hex loop
# Painting reference camera, fitted to seven painted landmark positions
# (see docs/concepts/JADE_GULLY_CONCEPT_V4.md).
MAP_CAMERA = {'location': (50, -156, 310), 'target': (14, 148, 14), 'lens': 40}


# ---------------------------------------------------------------- materials
def _nodes(material):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        material.use_nodes = True
    return material.node_tree.nodes, material.node_tree.links


def _bsdf(material):
    nodes, _ = _nodes(material)
    return nodes.get('Principled BSDF')


def _emit(bsdf, rgb, strength):
    socket = bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
    if socket is not None:
        socket.default_value = (*rgb, 1)
    if bsdf.inputs.get('Emission Strength') is not None:
        bsdf.inputs['Emission Strength'].default_value = strength


def flat(name, rgb, rough=.8, emission=0.0, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    b = _bsdf(m)
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metallic
    if emission:
        _emit(b, rgb, emission)
    return m


def checker(name, rgb1, rgb2, cell, rough=.85, emission=0.0, offset=.37):
    """3D procedural checker in object space (objects are authored in world
    coordinates, so squares line up across neighbouring columns)."""
    m = flat(name, rgb1, rough)
    nodes, links = _nodes(m)
    coord = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs['Location'].default_value = (offset * cell,) * 3
    tex = nodes.new('ShaderNodeTexChecker')
    tex.inputs['Color1'].default_value = (*rgb1, 1)
    tex.inputs['Color2'].default_value = (*rgb2, 1)
    tex.inputs['Scale'].default_value = 1.0 / cell
    links.new(coord.outputs['Object'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    b = nodes.get('Principled BSDF')
    links.new(tex.outputs['Color'], b.inputs['Base Color'])
    if emission:
        socket = b.inputs.get('Emission Color') or b.inputs.get('Emission')
        links.new(tex.outputs['Color'], socket)
        b.inputs['Emission Strength'].default_value = emission
    return m


def waterfall_material(name):
    """Vertical white/sky-blue streaks like the painted falls."""
    m = flat(name, (.80, .93, 1.0), .25)
    nodes, links = _nodes(m)
    coord = nodes.new('ShaderNodeTexCoord')
    wave = nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'X'
    wave.inputs['Scale'].default_value = .22
    wave.inputs['Distortion'].default_value = 4.0
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (.06, .32, .85, 1)
    ramp.color_ramp.elements[1].position = .8
    ramp.color_ramp.elements[1].color = (.85, .95, 1.0, 1)
    links.new(coord.outputs['Object'], wave.inputs['Vector'])
    links.new(wave.outputs['Fac'], ramp.inputs['Fac'])
    b = nodes.get('Principled BSDF')
    links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    socket = b.inputs.get('Emission Color') or b.inputs.get('Emission')
    links.new(ramp.outputs['Color'], socket)
    b.inputs['Emission Strength'].default_value = .18
    return m


def leafy(name, dark, light, scale=.35):
    """Noise-mottled foliage so jungle blobs read as leaf masses, not plastic."""
    m = flat(name, dark, .95)
    nodes, links = _nodes(m)
    coord = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 6.0
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .38
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = .68
    ramp.color_ramp.elements[1].color = (*light, 1)
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .7
    links.new(coord.outputs['Object'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    b = nodes.get('Principled BSDF')
    links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def cloud_material(name):
    """Soft painted cloud banks: white tops with blue-lilac shading, billowy
    bump, and silhouettes that fade out instead of ending as hard blobs."""
    m = flat(name, (.92, .95, 1.0), 1.0, emission=.12)
    nodes, links = _nodes(m)
    b = nodes.get('Principled BSDF')
    out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    coord = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = .18
    noise.inputs['Detail'].default_value = 4.0
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .55
    links.new(coord.outputs['Object'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], b.inputs['Normal'])
    weight = nodes.new('ShaderNodeLayerWeight')
    weight.inputs['Blend'].default_value = .35
    fade = nodes.new('ShaderNodeValToRGB')
    fade.color_ramp.elements[0].position = .30
    fade.color_ramp.elements[1].position = .88
    clear = nodes.new('ShaderNodeBsdfTransparent')
    mix = nodes.new('ShaderNodeMixShader')
    links.new(weight.outputs['Facing'], fade.inputs['Fac'])
    links.new(fade.outputs['Color'], mix.inputs['Fac'])
    links.new(b.outputs['BSDF'], mix.inputs[1])
    links.new(clear.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return m


def hud_material(name, rgb):
    """Unlit flat colour for the map title, labels and legend."""
    m = bpy.data.materials.new(name)
    nodes, links = _nodes(m)
    for node in list(nodes):
        if node.type != 'OUTPUT_MATERIAL':
            nodes.remove(node)
    out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (*rgb, 1)
    links.new(emission.outputs['Emission'], out.inputs['Surface'])
    return m


def sky_panel_material(name):
    """Unlit painted sky: deep blue at the top, pale near the horizon."""
    m = bpy.data.materials.new(name)
    nodes, links = _nodes(m)
    for node in list(nodes):
        if node.type != 'OUTPUT_MATERIAL':
            nodes.remove(node)
    out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    coord = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .30
    ramp.color_ramp.elements[0].color = (.50, .70, 1.0, 1)
    ramp.color_ramp.elements[1].position = .95
    ramp.color_ramp.elements[1].color = (.03, .12, .55, 1)
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value = 1.0
    links.new(coord.outputs['Generated'], sep.inputs[0])
    links.new(sep.outputs['Y'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], emission.inputs['Color'])
    links.new(emission.outputs['Emission'], out.inputs['Surface'])
    return m


def build_palette():
    """Colours sampled by eye from the approved painting (sRGB-ish linear)."""
    return {
        'grass': checker('grass checker (painting top)', (.045, .33, .02), (.15, .50, .03), 4.0),
        'grass_dark': checker('grass checker arch shade', (.03, .26, .02), (.10, .40, .03), 3.0),
        'cliff': checker('ochre/brown checker cliff', (.56, .17, .025), (.19, .05, .012), 4.0),
        'underside': flat('floating island rock underside', (.28, .14, .06), .95),
        'hex_outer': checker('hex loop green checker shell', (.05, .34, .06), (.12, .52, .10), 4.0),
        'hex_inner': checker('hex loop blue running surface', (.03, .14, .55), (.08, .30, .80), 4.0, emission=.10),
        'hex_rim': checker('hex loop rim', (.04, .28, .05), (.10, .44, .08), 4.0),
        'water': checker('pool water tiles', (.01, .16, .70), (.03, .32, .92), 2.0, .15, emission=.10),
        'falls': waterfall_material('waterfall streaks'),
        'foam': flat('foam and mist', (.90, .96, 1.0), .9, emission=.15),
        'cloud': cloud_material('soft cloud bank'),
        'monitor': flat('item monitor casing', (.70, .72, .78), .35, metallic=.4),
        'screen': flat('item monitor screen', (.10, .45, 1.0), .2, emission=1.2),
        'star': flat('bonus star', (1.0, .80, .10), .3, emission=.8, metallic=.3),
        'hud_plate': hud_material('label plate', (.015, .03, .16)),
        'hud_border': hud_material('label border', (.55, .70, 1.0)),
        'hud_text': hud_material('label text', (1.0, 1.0, 1.0)),
        'hud_gold': hud_material('label number badge', (1.0, .72, .05)),
        'hud_title': hud_material('title text', (1.0, .80, .08)),
        'hud_dark': hud_material('badge number', (.02, .02, .08)),
        'hud_pink': hud_material('legend spring', (1.0, .35, .75)),
        'hud_violet': hud_material('legend alternate', (.65, .25, 1.0)),
        'hud_green': hud_material('legend island top', (.10, .55, .05)),
        'hud_brown': hud_material('legend island side', (.55, .22, .04)),
        'abyss': flat('blue void under the clouds', (.02, .10, .55), 1.0, emission=.9),
        'bark': flat('giant tree bark', (.16, .08, .03), .9),
        'canopy': leafy('tree canopy', (.02, .18, .02), (.07, .40, .03), .45),
        'canopy_light': leafy('tree canopy light', (.05, .30, .02), (.16, .55, .04), .45),
        'jungle': leafy('jungle canopy', (.006, .06, .012), (.03, .22, .03), .5),
        'jungle_light': leafy('jungle canopy lit', (.02, .14, .02), (.08, .36, .04), .5),
        'bush': leafy('bush', (.02, .20, .02), (.07, .40, .03), .9),
        'sky_panel': sky_panel_material('painted sky backdrop'),
        'palm': flat('palm fronds', (.08, .48, .05), .8),
        'palm_trunk': flat('palm trunk', (.35, .20, .07), .9),
        'wood': flat('wood deck', (.40, .20, .06), .85),
        'plank': flat('light planks', (.62, .36, .12), .85),
        'rope': flat('rope', (.70, .52, .26), .9),
        'thatch': flat('straw thatch', (.85, .58, .12), .9, emission=.05),
        'hut_wall': flat('hut wall', (.55, .32, .10), .9),
        'dark': flat('door shadow', (.04, .03, .02), 1.0),
        'gold': flat('rings', (1.0, .72, .05), .3, emission=.55, metallic=.6),
        'route': flat('main route arrow', (1.0, .80, .12), .5, emission=.9),
        'alt_route': flat('alternate route dots', (.55, .10, .95), .5, emission=.8),
        'spring_base': flat('spring base', (.55, .55, .60), .5),
        'spring_top': flat('spring pad', (.95, .20, .60), .4, emission=.35),
        'pad_glow': flat('start/goal glow', (1.0, .70, .95), .4, emission=1.6),
        'mountain': flat('distant mountain', (.20, .22, .48), 1.0, emission=.30),
        'snow': flat('snow cap', (.90, .92, 1.0), 1.0, emission=.35),
        'far_hill': flat('far jungle hill', (.03, .16, .10), 1.0, emission=.05),
    }


# ---------------------------------------------------------------- builders
def link(obj, collection=None):
    (collection or bpy.context.scene.collection).objects.link(obj)
    obj['stage_role'] = 'concept_v4_visual_only'
    return obj


def mesh(name, verts, faces, materials, mats=None, smooth=False, collection=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    for material in materials:
        data.materials.append(material)
    if mats:
        data.polygons.foreach_set('material_index', mats)
    if smooth:
        data.polygons.foreach_set('use_smooth', [True] * len(data.polygons))
    return link(bpy.data.objects.new(name, data), collection)


def soften(obj, width=1.1):
    """Rounded grass lips like the painting (non-destructive bevel)."""
    bevel = obj.modifiers.new('painted_soft_edge', 'BEVEL')
    bevel.width = width
    bevel.segments = 2
    bevel.limit_method = 'ANGLE'
    return obj


def blob_field(name, blobs, materials, subdivisions=2, collection=None):
    """Many sphere blobs in ONE mesh (jungle canopy, clouds, tree crowns).
    blob = (x, y, z, radius, sx, sy, sz, material_index)."""
    bm = bmesh.new()
    for x, y, z, r, sx, sy, sz, index in blobs:
        matrix = Matrix.Translation((x, y, z)) @ Matrix.Diagonal((sx * r, sy * r, sz * r, 1))
        made = bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0, matrix=matrix)
        faces = {f for v in made['verts'] for f in v.link_faces}
        for f in faces:
            f.material_index = index
            f.smooth = True
    data = bpy.data.meshes.new(name)
    bm.to_mesh(data)
    bm.free()
    for material in materials:
        data.materials.append(material)
    return link(bpy.data.objects.new(name, data), collection)


def boxes(name, items, materials, collection=None):
    """Oriented boxes in one mesh: (centre, forward, width, length, height, mat)."""
    verts, faces, mats = [], [], []
    for centre, forward, width, length, height, index in items:
        f = Vector(forward).normalized()
        side = f.cross(Vector((0, 0, 1)))
        if side.length < 1e-6:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(f).normalized()
        c = Vector(centre)
        n = len(verts)
        for dz in (-.5, .5):
            for dl, dw in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
                verts.append(tuple(c + f * (dl * length) + side * (dw * width) + up * (dz * height)))
        for quad in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            faces.append(tuple(n + q for q in quad))
            mats.append(index)
    return mesh(name, verts, faces, materials, mats, collection=collection)


def tube(name, points, material, radius, collection=None):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    curve.use_fill_caps = True
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for node, p in zip(spline.points, points):
        node.co = (*p, 1)
    curve.materials.append(material)
    return link(bpy.data.objects.new(name, curve), collection)


def prim(kind, name, location, material, **kw):
    getattr(bpy.ops.mesh, 'primitive_' + kind + '_add')(location=location, **kw)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    obj['stage_role'] = 'concept_v4_visual_only'
    return obj


def rnd(seed_text, k=0):
    """Deterministic 0..1 value from a string (no global random state)."""
    h = 2166136261
    for ch in seed_text + '#' + str(k):
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h / 0xFFFFFFFF


def palm(name, x, y, z, height, pal, lean=None, collection=None):
    lean = (rnd(name) - .5) * .5 if lean is None else lean
    heading = rnd(name, 1) * math.tau
    trunk = []
    for k in range(7):
        t = k / 6
        bend = lean * height * t * t
        trunk.append((x + math.cos(heading) * bend, y + math.sin(heading) * bend, z + height * t))
    tube(name + '_trunk', trunk, pal['palm_trunk'], max(.35, height * .028), collection)
    top = trunk[-1]
    verts, faces = [], []
    blades = 9
    for b in range(blades):
        a = math.tau * b / blades + rnd(name, 2)
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        reach = height * (.42 + .08 * rnd(name, b + 3))
        w = reach * .17
        n = len(verts)
        verts.extend((
            top,
            (top[0] + ux * reach * .35 + vx * w, top[1] + uy * reach * .35 + vy * w, top[2] + reach * .10),
            (top[0] + ux * reach * .70 + vx * w * .7, top[1] + uy * reach * .70 + vy * w * .7, top[2] - reach * .05),
            (top[0] + ux * reach, top[1] + uy * reach, top[2] - reach * .42),
            (top[0] + ux * reach * .70 - vx * w * .7, top[1] + uy * reach * .70 - vy * w * .7, top[2] - reach * .05),
            (top[0] + ux * reach * .35 - vx * w, top[1] + uy * reach * .35 - vy * w, top[2] + reach * .10),
        ))
        faces.extend(((n, n + 1, n + 5), (n + 1, n + 2, n + 4, n + 5), (n + 2, n + 3, n + 4)))
    mesh(name + '_fronds', verts, faces, [pal['palm']], collection=collection)


# ---------------------------------------------------------------- scene parts
def build_ground(data, pal):
    for t in data['terraces']:
        poly = geo.rounded_rect(*t['center'], *t['size'], t['corner'])
        v, f, m = geo.prism(poly, t['top'], CLIFF_FOOT)
        soften(mesh('terrace_' + t['id'], v, f, [pal['grass'], pal['cliff'], pal['underside']], m))
    for i in data['islands']:
        poly = geo.rounded_rect(*i['center'], *i['size'], min(i['size']) * .22)
        band = min(6.0, i['depth'] * .3)
        v, f, m = geo.floating_island(poly, i['top'], band, i['depth'])
        soften(mesh('island_' + i['id'], v, f,
                    [pal['grass'], pal['cliff'], pal['underside'], pal['underside']], m), .8)
    # Rolling grass hills and ramps: Entry Hills is painted as soft slopes,
    # not flat boxes.
    for h in data['hills']:
        v, f, m = geo.grass_mound(*h['center'], h['base_z'], *h['radii'], h['height'])
        mesh(h['id'], v, f, [pal['grass']], m, smooth=True)
    for s in data['slopes']:
        v, f, m = geo.slope(s['from'], s['to'], s['width'], CLIFF_FOOT)
        soften(mesh(s['id'], v, f, [pal['grass'], pal['cliff'], pal['underside']], m), .9)
    for a in data['arches']:
        v, f, m = geo.arch(*a['center'], a['base_z'], a['radius'], a['thickness'], a['width'], 14)
        mesh(a['id'], v, f, [pal['grass'], pal['grass_dark'], pal['underside']], m)
    for p in data['pools']:
        poly = geo.rounded_rect(*p['center'], *p['size'], min(p['size']) * .3)
        v, f, m = geo.prism(poly, p['z'], p['z'] - .6)
        mesh('pool_' + p['id'], v, f, [pal['water'], pal['water'], pal['water']], m)
    for w in data['waterfalls']:
        x, y, z = w['top']
        half, h = w['width'] / 2, w['height']
        verts = [(x - half, y, z), (x + half, y, z),
                 (x + half * 1.15, y - 2.0, z - h), (x - half * 1.15, y - 2.0, z - h)]
        mesh('waterfall_' + w['id'], verts, [(3, 2, 1, 0)], [pal['falls']])
        blob_field('waterfall_' + w['id'] + '_mist',
                   [(x + (k - 1) * half * .8, y - 3, z - h + 1, half * .55, 1.3, .8, .55, 0)
                    for k in range(3)], [pal['foam']], 1)


def hex_tilt_matrix(data):
    """The painting shows the loop face-on although the map is seen from
    above, so the loop is tilted about X to face the reference camera."""
    h = data['hex_loop']
    c = Vector(h['center'])
    to_cam = Vector(MAP_CAMERA['location']) - c
    # 60% of the full face-on tilt: the opening reads as a hexagon while
    # the blue running surface inside stays visible, as painted.
    angle = -.6 * math.atan2(to_cam.z, -to_cam.y)
    return Matrix.Translation(c) @ Matrix.Rotation(angle, 4, 'X') @ Matrix.Translation(-c), angle


def in_hex(data, p):
    h = data['hex_loop']
    cx, cy, cz = h['center']
    return abs(p[1] - cy) <= h['depth'] / 2 + 2 and math.hypot(p[0] - cx, p[2] - cz) <= h['radius'] + 2


def tilt_hex_points(data, points):
    matrix, _ = hex_tilt_matrix(data)
    return [tuple(matrix @ Vector(p)) if in_hex(data, p) else tuple(p) for p in points]


def build_pillars(data, pal):
    """Checker columns rising out of the cloud sea, filling the painting's
    centre between the authored sky-bridge islands (decor only)."""
    solids = [(item['center'], max(item['size']) / 2) for item in data['terraces'] + data['islands']]
    placed = []
    for k in range(400):
        if len(placed) >= 24:
            break
        x = -36 + rnd('pillar_x', k) * 156
        y = 66 + rnd('pillar_y', k) * 180
        w = 7 + rnd('pillar_w', k) * 8
        if any(math.dist((x, y), c) < r + w * .7 + 4 for c, r in solids + placed):
            continue
        if math.hypot(x - data['hex_loop']['center'][0], y - data['hex_loop']['center'][1]) < 30:
            continue
        top = -14 + rnd('pillar_top', k) * 34
        poly = geo.rounded_rect(x, y, w, w * (.8 + .4 * rnd('pillar_d', k)), w * .2)
        v, f, m = geo.prism(poly, top, CLIFF_FOOT)
        soften(mesh('pillar_%02d' % len(placed), v, f, [pal['grass'], pal['cliff'], pal['underside']], m), .7)
        if rnd('pillar_palm', k) > .5:
            palm('pillar_palm_%02d' % len(placed), x, y, top, 9 + 5 * rnd('pp', k), pal)
        placed.append(((x, y), w / 2))
    return len(placed)


def build_hex(data, pal):
    h = data['hex_loop']
    cx, cy, cz = h['center']
    matrix, angle = hex_tilt_matrix(data)
    v, f, m = geo.hex_tube(cx, cy, cz, h['radius'], h['inner_ratio'], h['depth'])
    mesh(h['id'], [tuple(matrix @ Vector(p)) for p in v], f,
         [pal['hex_outer'], pal['hex_inner'], pal['hex_rim']], m)
    # Keep the ring trail inside the hexagon's flats (apothem), not its
    # corner radius, so no ring cuts into the blue running surface.
    inner = h['radius'] * h['inner_ratio'] * math.cos(math.pi / 6) - 3.2
    for k in range(9):
        a = math.pi * .15 + math.pi * 1.3 * k / 8
        pos = matrix @ Vector((cx + inner * math.sin(a), cy - h['depth'] * .2, cz - inner * math.cos(a)))
        prim('torus', 'hex_ring_%d' % k, tuple(pos),
             pal['gold'], major_radius=1.6, minor_radius=.36,
             rotation=(math.pi / 2 + angle, 0, 0), major_segments=16, minor_segments=6)


def build_village(data, pal):
    t = data['giant_tree']
    bx, by, bz = t['base']
    top = bz + t['height']
    prim('cone', t['id'] + '_trunk', (bx, by, (bz + top) / 2), pal['bark'],
         vertices=14, radius1=t['radius'] * 1.5, radius2=t['radius'] * .65, depth=t['height'])
    for k in range(5):
        a = math.tau * k / 5 + .3
        root = prim('cone', t['id'] + '_root_%d' % k,
                    (bx + math.cos(a) * t['radius'] * 1.3, by + math.sin(a) * t['radius'] * 1.3, bz + 5),
                    pal['bark'], vertices=6, radius1=4.0, radius2=.5, depth=14)
        root.rotation_euler = (math.sin(a) * -.6, math.cos(a) * .6, 0)
    branches = []
    for k in range(7):
        a = math.tau * k / 7 + .9
        start = (bx, by, top - 14 + (k % 3) * 4)
        end = (bx + math.cos(a) * t['canopy_radius'] * .7,
               by + math.sin(a) * t['canopy_radius'] * .5, top + 4 + (k % 2) * 6)
        tube(t['id'] + '_branch_%d' % k, [start, end], pal['bark'], 2.0)
        branches.append(end)
    crown = [(bx, by + 6, top + 8, t['canopy_radius'] * .55, 1.25, 1.0, .7, 0)]
    for k, (x, y, z) in enumerate(branches):
        crown.append((x, y, z + 2, t['canopy_radius'] * (.30 + .06 * (k % 3)), 1.2, 1.0, .75, k % 2))
    for k in range(14):
        a = math.tau * k / 14
        crown.append((bx + math.cos(a) * t['canopy_radius'] * .6, by + 8 + math.sin(a) * t['canopy_radius'] * .45,
                      top + 12 + (k % 3) * 3, t['canopy_radius'] * .24, 1.1, 1.0, .85, (k + 1) % 2))
    blob_field(t['id'] + '_canopy', crown, [pal['canopy'], pal['canopy_light']])

    # Spiral walkway wrapped around the trunk up to a ring deck, as painted.
    sp = data['spiral']
    sx, sy = sp['center']
    run = math.hypot(math.tau * sp['radius'] * sp['turns'], sp['z1'] - sp['z0'])
    stations = geo.spiral_steps(sx, sy, sp['radius'], sp['z0'], sp['z1'], sp['turns'], int(run / 1.9))
    steps = [(pos, tangent, 4.4, 2.1, .5, 0) for pos, tangent in stations]
    for k, (pos, _) in enumerate(stations[::6]):
        steps.append(((pos[0], pos[1], (pos[2] + bz) / 2), (0, 0, 1), .7, pos[2] - bz, .7, 1))
    ring = 44
    for k in range(ring):
        a = math.tau * (k + .5) / ring
        steps.append(((sx + sp['radius'] * math.cos(a), sy + sp['radius'] * math.sin(a), sp['deck_z']),
                      (-math.sin(a), math.cos(a), 0), 5.2, math.tau * sp['radius'] / ring * 1.04, .6, 0))
    boxes(sp['id'], steps, [pal['plank'], pal['wood']])
    rail = [(sx + (sp['radius'] + 2.1) * math.cos(math.atan2(p[1] - sy, p[0] - sx)),
             sy + (sp['radius'] + 2.1) * math.sin(math.atan2(p[1] - sy, p[0] - sx)), p[2] + 1.7)
            for p, _ in stations[::3]]
    tube(sp['id'] + '_rail', rail, pal['rope'], .14)
    tube(sp['id'] + '_deck_rail',
         [(sx + (sp['radius'] + 2.5) * math.cos(math.tau * k / 48),
           sy + (sp['radius'] + 2.5) * math.sin(math.tau * k / 48), sp['deck_z'] + 1.7) for k in range(49)],
         pal['rope'], .14)

    for hut in data['huts']:
        x, y, z = hut['deck']
        s = hut['size']
        prim('cylinder', hut['id'] + '_deck', (x, y, z), pal['wood'], vertices=14, radius=s * 1.15, depth=1.2)
        posts = []
        for k in range(6):
            a = math.tau * k / 6
            px, py = x + math.cos(a) * s * 1.0, y + math.sin(a) * s * 1.0
            posts.append(((px, py, (z + 10) / 2), (0, 0, 1), 1.0, z - 10, 1.0, 0))
            posts.append(((px, py, z + 1.5), (0, 0, 1), .4, 3, .4, 0))
        boxes(hut['id'] + '_posts', posts, [pal['wood']])
        prim('cylinder', hut['id'] + '_walls', (x, y, z + s * .33), pal['hut_wall'],
             vertices=10, radius=s * .62, depth=s * .62)
        roof_z = z + s * .64
        prim('cone', hut['id'] + '_thatch_skirt', (x, y, roof_z + s * .12), pal['thatch'],
             vertices=12, radius1=s * 1.08, radius2=s * .45, depth=s * .32)
        prim('cone', hut['id'] + '_thatch_roof', (x, y, roof_z + s * .5), pal['thatch'],
             vertices=12, radius1=s * .62, radius2=.2, depth=s * .62)
        if hut['tiers'] > 1:
            prim('cylinder', hut['id'] + '_upper_walls', (x, y, roof_z + s * .55), pal['hut_wall'],
                 vertices=10, radius=s * .38, depth=s * .4)
            prim('cone', hut['id'] + '_upper_roof', (x, y, roof_z + s * 1.0), pal['thatch'],
                 vertices=12, radius1=s * .62, radius2=.2, depth=s * .55)
        prim('cube', hut['id'] + '_door', (x, y - s * .6, z + s * .25), pal['dark'],
             size=1).dimensions = (s * .22, .4, s * .38)


def build_walkways(data, pal):
    for w in data['walkways']:
        a, b = (Vector(p) for p in tilt_hex_points(data, (w['from'], w['to'])))
        d = b - a
        length = d.length
        items = []
        if w['kind'] in ('rope', 'plank'):
            count = max(6, int(length / 1.7))
            for k in range(count):
                t = (k + .5) / count
                sag = -1.6 * math.sin(math.pi * t) if w['kind'] == 'rope' else 0
                c = a + d * t + Vector((0, 0, sag))
                items.append((tuple(c), tuple(d), 3.4, length / count * .78, .35, 0))
            boxes(w['id'], items, [pal['plank']])
            if w['kind'] == 'rope':
                side = d.cross(Vector((0, 0, 1))).normalized() * 1.9
                for sgn in (-1, 1):
                    rail = [tuple(a + d * (k / 12) + side * sgn +
                                  Vector((0, 0, 1.8 - 1.6 * math.sin(math.pi * k / 12))))
                            for k in range(13)]
                    tube(w['id'] + '_rope_%d' % sgn, rail, pal['rope'], .12)
        elif w['kind'] == 'stairs':
            flat_d = Vector((d.x, d.y, 0))
            count = max(5, int(abs(d.z) / .9))
            for k in range(count):
                t = (k + .5) / count
                c = a + d * t
                items.append((tuple(c), tuple(flat_d), 4.2, flat_d.length / count * 1.05, .6, 0))
            boxes(w['id'], items, [pal['plank']])
            side = flat_d.cross(Vector((0, 0, 1))).normalized() * 2.2
            for sgn in (-1, 1):
                tube(w['id'] + '_rail_%d' % sgn,
                     [tuple(a + side * sgn + Vector((0, 0, 1.6))), tuple(b + side * sgn + Vector((0, 0, 1.6)))],
                     pal['rope'], .14)
        elif w['kind'] == 'checker':
            count = max(4, int(length / 3.0))
            for k in range(count):
                t = (k + .5) / count
                c = a + d * t - Vector((0, 0, .8))
                items.append((tuple(c), tuple(d), 3.6, length / count, 1.8, k % 2))
            boxes(w['id'], items, [pal['grass'], pal['cliff']])


def build_props(data, pal):
    for c in data['clouds']:
        x, y, z = c['center']
        r = c['radius']
        blob_field(c['id'], [(x + dx * r, y + dy * r, z, r * s, 1.2, 1.0, .55, 0)
                             for dx, dy, s in ((0, 0, .8), (.7, .2, .6), (-.6, .3, .6), (.1, .6, .55))],
                   [pal['cloud']], 2)
    for k, (x, y, z) in enumerate(data['springs']):
        prim('cylinder', 'spring_%d_base' % k, (x, y, z + .5), pal['spring_base'], vertices=12, radius=1.8, depth=1.0)
        prim('cylinder', 'spring_%d_pad' % k, (x, y, z + 1.2), pal['spring_top'], vertices=12, radius=1.9, depth=.5)
    sx, sy, sz = data['start']
    prim('cylinder', 'start_pad', (sx, sy, sz + .4), pal['spring_top'], vertices=20, radius=5, depth=.8)
    prim('torus', 'start_glow', (sx, sy, sz + .9), pal['pad_glow'], major_radius=5.2, minor_radius=.35)
    gx, gy, gz = data['goal']
    prim('cylinder', 'goal_pad', (gx, gy, gz + .5), pal['spring_top'], vertices=20, radius=6, depth=1.0)
    prim('torus', 'goal_glow', (gx, gy, gz + 1.1), pal['pad_glow'], major_radius=6.2, minor_radius=.4)
    prim('torus', 'goal_ring_arch', (gx, gy, gz + 8), pal['gold'], major_radius=6.5, minor_radius=.7,
         rotation=(math.pi / 2, 0, 0))


def build_canyon_details(data, pal):
    """Wooden stilt decks and raised water channels feeding the falls."""
    basin = next(p['z'] for p in data['pools'] if p['id'] == 'canyon_basin_water')
    for d in data['platforms']:
        x, y, z = d['deck']
        s = d['size']
        prim('cylinder', d['id'], (x, y, z), pal['wood'], vertices=10, radius=s, depth=1.0)
        posts = []
        for k in range(4):
            a = math.tau * (k + .5) / 4
            px, py = x + math.cos(a) * s * .75, y + math.sin(a) * s * .75
            posts.append(((px, py, (z + basin) / 2), (0, 0, 1), .8, z - basin, .8, 0))
        posts.append(((x + s * .3, y, z + 1.3), (1, 0, 0), 1.6, 1.6, 1.6, 1))   # crate
        boxes(d['id'] + '_posts', posts, [pal['wood'], pal['plank']])
    for c in data['channels']:
        a, b = Vector(c['from']), Vector(c['to'])
        d = b - a
        w = c['width']
        boxes(c['id'], [(tuple((a + b) / 2 + Vector((0, 0, .35))), tuple(d), w, d.length, .7, 0),
                        (tuple((a + b) / 2 + d.cross(Vector((0, 0, 1))).normalized() * (w / 2 + .6)
                               + Vector((0, 0, .9))), tuple(d), 1.2, d.length, 1.8, 1),
                        (tuple((a + b) / 2 - d.cross(Vector((0, 0, 1))).normalized() * (w / 2 + .6)
                               + Vector((0, 0, .9))), tuple(d), 1.2, d.length, 1.8, 1)],
              [pal['water'], pal['cliff']])


def build_items(data, pal):
    """Item monitors and bonus stars (original designs, painting props)."""
    for k, (x, y, z) in enumerate(data['monitors']):
        boxes('monitor_%d' % k, [((x, y, z + 1.6), (0, 1, 0), 2.6, 2.4, 3.0, 0),
                                 ((x, y - 1.25, z + 1.9), (0, 1, 0), 1.9, .12, 1.7, 1)],
              [pal['monitor'], pal['screen']])
        prim('torus', 'monitor_%d_icon' % k, (x, y - 1.36, z + 1.9), pal['gold'],
             major_radius=.55, minor_radius=.14, rotation=(math.pi / 2, 0, 0),
             major_segments=12, minor_segments=4)
    loc = Vector(MAP_CAMERA['location'])
    for k, (x, y, z) in enumerate(data['stars']):
        to_cam = loc - Vector((x, y, z))
        tilt = Matrix.Translation((x, y, z)) @ Matrix.Rotation(
            -math.atan2(to_cam.z, -to_cam.y), 4, 'X') @ Matrix.Translation((-x, -y, -z))
        v, f, m = geo.star_prism(x, y, z, 2.6, 1.1, .6)
        mesh('bonus_star_%d' % k, [tuple(tilt @ Vector(p)) for p in v], f, [pal['star']], m)


def build_rings_and_routes(data, pal):
    overlay = bpy.data.collections.new(OVERLAY)
    bpy.context.scene.collection.children.link(overlay)
    for route in data['routes']:
        pts = [tuple(p[k] + (1.6 if k == 2 else 0) for k in range(3))
               for p in tilt_hex_points(data, route['points'])]
        curve = geo.catmull_rom(pts, 6)
        if route['kind'] == 'main':
            tube('route_' + route['id'], curve, pal['route'], 1.05, overlay)
            for k, (pos, direction) in enumerate(geo.sample_along(curve, 26, 13)):
                arrow = prim('cone', 'route_arrow_%02d' % k, pos, pal['route'],
                             vertices=8, radius1=2.8, radius2=0, depth=4.6)
                arrow.rotation_euler = Vector(direction).to_track_quat('Z', 'Y').to_euler()
                bpy.context.scene.collection.objects.unlink(arrow)
                overlay.objects.link(arrow)
        else:
            dots = [(p[0], p[1], p[2], .8, 1, 1, 1, 0) for p, _ in geo.sample_along(curve, 3.2)]
            blob_field('route_' + route['id'] + '_dots', dots, [pal['alt_route']], 1, overlay)
            end, direction = geo.sample_along(curve, geo.polyline_length(curve) - .1)[-1]
            arrow = prim('cone', 'route_' + route['id'] + '_arrow', end, pal['alt_route'],
                         vertices=8, radius1=1.6, radius2=0, depth=3.0)
            arrow.rotation_euler = Vector(direction).to_track_quat('Z', 'Y').to_euler()
            bpy.context.scene.collection.objects.unlink(arrow)
            overlay.objects.link(arrow)
    # Ring rows: groups of four along the main route, facing the viewer.
    main = geo.catmull_rom([tuple(p[k] + (3.4 if k == 2 else 0) for k in range(3))
                            for p in tilt_hex_points(data, data['routes'][0]['points'])], 6)
    marks = geo.sample_along(main, 3.6, 6)
    count = 0
    for k, (pos, _) in enumerate(marks):
        if (k // 4) % 3 == 1:   # 4 rings, gap of 8 slots
            prim('torus', 'ring_%03d' % k, pos, pal['gold'], major_radius=1.6, minor_radius=.36,
                 rotation=(math.pi / 2, 0, 0), major_segments=14, minor_segments=6)
            count += 1
    return count


def surface_top(data, x, y):
    for item in data['terraces'] + data['islands']:
        cx, cy = item['center']
        w, d = item['size']
        if abs(x - cx) <= w / 2 - 2 and abs(y - cy) <= d / 2 - 2:
            return item['top']
    return None


def build_vegetation(data, pal):
    palms = 0
    for item in data['terraces'] + data['islands']:
        if item['id'] in ('canyon_floor', 'village_floor'):
            continue
        cx, cy = item['center']
        w, d = item['size']
        n = 1 if w * d < 500 else (2 if w * d < 1500 else 4)
        for k in range(n):
            x = cx + (rnd(item['id'], k) - .5) * (w - 8)
            y = cy + (rnd(item['id'], k + 9) - .5) * (d - 8)
            palm('palm_%s_%d' % (item['id'], k), x, y, item['top'], 11 + 7 * rnd(item['id'], k + 20), pal)
            palms += 1
    # Huge framing palms in the foreground, like the painting's corners.
    for k, (x, y, z, h, lean) in enumerate(((-172, -40, -30, 62, .35), (-138, -26, -22, 44, -.2),
                                            (60, -52, -40, 66, -.25), (150, -30, -30, 58, .2),
                                            (178, 40, -26, 50, .3))):
        palm('foreground_palm_%d' % k, x, y, z, h, pal, lean)
        palms += 1
    # Bushes hugging terrace and island rims, as in Entry Hills.
    bushes = []
    for item in data['terraces'] + data['islands']:
        if item['id'] in ('canyon_floor',):
            continue
        poly = geo.rounded_rect(*item['center'], *item['size'], 3)
        for k in range(0, len(poly), 2):
            if rnd(item['id'] + 'bush', k) < .45:
                continue
            x, y = poly[k]
            cx, cy = item['center']
            x, y = x + (cx - x) * .08, y + (cy - y) * .08
            r = 1.6 + 1.4 * rnd(item['id'] + 'br', k)
            bushes.append((x, y, item['top'] + r * .45, r, 1.2, 1.2, .8, 0))
    blob_field('rim_bushes', bushes, [pal['bush']], 2)
    # Dense jungle under the cliffs (left, right and foreground band); the
    # centre stays open over the cloud sea like the painting.
    jungle = []
    step = 9
    for gx in range(-260, 300, step):
        for gy in range(-90, 360, step):
            if -40 < gx < 125 and 62 < gy < 250:
                continue
            j = rnd('jungle', gx * 1000 + gy)
            jungle.append((gx + (j - .5) * 6, gy + (rnd('jy', gx + gy * 7) - .5) * 6,
                           JUNGLE_Z + j * 9, 5 + j * 4, 1.0, 1.0, .85, int(j * 10) % 2))
    blob_field('jungle_canopy', jungle, [pal['jungle'], pal['jungle_light']], 2)
    for k in range(36):
        x = -250 + rnd('jpx', k) * 540
        y = -80 + rnd('jpy', k) * 420
        if -40 < x < 125 and 62 < y < 250:
            continue
        palm('jungle_palm_%02d' % k, x, y, JUNGLE_Z + 4, 18 + 10 * rnd('jph', k), pal)
        palms += 1
    # Cloud sea in the centre, below the sky bridges and hex loop.
    sea = []
    for gx in range(-44, 130, 8):
        for gy in range(58, 256, 8):
            j = rnd('sea', gx * 997 + gy)
            if j < .7:
                continue          # blue gaps between cloud banks
            x, y = gx + (j - .5) * 5, gy + (rnd('sy', gx + gy) - .5) * 5
            sea.append((x, y, CLOUD_SEA_Z + j * 7, 5 + j * 4, 1.6, 1.3, .6, 0))
            # Billowing cumulus puffs on top of each bank, as painted.
            for q in range(3):
                a = math.tau * rnd('puff', gx * 31 + gy * 17 + q)
                sea.append((x + math.cos(a) * 4, y + math.sin(a) * 3,
                            CLOUD_SEA_Z + j * 7 + 2.5 + q, 2.2 + 1.4 * rnd('pr', gx + gy + q),
                            1.0, 1.0, .8, 0))
    blob_field('cloud_sea', sea, [pal['cloud']], 2)
    # Deep painted-blue void below the cloud banks (the painting's centre).
    poly = geo.rounded_rect(42, 150, 220, 260, 30)
    v, f, m = geo.prism(poly, -78, -80)
    mesh('sky_abyss', v, f, [pal['abyss']] * 3, m)
    return palms


def build_backdrop(data, pal):
    """Painted-map backdrop. The reference camera looks down ~44 degrees, so
    (like the painting) the horizon is staged: a camera-facing sky panel,
    a low distant mountain range and far jungle hills fill the top band."""
    cam = MAP_CAMERA
    loc, target = Vector(cam['location']), Vector(cam['target'])
    forward = (target - loc).normalized()
    panel_centre = loc + forward * 1150
    bpy.ops.mesh.primitive_plane_add(size=1, location=panel_centre)
    panel = bpy.context.object
    panel.name = 'backdrop_sky_panel'
    panel.rotation_euler = (-forward).to_track_quat('Z', 'Y').to_euler()
    panel.scale = (1500, 1100, 1)
    panel.data.materials.append(pal['sky_panel'])
    panel['stage_role'] = 'concept_v4_visual_only'
    panel.visible_shadow = False
    v, f, m = geo.mountain_range(-560, 620, 470, -118, 26, seed=11, scale=.45)
    mesh('backdrop_mountains', v, f, [pal['mountain'], pal['snow']], m)
    hills = []
    for k in range(64):
        x = -520 + k * 18
        j = rnd('hill', k)
        hills.append((x, 360 + j * 70, -92 + j * 22, 16 + j * 14, 1.5, 1.0, .9, k % 2))
    blob_field('backdrop_jungle_hills', hills, [pal['far_hill'], pal['jungle']], 1)
    for k, (x, y, z, h) in enumerate(((-210, 380, -44, 46), (-120, 420, -50, 40), (250, 400, -40, 50))):
        mesh('backdrop_falls_%d' % k, [(x - 3, y, z), (x + 3, y, z), (x + 4, y - 1, z - h), (x - 4, y - 1, z - h)],
             [(3, 2, 1, 0)], [pal['falls']])
    sky = []
    for k in range(30):
        j = rnd('sky', k)
        sky.append((-600 + k * 42 + j * 30, 640 + j * 100, -50 + rnd('skz', k) * 60,
                    22 + j * 22, 2.6, 1.0, .5, 0))
    blob_field('sky_clouds', sky, [pal['cloud']], 2)


HUD = 'MAP_HUD'
HUD_DEPTH = 10.0


def build_map_hud(data, pal, cam):
    """Map title, numbered region labels, START/GOAL tags and legend, laid
    out at the painting's measured image positions. Parented to the
    reference camera and only rendered in the map shot (text is the
    project's own wording; no logo or painting pixels)."""
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    hud = bpy.data.collections.new(HUD)
    scene.collection.children.link(hud)
    hw = HUD_DEPTH * (cam.data.sensor_width / 2) / cam.data.lens
    hh = hw * data['render']['height'] / data['render']['width']

    def at(u, v):
        return Vector(((u - .5) * 2 * hw, (.5 - v) * 2 * hh))

    def attach(obj, xy, layer):
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        hud.objects.link(obj)
        obj['stage_role'] = 'concept_v4_map_overlay'
        obj.parent = cam
        obj.location = (xy.x, xy.y, -HUD_DEPTH + layer * .004)
        for flag in ('visible_shadow', 'visible_diffuse', 'visible_glossy',
                     'visible_transmission', 'visible_volume_scatter'):
            setattr(obj, flag, False)
        return obj

    def text(body, size, xy, mat, align='CENTER', layer=3):
        curve = bpy.data.curves.new('hud_text', 'FONT')
        curve.body = body
        curve.size = size
        curve.align_x = align
        curve.align_y = 'CENTER'
        curve.materials.append(mat)
        return attach(bpy.data.objects.new('HUD_' + body[:24], curve), xy, layer)

    def rect(name, xy, w, h, mat, layer):
        v = [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)]
        return attach(mesh('HUD_' + name, v, [(0, 1, 2, 3)], [mat]), xy, layer)

    def disc(name, xy, r, mat, layer, n=20):
        v = [(r * math.cos(math.tau * k / n), r * math.sin(math.tau * k / n), 0) for k in range(n)]
        return attach(mesh('HUD_' + name, v, [tuple(range(n))], [mat]), xy, layer)

    def width(obj):
        bpy.context.view_layer.update()
        return obj.dimensions.x

    def panel(name, xy, w, h):
        rect(name + '_border', xy, w + .05, h + .05, pal['hud_border'], 0)
        rect(name + '_plate', xy, w, h, pal['hud_plate'], 1)

    # Title (top-left), gold with a dark drop shadow like a printed map.
    o = data['overlay']
    t = at(*o['title_uv'])
    text(o['title'], .25, t, pal['hud_title'], layer=3)
    text(o['title'], .25, t + Vector((.02, -.02)), pal['hud_dark'], layer=2)
    sub = t + Vector((0, -.27))
    strip = text(o['subtitle'], .11, sub, pal['hud_text'], layer=3)
    rect('subtitle_strip', sub, width(strip) + .3, .2, pal['hud_plate'], 1)

    # Numbered region labels with their painted notes.
    for r in data['regions']:
        c = at(*r['label_uv'])
        title = text(r['title'], .17, c, pal['hud_text'], 'LEFT')
        notes = [text('• ' + n, .085, c, pal['hud_text'], 'LEFT') for n in r['notes']]
        w = max([width(title) + .32] + [width(n) for n in notes]) + .26
        h = .34 + .125 * len(notes)
        c.x = max(-hw + w / 2 + .06, min(hw - w / 2 - .06, c.x))   # stay in frame
        left, top = c.x - w / 2, c.y + h / 2
        title.location.x, title.location.y = left + .44, top - .17
        for k, n in enumerate(notes):
            n.location.x, n.location.y = left + .14, top - .36 - .125 * k
        panel('label_' + r['id'], c, w, h)
        badge = Vector((left + .2, top - .17))
        disc('badge_' + r['id'], badge, .15, pal['hud_gold'], 2)
        text(str(r['number']), .17, badge + Vector((0, .005)), pal['hud_dark'])

    # START / GOAL tags above the painted pads.
    for key, label in (('start', 'START'), ('goal', 'GOAL')):
        p = Vector(data[key]) + Vector((0, 0, 14))
        co = world_to_camera_view(scene, cam, p)
        xy = at(co.x, 1 - co.y)
        tag = text(label, .15, xy, pal['hud_text'])
        w = width(tag) + .24
        # Keep the tag fully inside the frame (START sits at the left edge).
        xy.x = max(-hw + w / 2 + .08, min(hw - w / 2 - .08, xy.x))
        xy.y = max(-hh + .25, min(hh - .25, xy.y))
        tag.location.x, tag.location.y = xy.x, xy.y
        rect(key + '_tag_border', xy, w + .05, .32, pal['hud_border'], 0)
        rect(key + '_tag', xy, w, .27, pal['hud_plate'], 1)

    # Legend (bottom-right).
    c = at(*o['legend_uv'])
    rows = (('route', 'Main Route (Start - Goal)'), ('alt', 'Alternate Route / Shortcut'),
            ('ring', 'Rings (examples)'), ('spring', 'Spring / Bounce'),
            ('cloud', 'Cloud Platform'), ('island', 'Floating Platform / Island'))
    w, h = 1.62, .42 + .16 * len(rows)
    panel('legend', c, w, h)
    left, top = c.x - w / 2, c.y + h / 2
    text('MAP LEGEND', .14, Vector((left + .14, top - .17)), pal['hud_title'], 'LEFT')
    for k, (kind, label) in enumerate(rows):
        y = top - .40 - .16 * k
        ix = left + .27
        if kind == 'route':
            rect('legend_route', Vector((ix - .03, y)), .26, .05, pal['hud_title'], 2)
            disc('legend_route_head', Vector((ix + .12, y)), .07, pal['hud_title'], 2, 3)
        elif kind == 'alt':
            for d in range(4):
                disc('legend_alt_%d' % d, Vector((ix - .14 + d * .09, y)), .025, pal['hud_violet'], 2)
        elif kind == 'ring':
            disc('legend_ring', Vector((ix, y)), .06, pal['hud_gold'], 2)
            disc('legend_ring_hole', Vector((ix, y)), .033, pal['hud_plate'], 3)
        elif kind == 'spring':
            disc('legend_spring', Vector((ix, y)), .06, pal['hud_pink'], 2)
        elif kind == 'cloud':
            for d, (dx, r) in enumerate(((-.07, .045), (0, .06), (.07, .045))):
                disc('legend_cloud_%d' % d, Vector((ix + dx, y)), r, pal['hud_text'], 2)
        else:
            rect('legend_island_side', Vector((ix, y - .02)), .2, .07, pal['hud_brown'], 2)
            rect('legend_island_top', Vector((ix, y + .03)), .22, .04, pal['hud_green'], 3)
        text(label, .075, Vector((left + .48, y)), pal['hud_text'], 'LEFT')
    return hud


def setup_world(data):
    world = bpy.data.worlds.new('Jade Gully painted sky')
    bpy.context.scene.world = world
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    bg = nodes.get('Background')
    coord = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (.50, .70, 1.0, 1)
    ramp.color_ramp.elements[1].position = .45
    ramp.color_ramp.elements[1].color = (.03, .12, .55, 1)
    links.new(coord.outputs['Generated'], sep.inputs[0])
    links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bg.inputs['Color'])
    # Bright painted sky for camera rays, but a dimmer fill so the sun can
    # carve the saturated shadows of the painting.
    path = nodes.new('ShaderNodeLightPath')
    strength = nodes.new('ShaderNodeMath')
    strength.operation = 'MULTIPLY_ADD'
    strength.inputs[1].default_value = .6
    strength.inputs[2].default_value = .4
    links.new(path.outputs['Is Camera Ray'], strength.inputs[0])
    links.new(strength.outputs['Value'], bg.inputs['Strength'])
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 300))
    sun = bpy.context.object
    sun.name = 'ART_Sun'
    sun.data.energy = 4.2
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(38), math.radians(-22), math.radians(-30))
    scene = bpy.context.scene
    scene.render.resolution_x = data['render']['width']
    scene.render.resolution_y = data['render']['height']
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = data['render']['samples']
    scene.cycles.transparent_max_bounces = 32   # overlapping soft cloud edges
    try:
        scene.cycles.use_denoising = True
    except AttributeError:
        pass
    scene.view_settings.view_transform = 'Standard'
    try:
        scene.view_settings.look = 'Medium High Contrast'
    except (TypeError, ValueError):
        pass
    scene.render.film_transparent = False


def camera(name, location, target, lens=None, ortho=None):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.object
    cam.name = name
    cam.rotation_euler = (Vector(target) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.clip_end = 5000
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho
    else:
        cam.data.lens = lens
    return cam


def create_cameras(data):
    cams = {
        # Reference framing of the approved painting (same aspect ratio).
        'map': camera('JG4_Painting_Reference', MAP_CAMERA['location'], MAP_CAMERA['target'],
                      lens=MAP_CAMERA['lens']),
        'top': camera('JG4_Top', (5, 140, 600), (5, 140, 0), ortho=400),
    }
    for region in data['regions']:
        x0, y0, x1, y1 = region['rect']
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        span = max(x1 - x0, y1 - y0)
        cams[region['id']] = camera('JG4_Region_' + region['id'],
                                    (cx - span * .15, cy - span * 1.05, 40 + span * .75),
                                    (cx, cy, 25), lens=32)
    # The hex is tilted toward the map camera: frame it along its own face
    # normal, far enough back that the whole tube and its rings fit.
    h = data['hex_loop']
    _, angle = hex_tilt_matrix(data)
    centre = Vector(h['center'])
    normal = Matrix.Rotation(angle, 4, 'X') @ Vector((0, -1, 0))
    eye = centre + normal * h['radius'] * 3.4 + Vector((-h['radius'] * .9, 0, 0))
    bpy.data.objects.remove(cams['hex_loop'])
    cams['hex_loop'] = camera('JG4_Region_hex_loop', tuple(eye), tuple(centre), lens=32)
    return cams


# ---------------------------------------------------------------- review
def load_pixels(path):
    import numpy as np
    image = bpy.data.images.load(str(path), check_existing=False)
    w, h = image.size
    px = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    bpy.data.images.remove(image)
    return px.reshape(h, w, 4)[:, :, :3]


def colour_shares(rgb):
    """Fractions of pixels in the painting's key colour families."""
    import numpy as np
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    families = {
        'green': (g >= r) & (g >= b) & (sat > .25),
        'blue': (b > r) & (b > g) & (sat > .25),
        'ochre_brown': (r > g) & (g > b) & (sat > .25),
        'white_cloud': (mn > .78) & (sat < .18),
    }
    shares = {k: float(v.mean()) for k, v in families.items()}
    shares['mean_saturation'] = float(sat.mean())
    shares['mean_value'] = float(mx.mean())
    return shares


def review(out, render_path):
    import numpy as np
    concept = load_pixels(CONCEPT_PNG)
    render = load_pixels(render_path)
    a, b = colour_shares(concept), colour_shares(render)
    keys = ('green', 'blue', 'ochre_brown', 'white_cloud')
    distance = sum(abs(a[k] - b[k]) for k in keys)

    def fit(img, height):
        h, w, _ = img.shape
        ys = (np.arange(height) * h / height).astype(int)
        width = int(w * height / h)
        xs = (np.arange(width) * w / width).astype(int)
        return img[ys][:, xs]

    height = 640
    left, right = fit(concept, height), fit(render, height)
    gap = np.ones((height, 12, 3), dtype=np.float32)
    combined = np.concatenate((left, gap, right), axis=1)
    rgba = np.concatenate((combined, np.ones((*combined.shape[:2], 1), dtype=np.float32)), axis=2)
    img = bpy.data.images.new('jade_v4_compare', combined.shape[1], combined.shape[0], alpha=False)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = str(out / 'jade-gully-v4-compare.png')
    img.file_format = 'PNG'
    img.save()
    return {'concept': a, 'render': b, 'family_share_l1_distance': distance,
            'note': 'colour-family shares only; NOT a perceptual or layout match score'}


# ---------------------------------------------------------------- main
def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(args) != 1:
        raise SystemExit('Usage: -- OUTPUT_DIRECTORY')
    out = Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    data = json.loads(DEFAULT.read_text(encoding='utf-8'))
    report = validate(data)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    pal = build_palette()
    build_ground(data, pal)
    report['pillars'] = build_pillars(data, pal)
    build_hex(data, pal)
    build_village(data, pal)
    build_walkways(data, pal)
    build_props(data, pal)
    build_canyon_details(data, pal)
    build_items(data, pal)
    report['rings'] = build_rings_and_routes(data, pal)
    report['palms'] = build_vegetation(data, pal)
    build_backdrop(data, pal)
    setup_world(data)
    cams = create_cameras(data)
    hud = build_map_hud(data, pal, cams['map'])
    required = ['hex_loop_main', 'village_giant_tree_trunk', 'village_main_hut_thatch_roof',
                'entry_grass_arch', 'island_sky_a', 'terrace_canyon_goal', 'goal_ring_arch',
                'cloud_sea', 'backdrop_mountains', 'route_main', 'hill_lawn_west',
                'slope_lawn_upper', 'village_spiral_stair', 'channel_goal', 'canyon_deck_a',
                'monitor_0', 'bonus_star_0', 'HUD_label_entry_hills_plate', 'HUD_legend_plate']
    missing = [n for n in required if n not in bpy.data.objects]
    if missing:
        raise RuntimeError('Incomplete painting reconstruction: ' + ', '.join(missing))
    report['blender_version'] = bpy.app.version_string
    report['mesh_object_count'] = sum(o.type == 'MESH' for o in bpy.data.objects)
    report['mesh_polygon_count'] = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    report['note'] = 'Offline render scene; NOT Saturn-exported triangles or gameplay'

    scene = bpy.context.scene
    overlay = bpy.data.collections[OVERLAY]

    def shoot(key, cam, with_overlay):
        overlay.hide_render = not with_overlay
        hud.hide_render = not (with_overlay and key == 'map')
        scene.camera = cam
        scene.render.filepath = str(out / ('jade-gully-v4-' + key + '.png'))
        bpy.ops.render.render(write_still=True)
        return scene.render.filepath

    import os
    quick = os.environ.get('JADE_V4_QUICK') == '1'   # map + comparison only
    map_png = shoot('map', cams['map'], True)
    if not quick:
        shoot('clean', cams['map'], False)
        shoot('top', cams['top'], True)
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.cycles.samples = min(32, data['render']['samples'])
    for region in ([] if quick else data['regions']):
        shoot(region['id'], cams[region['id']], False)
    scene.render.resolution_x, scene.render.resolution_y = data['render']['width'], data['render']['height']
    scene.cycles.samples = data['render']['samples']
    overlay.hide_render = False
    hud.hide_render = False
    scene.camera = cams['map']
    report['review'] = review(out, map_png)
    report['preview_files'] = (['jade-gully-v4-map.png', 'jade-gully-v4-clean.png', 'jade-gully-v4-top.png',
                                'jade-gully-v4-compare.png'] +
                               ['jade-gully-v4-%s.png' % r['id'] for r in data['regions']])
    (out / 'concept-v4-contract.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'jade_gully_act1_concept_v4.blend'))
    print('[jade v4] painting-faithful concept written to', out)
    print('[jade v4] colour-family L1 distance vs painting: %.3f' % report['review']['family_share_l1_distance'])


if __name__ == '__main__':
    main()
