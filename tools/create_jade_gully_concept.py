"""Build the entire Jade Gully Act 1 concept as an editable Blender scene.

Offline 5-sector ART BLOCKOUT, intentionally not exported to the Saturn engine.
Requires Blender 4.x, not the LibSaturn Blender exporter.

  blender -b --factory-startup --python-exit-code 1 \\
    --python tools/create_jade_gully_concept.py -- build/jade-gully-concept

This does NOT replace tools/create_jade_gully_adventure.py or the Ymir baseline.
Geometry is original and parameterized by assets/levels/jade_gully_concept_v1.json.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validate_jade_concept import DEFAULT, validate
from tools import jade_concept_dressing, jade_concept_presentation

PI = math.pi


def mat(name, rgb, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.72
    bsdf.inputs['Metallic'].default_value = metallic
    return m



def textured(material, name, repeat=8):
    """Map already tracked, unmodified Kenney CC0 texture to concept material.

    Generated UV-space coordinates keep preview meshes texture-mapped without
    baking image data from the fan concept painting. Texture images get packed
    into the saved .blend, so the editable scene remains portable.
    """
    source = ROOT / 'assets/textures/jade-gully' / name
    if not source.is_file():
        raise FileNotFoundError('Missing vendored Kenney CC0 material: '+str(source))
    image = bpy.data.images.load(str(source), check_existing=True)
    image.pack()
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (repeat, repeat, repeat)
    coords = nodes.new('ShaderNodeTexCoord')
    bitmap = nodes.new('ShaderNodeTexImage')
    bitmap.image = image
    bitmap.interpolation = 'Closest'
    bitmap.extension = 'REPEAT'
    links.new(coords.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], bitmap.inputs['Vector'])
    links.new(bitmap.outputs['Color'], nodes.get('Principled BSDF').inputs['Base Color'])
    return material


def mesh(name, verts, faces, materials, assignments=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    for material in materials:
        data.materials.append(material)
    for i, poly in enumerate(data.polygons):
        poly.material_index = assignments[i] if assignments else 0
    obj['stage_role'] = 'concept_visual_only'
    return obj


def at_z(x, y, data):
    """Terrain height deterministic from path elevation plus lateral relief."""
    path = data['routes'][0]['points']
    a, b = path[0], path[-1]
    for i in range(len(path)-1):
        if path[i][1] <= y <= path[i+1][1]:
            a, b = path[i], path[i+1]
            break
    t = max(0, min(1, (y-a[1]) / (b[1]-a[1])))
    route_z = a[2] + (b[2]-a[2])*t
    center_x = a[0] + (b[0]-a[0])*t
    distance = abs(x-center_x)
    relief = 0.0 if distance <= 8 else 1.0 - math.exp(-(distance-8)/17)
    side = 17 if x < center_x else -8
    wave = 4.0 * math.sin(x*.077+y*.061) + 2.3*math.cos(x*.14-y*.045)
    zone = next((s['id'] for s in data['sectors'] if s['y_range'][0] <= y <= s['y_range'][1]), 'summit')
    if zone == 'ridges': side += 15
    if zone == 'bamboo': side += 8
    if zone == 'current' and x > 16: side -= 12
    if zone == 'summit': side += 12
    return route_z - 1.8 + relief*(side+wave)


def cylinder(name, x, y, z, radius, depth, material, vertices=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=depth, location=(x,y,z))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    obj['stage_role'] = 'concept_visual_only'
    return obj


def cone(name, x, y, z, radius, depth, material):
    bpy.ops.mesh.primitive_cone_add(vertices=9, radius1=radius, radius2=.2,
                                    depth=depth, location=(x,y,z))
    obj=bpy.context.object
    obj.name=name
    obj.data.materials.append(material)
    obj['stage_role'] = 'concept_visual_only'
    return obj


def box(name, center, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj=bpy.context.object
    obj.name=name
    obj.dimensions=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    obj['stage_role']='concept_visual_only'
    return obj


def line(name, points, material, radius=.28):
    curve=bpy.data.curves.new(name,'CURVE')
    curve.dimensions='3D'
    curve.resolution_u=1
    curve.bevel_depth=radius
    curve.bevel_resolution=2
    spline=curve.splines.new('POLY')
    spline.points.add(len(points)-1)
    for node, point in zip(spline.points, points):
        node.co=(*point,1)
    obj=bpy.data.objects.new(name,curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.materials.append(material)
    obj['stage_role']='concept_visual_only'
    return obj


def terrain(sector, data, palette):
    """Contiguous terrain, checker cliff faces, and a river-cut variation."""
    nx=data['render']['terrain_x_steps']
    ny=data['render']['terrain_y_steps_per_sector']
    y0,y1=sector['y_range']
    half=sector['width']
    verts=[]
    faces=[]
    index=[]
    for j in range(ny+1):
        y=y0 + (y1-y0)*j/ny
        for i in range(nx+1):
            x=-half + 2*half*i/nx
            verts.append((x,y,at_z(x,y,data)))
    for j in range(ny):
        for i in range(nx):
            n=j*(nx+1)+i
            faces.append((n,n+1,n+nx+2,n+nx+1))
            if (i<2 or i>=nx-2) and (j+i)%3==0:
                index.append(2)
            else:
                index.append(1 if (i+j)%5==0 else 0)
    # Instead of the former 2 huge vertical striped wall bands, tile the
    # exposed cliff into 4 checker tiers * 3 longitudinal cells per station.
    # This creates actual mesh-level contrasting squares that remain readable
    # even when a source texture wraps or appears too dark in the preview.
    cliff_tiers=4
    cliff_substeps=3
    cliff_depth=24.0
    for side in (0,nx):
        for j in range(ny):
            a=verts[j*(nx+1)+side]
            b=verts[(j+1)*(nx+1)+side]
            for sub in range(cliff_substeps):
                t0=sub/cliff_substeps
                t1=(sub+1)/cliff_substeps
                p0=tuple(a[k]+(b[k]-a[k])*t0 for k in range(3))
                p1=tuple(a[k]+(b[k]-a[k])*t1 for k in range(3))
                for tier in range(cliff_tiers):
                    d0=cliff_depth*tier/cliff_tiers
                    d1=cliff_depth*(tier+1)/cliff_tiers
                    n=len(verts)
                    verts.extend((
                        (p0[0],p0[1],p0[2]-d0),
                        (p1[0],p1[1],p1[2]-d0),
                        (p1[0],p1[1],p1[2]-d1),
                        (p0[0],p0[1],p0[2]-d1),
                    ))
                    faces.append((n,n+1,n+2,n+3))
                    index.append(2 if (j*cliff_substeps+sub+tier)%2 else 3)
    obj=mesh('sector_'+sector['id']+'_checker_landmass', verts, faces,
             (palette['grass'],palette['foliage'],palette['cliff_fern'],palette['cliff_ochre']), index)
    obj['concept_sector']=sector['id']
    return obj


def path_mesh(route, materials):
    points=route['points']
    verts=[]
    faces=[]
    width=3.8 if route['kind']=='main' else 2.8
    for i,(x,y,z) in enumerate(points):
        previous=points[max(0,i-1)]
        following=points[min(len(points)-1,i+1)]
        dx=following[0]-previous[0]
        dy=following[1]-previous[1]
        d=math.hypot(dx,dy)
        nx,ny=dy/d*width,-dx/d*width
        verts.extend(((x-nx,y-ny,z+.25),(x+nx,y+ny,z+.25)))
        if i:
            n=i*2
            faces.append((n-2,n-1,n+1,n))
    palette_name={'main':'route_grass','risk':'gold','explore':'bridge'}[route['kind']]
    obj=mesh('path_'+route['id'],verts,faces,[materials[palette_name]])
    obj['concept_route_kind']=route['kind']
    # Guide lines are visible in the editable art scene; no runtime paths.
    guide={'main':'gold','risk':'purple','explore':'cyan'}[route['kind']]
    line('guide_'+route['id'],[(x,y,z+.7) for x,y,z in points],materials[guide],.22)
    return obj


def hex_loop(ident, center, radius, materials):
    """Raised angular hex ring, readable from the isometric overview.

    It is a visual landmark ONLY: the current runtime does not implement
    gravity switching or loop-constrained player locomotion.
    """
    x,y,z=center
    verts=[]
    faces=[]
    indices=[]
    for layer in (0,7):
        for i in range(6):
            angle=2*PI*i/6+PI/6
            for r in (radius,radius*.70):
                verts.append((x+layer,y+r*math.sin(angle),z+r*math.cos(angle)))
    for i in range(6):
        nxt=(i+1)%6
        a=2*i; b=2*nxt
        c=12+2*i; d=12+2*nxt
        faces.extend(((a,b,b+1,a+1),(c+1,d+1,d,c),
                      (a,c,d,b),(a+1,b+1,d+1,c+1)))
        indices.extend((i%2,1-i%2,2,2))
    mesh(ident+'_angular_checker_loop',verts,faces,
         [materials['cliff_ochre'],materials['cliff_fern'],materials['rock']],indices)
    for dx in (-radius*.75,radius*.75):
        box(ident+'_base_'+str(round(dx,1)),(x,y+dx,z-radius-3),
            (10,3,5),materials['rock'])


def walkway(name, p1, p2, material, plank_width=4):
    """A segmented rope suspension bridge, not one featureless cube."""
    v=Vector(p2)-Vector(p1)
    length=v.length
    if length < 1:
        raise ValueError('bridge endpoints too close')
    mid=(Vector(p1)+Vector(p2))*.5
    deck=box(name+'_structural_deck',mid,(plank_width,length,.30),material)
    deck.rotation_euler=v.to_track_quat('Y','Z').to_euler()
    plank_count=max(8,int(length/2.0))
    for i in range(plank_count):
        t=(i+.5)/plank_count
        p=Vector(p1)+v*t+Vector((0,0,.22))
        plank=box(name+'_plank_%02d'%i,p,
                  (plank_width*.97,length/plank_count*.83,.23),material)
        plank.rotation_euler=deck.rotation_euler
    sideways=Vector((v.y,-v.x,0)).normalized()
    for side in (-1,1):
        offset=side*plank_width*.56
        cable=[]
        for i in range(17):
            t=i/16
            p=Vector(p1)+v*t+sideways*offset
            p.z += 2.7-1.0*math.sin(PI*t)
            cable.append(tuple(p))
        line(name+'_sagging_rope_'+str(side),cable,material,.15)
        for j in range(0,plank_count+1,max(2,plank_count//6)):
            t=j/plank_count
            foot=Vector(p1)+v*t+sideways*offset
            line(name+'_rope_post_%d_%d'%(side,j),
                 [tuple(foot),tuple(foot+Vector((0,0,2.5)))],material,.12)


def treehouse(ident, loc, size, materials):
    x,y,platform_z=loc
    ground=platform_z-size*3.2
    cylinder(ident+'_giant_tree',x,y,(ground+platform_z)/2,size*.33,
             platform_z-ground,materials['wood'])
    cylinder(ident+'_canopy_platform',x,y,platform_z,size*1.05,1.6,materials['wood'],12)
    cylinder(ident+'_hut_walls',x,y,platform_z+4,size*.62,7,materials['bamboo'],9)
    cone(ident+'_thatched_roof',x,y,platform_z+10,size*.95,7,materials['roof'])
    for direction in range(6):
        theta=direction*PI/3
        xx=x+(size*.94)*math.cos(theta)
        yy=y+(size*.94)*math.sin(theta)
        cylinder(ident+'_post_'+str(direction),xx,yy,platform_z+1.8,.2,4,materials['wood'],6)
    # Broad tropical canopy masses frame the elevated huts; the previous
    # pointed cones made the whole tree village look like a pine forest.
    for direction in range(6):
        theta=2*PI*direction/6
        xx=x+size*.90*math.cos(theta)
        yy=y+size*.90*math.sin(theta)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,
                                               radius=size*.44,
                                               location=(xx,yy,platform_z+size*2.02))
        obj=bpy.context.object
        obj.name=ident+'_broad_canopy_'+str(direction)
        obj.scale=(1.03,1.16,.60)
        obj.data.materials.append(materials['foliage'])
        obj['stage_role']='concept_visual_only'


def waterfall(ident, loc, size, materials):
    """Visible tiered falls in a YZ plane facing the panoramic camera."""
    x,y,z=loc
    half_width=size*.30
    top=z+size*.55
    bottom=z-size*.75
    for band in range(3):
        shift=(band-1)*half_width*.64
        fall_x=x+(band%2)*.6
        verts=[
            (fall_x,y+shift-half_width*.52,top),
            (fall_x,y+shift+half_width*.52,top),
            (fall_x+size*.19,y+shift+half_width*.52,bottom),
            (fall_x+size*.19,y+shift-half_width*.52,bottom),
        ]
        mesh(ident+'_water_curtain_'+str(band),verts,[(0,1,2,3)],
             [materials['water']])
        for j in (-1,0,1):
            river_y=y+shift+j*half_width*.19
            line(ident+'_fall_foam_%d_%d'%(band,j),
                 [(fall_x+.25,river_y,top-1),
                  (fall_x+size*.1,river_y+1,bottom+2)],
                 materials['foam'],.19)
    cylinder(ident+'_pool',x+size*.22,y,bottom+.5,
             size*.76,.75,materials['water'],18)
    for j in range(4):
        line(ident+'_pool_ripple_'+str(j),
             [(x+size*.22,y+size*.24*(j-2),bottom+1.1),
              (x+size*.38,y+size*.24*(j-2),bottom+1.2)],
             materials['foam'],.28)


def tree(name, x, y, ground, h, materials):
    """Tropical low-poly palm rather than the pointed pine placeholders.

    Broad radial fronds are a *single* indexed mesh per tree, suitable for
    later Saturn LOD reduction; the decorative tree has no game collision.
    """
    tilt=(sum(ord(c) for c in name)%5-2)*.17
    trunk=cylinder(name+'_trunk',x,y,ground+h*.46,.55+h*.014,h*.92,materials['wood'],7)
    trunk.rotation_euler[1]=tilt*.07
    top=(x+tilt,y,ground+h)
    verts=[]; faces=[]
    for blade in range(8):
        angle=2*PI*blade/8+(len(name)%7)*.11
        ux,uy=math.cos(angle),math.sin(angle)
        vx,vy=-uy,ux
        reach=h*(.41+(blade%3)*.035)
        spread=reach*.26
        z=top[2]
        k=len(verts)
        verts.extend((
            top,
            (top[0]+ux*reach*.37+vx*spread,top[1]+uy*reach*.37+vy*spread,z+.62),
            (top[0]+ux*reach,top[1]+uy*reach,z-reach*.33),
            (top[0]+ux*reach*.37-vx*spread,top[1]+uy*reach*.37-vy*spread,z+.62),
        ))
        faces.extend(((k,k+1,k+2),(k,k+2,k+3)))
    mesh(name+'_eight_fronds',verts,faces,[materials['foliage']])


def ring(name, x, y, z, materials, radius=1.45):
    # Golden annulus in vertical XZ plane.
    verts=[]; faces=[]
    for i in range(10):
        theta=2*PI*i/10
        for r in (radius,radius*.67):
            verts.append((x,y+r*math.sin(theta),z+r*math.cos(theta)))
    for i in range(10):
        j=(i+1)%10
        faces.append((2*i,2*j,2*j+1,2*i+1))
    mesh(name,verts,faces,[materials['gold']])


def label(name, content, location, materials, size=4):
    bpy.ops.object.text_add(location=location)
    obj=bpy.context.object
    obj.name=name
    obj.data.body=content
    obj.data.size=size
    obj.data.extrude=.04
    obj.data.materials.append(materials['foam'])
    obj['stage_role']='concept_editor_annotation'
    # Face the panorama camera later; annotation quads must never be edge-on.
    obj.data.align_x='CENTER'
    return obj


def build_landmarks(data, materials):
    by_id={item['id']:item for item in data['landmarks']}
    village_decks={}
    for item in data['landmarks']:
        ident=item['id']; kind=item['kind']; x,y,z=item['position']; size=item['size']
        if kind=='hex_loop':
            # The opening used to be buried below terrain and edge-on.
            loop_z=z+size*.72
            hex_loop(ident,(x,y,loop_z),size*1.10,materials)
            for j in range(9):
                t=(j+1)*PI/10
                ring(ident+'_gold_inner_'+str(j),x+9,
                     y+size*.76*math.sin(t),
                     loop_z+size*.76*math.cos(t),materials,radius=1.25)
        elif kind=='treehouse':
            # The original deck coordinates sometimes sat inside the terrain.
            # Lift only the visual concept deck, keeping manifest coordinates
            # intact for future gameplay sector authoring.
            deck=max(z,at_z(x,y,data)+size*1.45)
            village_decks[ident]=(x,y,deck)
            treehouse(ident,(x,y,deck),size,materials)
        elif kind=='waterfall':
            waterfall(ident,(x,y,z),size,materials)
        elif kind=='dome':
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,
                                                 radius=size,location=(x,y,z+size*.22))
            obj=bpy.context.object; obj.name=ident+'_base_dome'
            obj.scale.z=.65; obj.data.materials.append(materials['bamboo'])
            box(ident+'_door',(x,y-size*.8,z),(size*.2,size*.2,size*.8),materials['wood'])
        elif kind=='tower':
            cylinder(ident+'_tower',x,y,z+size*.6,size*.43,size*1.2,materials['wood'])
            cone(ident+'_roof',x,y,z+size*1.35,size*.7,size*.58,materials['roof'])
        elif kind=='goal':
            for side in (-1,1):
                cylinder(ident+'_pole_'+str(side),x+side*size*.75,y,z+size*.9,
                         .42,size*1.8,materials['rock'],8)
            for col in range(8):
                for row in range(4):
                    box(ident+'_flag_%d_%d'%(col,row),
                        (x-size*.69+(col+.5)*size*1.38/8,y,z+size*1.7+(row+.5)*size*.5/4),
                        (size*1.38/8,.26,size*.5/4),
                        materials['foam' if (col+row)%2==0 else 'rock'])
    # Two genuinely connected suspended walkways between the three houses.
    huts=[village_decks['bamboo_village_'+str(i)] for i in (1,2,3)]
    walkway('bamboo_suspension_bridge_12',huts[0],huts[1],materials['wood'])
    walkway('bamboo_suspension_bridge_23',huts[1],huts[2],materials['wood'])


def setup_camera_and_lighting(data, materials):
    world=bpy.data.worlds.new('Jade Gully Sky')
    bpy.context.scene.world=world
    world.use_nodes=True
    bg=world.node_tree.nodes.get('Background')
    # Soft sunset-to-blue background: actual world rays, not a flat gray
    # ambient that makes the render look like an unlit geometry screenshot.
    bg.inputs['Color'].default_value=(.42,.56,.72,1)
    bg.inputs['Strength'].default_value=.80
    nodes=world.node_tree.nodes
    links=world.node_tree.links
    direction=nodes.new('ShaderNodeTexCoord')
    vertical=nodes.new('ShaderNodeSeparateXYZ')
    sky_ramp=nodes.new('ShaderNodeValToRGB')
    sky_ramp.color_ramp.elements[0].position=0.0
    sky_ramp.color_ramp.elements[0].color=(.80,.56,.51,1)
    sky_ramp.color_ramp.elements[1].position=0.90
    sky_ramp.color_ramp.elements[1].color=(.26,.46,.72,1)
    sky_ramp.color_ramp.elements.new(.40).color=(.56,.65,.78,1)
    links.new(direction.outputs['Normal'],vertical.inputs[0])
    links.new(vertical.outputs['Z'],sky_ramp.inputs[0])
    links.new(sky_ramp.outputs['Color'],bg.inputs['Color'])
    bpy.ops.object.light_add(type='SUN',location=(0,120,220))
    sun=bpy.context.object
    sun.name='ART_Sun'
    sun.data.energy=3.1
    sun.rotation_euler=(math.radians(30),math.radians(-28),math.radians(20))
    # View from the side of progression, so +Y spans the panoramic frame.
    bpy.ops.object.camera_add(location=(445,98,340))
    camera=bpy.context.object
    camera.name='Concept_Perspective'
    target=Vector((0,258,60))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO'
    camera.data.ortho_scale=615
    bpy.context.scene.camera=camera
    bpy.ops.object.camera_add(location=(0,258,520))
    top=bpy.context.object
    top.name='Concept_Top_Layout'
    top.rotation_euler=(Vector((0,258,0))-top.location).to_track_quat('-Z','Y').to_euler()
    top.data.type='ORTHO'; top.data.ortho_scale=600
    scene=bpy.context.scene
    scene.render.resolution_x=data['render']['width']
    scene.render.resolution_y=data['render']['height']
    scene.render.resolution_percentage=65
    scene.render.image_settings.file_format='PNG'
    # CI runs without a physical GPU: CPU Cycles renders node textures
    # reliably in background mode, rather than requiring a GL/Eevee context.
    scene.render.engine='CYCLES'
    scene.cycles.samples=data['render']['samples']
    scene.cycles.device='CPU'
    scene.view_settings.view_transform='Standard'
    try:
        scene.view_settings.look='Medium High Contrast'
    except (TypeError,ValueError):
        pass
    scene.render.film_transparent=False
    return camera, top


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(args)!=1:
        raise SystemExit('Usage: -- OUTPUT_DIRECTORY')
    out=Path(args[0]).resolve(); out.mkdir(parents=True,exist_ok=True)
    data=json.loads(DEFAULT.read_text(encoding='utf-8'))
    report=validate(data)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    palette={
        'grass':mat('lush jade grass',(.19,.48,.11)),
        'foliage':mat('canopy emerald',(.045,.29,.09)),
        'checker_green':mat('Xtreme checker moss',(.21,.44,.16)),
        'checker_brown':mat('Xtreme checker sandstone',(.47,.24,.12)),
        'cliff_fern':mat('checker cliff vivid moss',(.16,.48,.16)),
        'cliff_ochre':mat('checker cliff warm sandstone',(.70,.38,.15)),
        'loop_border':mat('golden rim of the six-sided loops',(.94,.47,.07),.06),
        'warm_window':mat('warm glowing village windows',(1.0,.63,.19)),
        'rock':mat('canyon stone',(.24,.23,.20)),
        'wood':mat('bamboo wood',(.38,.22,.10)),
        'bamboo':mat('palm bamboo hut',(.69,.53,.24)),
        'roof':mat('roof thatch',(.52,.33,.11)),
        'water':mat('canyon stream cyan',(.025,.52,.68)),
        'foam':mat('mist and signage',(.90,.96,.92)),
        'gold':mat('rings and main route',(.98,.68,.06),.35),
        'spring_red':mat('springs — ruby red',(.89,.08,.07),.19),
        'emerald':mat('Summit emerald reward',(.05,.82,.36),.30),
        'purple':mat('hazard shortcuts',(.62,.18,.75)),
        'cyan':mat('exploration routes',(.08,.68,.88)),
        'route_grass':mat('main path terrain',(.33,.53,.15)),
        'bridge':mat('alternative path deck',(.43,.36,.17)),
    }
    # Reuse the real CC0 source images already checked into the repo.
    # These are not Sega rips and not generated from the concept art.
    for key, filename, repeats in (
        ('grass','meadow-grass.png',12),
        ('foliage','forest-leaves.png',6),
        ('checker_green','moss-bank.png',8),
        ('checker_brown','sandstone.png',8),
        ('rock','rock-grey.png',7),
        ('wood','sand-path.png',5),
        ('bamboo','sandstone.png',5),
        ('roof','moss-bank.png',4),
        ('water','waterfall.png',3),
        ('route_grass','grass-path.png',12),
        ('bridge','sandstone.png',5),
    ):
        textured(palette[key],filename,repeats)
    for sector in data['sectors']:
        terrain(sector,data,palette)
        y0,y1=sector['y_range']
        for j in range(11):
            y=y0+6+(y1-y0-12)*j/10
            for side in (-1,1):
                x=side*(sector['width']*.65 + (j%3)*5)
                tree('tree_'+sector['id']+'_'+str(j)+'_'+str(side),x,y,
                     at_z(x,y,data),9+(j%4)*3,palette)
    for route in data['routes']:
        path_mesh(route,palette)
        # Ring props are a visual note, NOT pickups/objects for the Saturn.
        for i in range(1,len(route['points'])-1,2):
            x,y,z=route['points'][i]
            ring('ring_'+route['id']+'_'+str(i),x,y,z+4,palette)
    build_landmarks(data,palette)
    jade_concept_dressing.decorate(data,palette,sys.modules[__name__])
    # Canyon river current and a clearer water path between the waterfalls.
    water_route=[(39,336,30),(38,354,24),(23,373,22),(33,389,27),(16,402,38)]
    line('gully_current_river',water_route,palette['water'],2.6)
    for sector in data['sectors']:
        y=(sector['y_range'][0]+sector['y_range'][1])*.5
        label('sector_tag_'+sector['id'],sector['title'],
              (sector['width']*.90,y,at_z(sector['width']*.90,y,data)+72),palette,9.0)
    presentation_report=jade_concept_presentation.apply_presentation(
        data,palette,sys.modules[__name__])
    # Fail the art build if a key recognizable object silently disappears.
    required_objects=(
        'ridge_hex_loop_angular_checker_loop',
        'bamboo_village_1_canopy_platform',
        'bamboo_suspension_bridge_12_structural_deck',
        'bamboo_halfpipe_main_gutter',
        'gully_current_broad_river',
        'current_falls_right_water_curtain_0',
        'jade_summit_emerald',
    )
    missing=[name for name in required_objects if name not in bpy.data.objects]
    if missing:
        raise RuntimeError('Incomplete five-region visual build: '+', '.join(missing))
    report['visual_pass']='tropical-landmark-visibility-v3'
    report['presentation']=presentation_report
    report['key_art_objects']=list(required_objects)
    report['mesh_object_count']=sum(obj.type=='MESH' for obj in bpy.data.objects)
    report['mesh_polygon_count']=sum(len(obj.data.polygons)
        for obj in bpy.data.objects if obj.type=='MESH')
    report['note']='Offline render scene; NOT Saturn-exported triangles or gameplay'
    camera, top=setup_camera_and_lighting(data,palette)
    for obj in bpy.data.objects:
        if obj.get('stage_role')=='concept_editor_annotation':
            # In the former render, all five labels looked like vertical noise.
            obj.rotation_euler=(camera.location-obj.location).to_track_quat('Z','Y').to_euler()
    # Reject a regression to the tiny 2-band cliff topology from the
    # screenshot: every sector must export its fully subdivided checker wall.
    nx=data['render']['terrain_x_steps']
    ny=data['render']['terrain_y_steps_per_sector']
    expected_faces=nx*ny + 2*ny*3*4
    terrain_faces={}
    for sector in data['sectors']:
        name='sector_'+sector['id']+'_checker_landmass'
        obj=bpy.data.objects.get(name)
        if obj is None or obj.type!='MESH':
            raise RuntimeError('Missing authored terrain: '+name)
        actual=len(obj.data.polygons)
        if actual!=expected_faces:
            raise RuntimeError(
                f'{name} has {actual} faces; checker terrain needs '
                f'{expected_faces} (including tiered canyon walls)')
        terrain_faces[sector['id']]=actual
    required=('gully_current_broad_river','bamboo_halfpipe_main_gutter',
              'bamboo_ancient_worldtree_trunk','jade_summit_emerald')
    missing=[name for name in required if name not in bpy.data.objects]
    if missing:
        raise RuntimeError('Missing art landmarks: '+', '.join(missing))
    report['blender_art_gate']={
        'checker_faces_per_sector': terrain_faces,
        'terrain_faces_total': sum(terrain_faces.values()),
        'required_landmarks': len(required),
        'visual_only': True,
    }
    region_cameras=jade_concept_presentation.create_region_cameras(
        data,sys.modules[__name__])
    report['preview_files']=[
        'jade-gully-concept-isometric.png',
        'jade-gully-concept-top.png',
    ]+['jade-gully-concept-'+sec['id']+'.png' for sec in data['sectors']]
    (out/'concept-contract.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    scene=bpy.context.scene
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'jade_gully_act1_concept.blend'))
    for key,cam in (('isometric',camera),('top',top)):
        scene.camera=cam
        scene.render.filepath=str(out/('jade-gully-concept-'+key+'.png'))
        bpy.ops.render.render(write_still=True)
    # Five lightweight close-ups make the loops, huts and waterfalls
    # inspectable without the wide view compressing them to tiny shapes.
    original=(scene.render.resolution_x,scene.render.resolution_y,
              scene.render.resolution_percentage,scene.cycles.samples)
    scene.render.resolution_x=1600
    scene.render.resolution_y=900
    scene.render.resolution_percentage=70
    scene.cycles.samples=min(18,original[3])
    for name,cam in region_cameras.items():
        scene.camera=cam
        scene.render.filepath=str(out/('jade-gully-concept-'+name+'.png'))
        bpy.ops.render.render(write_still=True)
    (scene.render.resolution_x,scene.render.resolution_y,
     scene.render.resolution_percentage,scene.cycles.samples)=original
    scene.camera=camera
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'jade_gully_act1_concept.blend'))
    print('[jade concept] 5 regions, editable Blender + 7 actual rendered previews:',out)
    print('[jade concept] DOES NOT export to Saturn; gameplay/collision and sector LOD pending')

if __name__=='__main__':
    main()
