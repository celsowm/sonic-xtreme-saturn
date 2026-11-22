"""Artist-authored environmental setpieces for the offline Blender concept.

This file is deliberately separate from the Saturn greybox exporters.
Geometry is original; no ripped mesh or texture is used.
"""
import math
from tools.jade_concept_geometry import mesa_mesh, ribbon_mesh, halfpipe_mesh


def decorate(data, materials, artist):
    """Build art-only objects using the main Blender generator's primitives."""
    import bpy

    terrain_z=lambda x,y: artist.at_z(x,y,data)
    # Checkerboard terraces frame each named region instead of one uniform wall.
    mesas=(
        ('base_garden',-56,70,18,15),
        ('base_lookout',55,87,16,15),
        ('ridge_north',-60,124,23,24),
        ('ridge_loop_buttress',58,188,25,22),
        ('bamboo_canopy_left',-62,229,19,17),
        ('bamboo_balcony',63,301,20,18),
        ('gully_high_bank',-62,337,26,25),
        ('gully_wide_bank',64,395,26,21),
        ('summit_mid',-58,438,22,21),
        ('summit_peak',56,481,23,22),
    )
    for name,x,y,radius,rise in mesas:
        base=terrain_z(x,y)-3.5
        verts,faces,indices=mesa_mesh(x,y,base,radius,rise)
        artist.mesh('scenic_mesa_'+name,verts,faces,
                    [materials['grass'],materials['checker_brown'],
                     materials['checker_green']],indices)
        artist.tree('mesa_palm_'+name,x+radius*.27,y-radius*.18,
                    base+rise,11+(len(name)%5)*2,materials)

    # Curved, actually three-dimensional bamboo slide meshes.
    for name,start,end,radius in (
        ('bamboo_halfpipe_main',(-12,211,49),(-3,297,88),6.5),
        ('bamboo_halfpipe_upper',(24,241,78),(3,291,88),4.4),
    ):
        verts,faces,indices=halfpipe_mesh(start,end,radius)
        artist.mesh(name+'_gutter',verts,faces,
                    [materials['bamboo'],materials['roof']],indices)
        for side in (-1,1):
            artist.line(name+'_rim_'+str(side),
                       [(start[0]+side*radius,start[1],start[2]+radius),
                        (end[0]+side*radius,end[1],end[2]+radius)],
                        materials['wood'],.24)

    # A river must read as WATER at a distance, not just a thin blue wire.
    river_xy=((37,320),(43,337),(47,351),(35,369),
              (28,384),(27,395),(17,410))
    river=[(x,y,terrain_z(x,y)+1.3) for x,y in river_xy]
    verts,faces=ribbon_mesh(river,5.3)
    artist.mesh('gully_current_broad_river',verts,faces,[materials['water']])
    for side in (-1,1):
        artist.line('gully_foam_bank_'+str(side),
                    [(x+side*5.5,y,z+.35) for x,y,z in river],
                    materials['foam'],.18)

    # One gigantic central canopy silhouette unifies the three huts.
    gx,gy=49,268
    ground=terrain_z(gx,gy)-5
    artist.cylinder('bamboo_ancient_worldtree_trunk',gx,gy,ground+32,
                    6.8,69,materials['wood'],12)
    for i in range(8):
        theta=math.tau*i/8
        x=gx+math.cos(theta)*16
        y=gy+math.sin(theta)*17
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=17,
                    location=(x,y,ground+74+(i%3)*4))
        obj=bpy.context.object
        obj.name='bamboo_ancient_worldtree_crown_%02d'%i
        obj.scale=(1.3,1.1,.59)
        obj.data.materials.append(materials['foliage'])
        obj['stage_role']='concept_visual_only'

    # The communications dish reads as a stronger opening landmark.
    bx,by=-48,39
    bz=terrain_z(bx,by)+12
    artist.cylinder('sonic_base_satellite_mast',bx,by,bz+4,
                    .65,9,materials['rock'],8)
    dish=artist.cone('sonic_base_satellite_dish',bx,by,bz+9,
                    6,2.1,materials['foam'])
    dish.rotation_euler[1]=-.38

    # Real red spring and item-monitor silhouettes rather than editor markers.
    for j in (2,5,10,15,20,23):
        x,y,z=data['routes'][0]['points'][j]
        artist.cylinder('spring_%02d_housing'%j,x+5,y,z+1,
                        2.3,1.5,materials['rock'],10)
        artist.cylinder('spring_%02d_red_cap'%j,x+5,y,z+1.95,
                        2.25,.45,materials['spring_red'],10)
    for j in (3,8,14,19):
        x,y,z=data['routes'][0]['points'][j]
        artist.box('monitor_%02d_case'%j,(x-5,y,z+1.8),
                   (3.3,3.3,3.6),materials['rock'])
        artist.box('monitor_%02d_screen'%j,(x-3.27,y,z+2),
                   (.21,2.5,2.4),materials['cyan'])

    # More rings along coherent route splines.
    for route in data['routes']:
        fractions=(.33,.66) if route['kind']=='risk' else (.25,.5,.75)
        for seg,(a,b) in enumerate(zip(route['points'],route['points'][1:])):
            for k,t in enumerate(fractions):
                x=a[0]+(b[0]-a[0])*t
                y=a[1]+(b[1]-a[1])*t
                z=a[2]+(b[2]-a[2])*t
                artist.ring('route_ring_%s_%02d_%d'%(route['id'],seg,k),
                            x,y,z+3.7,materials,radius=1.12)

    # Larger emerald goal landmark to communicate the final section.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=9,
                    location=(3,512,158))
    gem=bpy.context.object
    gem.name='jade_summit_emerald'
    gem.scale=(.8,.8,1.58)
    gem.data.materials.append(materials['emerald'])
    gem['stage_role']='concept_visual_only'
