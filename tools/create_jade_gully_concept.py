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
    # Exterior side walls: a broad near/far chess-pattern bank into the gorge.
    for side in (0,nx):
        for j in range(ny):
            top0=j*(nx+1)+side
            top1=(j+1)*(nx+1)+side
            a=verts[top0]; b=verts[top1]
            for k in range(2):
                z0a=a[2]-k*12; z0b=b[2]-k*12
                z1a=a[2]-(k+1)*12; z1b=b[2]-(k+1)*12
                base=len(verts)
                verts.extend(((a[0],a[1],z0a),(b[0],b[1],z0b),
                              (b[0],b[1],z1b),(a[0],a[1],z1a)))
                faces.append((base,base+1,base+2,base+3))
                index.append(2 if (j+k)%2 else 3)
    obj=mesh('sector_'+sector['id']+'_checker_landmass', verts, faces,
             (palette['grass'],palette['foliage'],palette['checker_green'],palette['checker_brown']), index)
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
                verts.append((x+r*math.sin(angle),y+layer,z+r*math.cos(angle)))
    for i in range(6):
        nxt=(i+1)%6
        a=2*i; b=2*nxt
        c=12+2*i; d=12+2*nxt
        faces.extend(((a,b,b+1,a+1),(c+1,d+1,d,c),
                      (a,c,d,b),(a+1,b+1,d+1,c+1)))
        indices.extend((i%2,1-i%2,2,2))
    mesh(ident+'_angular_checker_loop',verts,faces,
         [materials['checker_brown'],materials['checker_green'],materials['rock']],indices)
    for dx in (-radius*.75,radius*.75):
        box(ident+'_base_'+str(round(dx,1)),(x+dx,y,z-radius-3),
            (3,10,5),materials['rock'])


def walkway(name, p1, p2, material, plank_width=4):
    v=Vector(p2)-Vector(p1)
    length=v.length
    mid=(Vector(p1)+Vector(p2))*.5
    obj=box(name,mid,(plank_width,length,1.0),material)
    # Local +Y axis is the length of the bridge.
    obj.rotation_euler=v.to_track_quat('Y','Z').to_euler()
    for side in (-plank_width*.52,plank_width*.52):
        # Rail endpoints are offset perpendicular to the travel direction.
        perp=Vector((v.y,-v.x,0)).normalized()*side
        a=Vector(p1)+perp+Vector((0,0,1.8))
        b=Vector(p2)+perp+Vector((0,0,1.8))
        line(name+'_rail_'+str(round(side,2)),[a,b],material,.13)


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
    # Tree crowns above the huts signal dense canopy, not floating houses.
    for direction in range(5):
        theta=2*PI*direction/5
        xx=x+size*.85*math.cos(theta)
        yy=y+size*.85*math.sin(theta)
        cone(ident+'_leaf_'+str(direction),xx,yy,platform_z+16,size*.5,10,materials['foliage'])


def waterfall(ident, loc, size, materials):
    x,y,z=loc
    waterfall_width=size*.42
    mesh(ident+'_cascade',[(x-waterfall_width,y,z+size*.45),
                           (x+waterfall_width,y,z+size*.45),
                           (x+waterfall_width,y+size*.25,z-size),
                           (x-waterfall_width,y+size*.25,z-size)],
         [(0,1,2,3)],[materials['water']])
    cylinder(ident+'_pool',x,y+size*.30,z-size, size*.82,.6,materials['water'],14)
    for i in range(3):
        line(ident+'_whitewater_'+str(i),
             [(x+(i-1)*waterfall_width*.6,y,z+size*.4),
              (x+(i-1)*waterfall_width*.6,y+size*.21,z-size)],
             materials['foam'],.22)


def tree(name, x, y, ground, h, materials):
    cylinder(name+'_trunk',x,y,ground+h*.36,.75,h*.72,materials['wood'],6)
    for j in range(2):
        cone(name+'_foliage_'+str(j),x,y,ground+h*(.64+j*.17),
             4.4-j*.6,h*.52,materials['foliage'])


def ring(name, x, y, z, materials, radius=1.45):
    # Golden annulus in vertical XZ plane.
    verts=[]; faces=[]
    for i in range(10):
        theta=2*PI*i/10
        for r in (radius,radius*.67):
            verts.append((x+r*math.sin(theta),y,z+r*math.cos(theta)))
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
    # Slightly above flat ground, for bird's-eye camera annotations.
    return obj


def build_landmarks(data, materials):
    by_id={item['id']:item for item in data['landmarks']}
    for item in data['landmarks']:
        ident=item['id']; kind=item['kind']; x,y,z=item['position']; size=item['size']
        if kind=='hex_loop':
            hex_loop(ident,(x,y,z),size,materials)
        elif kind=='treehouse':
            treehouse(ident,(x,y,z),size,materials)
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
    huts=[by_id['bamboo_village_'+str(i)] for i in (1,2,3)]
    walkway('bamboo_suspension_bridge_12',huts[0]['position'],huts[1]['position'],materials['wood'])
    walkway('bamboo_suspension_bridge_23',huts[1]['position'],huts[2]['position'],materials['wood'])


def setup_camera_and_lighting(data, materials):
    world=bpy.context.scene.world
    world.use_nodes=True
    bg=world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value=(.42,.56,.72,1)
    bg.inputs['Strength'].default_value=.75
    bpy.ops.object.light_add(type='SUN',location=(0,120,220))
    sun=bpy.context.object
    sun.name='ART_Sun'
    sun.data.energy=2.5
    sun.rotation_euler=(math.radians(30),math.radians(-28),math.radians(20))
    # View from the side of progression, so +Y spans the panoramic frame.
    bpy.ops.object.camera_add(location=(260,-110,280))
    camera=bpy.context.object
    camera.name='Concept_Perspective'
    target=Vector((0,258,60))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO'
    camera.data.ortho_scale=650
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
    try:
        scene.render.engine='BLENDER_EEVEE_NEXT'
    except TypeError:
        try: scene.render.engine='BLENDER_EEVEE'
        except TypeError: scene.render.engine='BLENDER_WORKBENCH'
    scene.view_settings.view_transform='Standard'
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
        'rock':mat('canyon stone',(.24,.23,.20)),
        'wood':mat('bamboo wood',(.38,.22,.10)),
        'bamboo':mat('palm bamboo hut',(.69,.53,.24)),
        'roof':mat('roof thatch',(.52,.33,.11)),
        'water':mat('canyon stream cyan',(.025,.52,.68)),
        'foam':mat('mist and signage',(.90,.96,.92)),
        'gold':mat('rings and main route',(.98,.68,.06),.35),
        'purple':mat('hazard shortcuts',(.62,.18,.75)),
        'cyan':mat('exploration routes',(.08,.68,.88)),
        'route_grass':mat('main path terrain',(.33,.53,.15)),
        'bridge':mat('alternative path deck',(.43,.36,.17)),
    }
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
    # Canyon river current and a clearer water path between the waterfalls.
    water_route=[(39,336,30),(38,354,24),(23,373,22),(33,389,27),(16,402,38)]
    line('gully_current_river',water_route,palette['water'],2.6)
    for sector in data['sectors']:
        y=(sector['y_range'][0]+sector['y_range'][1])*.5
        label('sector_tag_'+sector['id'],sector['title'],
              (-sector['width']*.93,y,at_z(-sector['width']*.93,y,data)+25),palette,4.7)
    camera, top=setup_camera_and_lighting(data,palette)
    (out/'concept-contract.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'jade_gully_act1_concept.blend'))
    scene=bpy.context.scene
    for key,cam in (('isometric',camera),('top',top)):
        scene.camera=cam
        scene.render.filepath=str(out/('jade-gully-concept-'+key+'.png'))
        bpy.ops.render.render(write_still=True)
    scene.camera=camera
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'jade_gully_act1_concept.blend'))
    print('[jade concept] 5-sectors; offline editable Blender + 2 previews:',out)
    print('[jade concept] DOES NOT export to Saturn; gameplay/collision and sector LOD pending')

if __name__=='__main__':
    main()
