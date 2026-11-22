"""Author a standalone, editable 50x70 m Jade Gully Tree Village Blender kit.

Run:
  blender --background --factory-startup --python-exit-code 1 \
    --python tools/create_tree_village_kit.py -- \
    assets/jade-gully/tree-village/kit-manifest.json build/tree-village [--preview]

This is a Blender ART SOURCE, not a new in-game level or Saturn streaming runtime.
The textures are original, procedurally painted here and PACKED into the .blend.
No extra Blender plugins, pip modules, or internet dependencies are required.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) not in (2, 3) or (len(args) == 3 and args[2] != "--preview"):
    raise SystemExit("usage: Blender --python tools/create_tree_village_kit.py -- MANIFEST OUT [--preview]")
MANIFEST = Path(args[0]).resolve()
OUT = Path(args[1]).resolve()
PREVIEW = len(args) == 3
data = json.loads(MANIFEST.read_text(encoding="utf-8"))
assert data["schema_version"] == 1 and data["axes"] == "RH_Z_UP" and data["units"] == "m"
assert data["runtime_status"] == "blender_authoring_only"
OUT.mkdir(parents=True, exist_ok=True)
TEX = OUT / "textures"
TEX.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100

COLLECTIONS = {}
for name in ("JG_TERRAIN", "JG_TREE_VILLAGE_CORE", "JG_TREE_VILLAGE_DECOR",
             "JG_BILLBOARDS", "JG_COLLISION", "JG_HELPERS", "JG_REFERENCE"):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    COLLECTIONS[name] = c


def create_image(name, paint):
    img = bpy.data.images.new(name, width=64, height=64, alpha=True)
    pixels = []
    for y in range(64):
        for x in range(64):
            pixels.extend(paint(x, y))
    img.pixels.foreach_set(pixels)
    img.filepath_raw = str(TEX / (name + ".png"))
    img.file_format = "PNG"
    img.save()
    img.pack()
    return img


def palm_pixel(x, y):
    # Hand-authored raster palm silhouette: brown curving trunk, green fronds,
    # transparent surroundings. No proprietary sprite sheets.
    cx = 31.5 + 1.2 * math.sin(y / 10.0)
    if 4 <= y < 45 and abs(x - cx) < 3.3:
        return (.34, .20, .08, 1.)
    origin = (32., 43.)
    tips = ((2, 32), (6, 55), (20, 63), (44, 63),
            (58, 55), (62, 32), (4, 43), (60, 43), (16, 55), (48, 55))
    for a, b in tips:
        vx, vy = a - origin[0], b - origin[1]
        t = ((x - origin[0]) * vx + (y - origin[1]) * vy) / (vx * vx + vy * vy)
        if 0 <= t <= 1:
            dist = abs((x - origin[0]) * vy - (y - origin[1]) * vx) / math.hypot(vx, vy)
            if dist < max(1.2, 8.5 * (1 - .72 * t)):
                tint = ((x * 7 + y * 11) % 9) / 9.
                return (.08 + .05 * tint, .39 + .15 * tint, .08 + .04 * tint, 1.)
    return (0., 0., 0., 0.)


def facade_pixel(x, y):
    """A recognisable little hut roof, shutters and door in a 64px alpha sprite."""
    # Texture X is local horizontal; Y is height from bottom.
    top = 40.0 + (23.0 * (1.0 - abs(x - 32.0) / 31.0))
    if 8 <= x <= 56 and 36 <= y <= top:
        return (.25, .36, .17, 1.) if (x + y) % 11 > 2 else (.13, .23, .09, 1.)
    if 10 <= x <= 54 and 3 <= y < 38:
        if 27 <= x <= 38 and y <= 24:
            return (.15, .10, .08, 1.) if x not in (27, 38) else (.60, .39, .19, 1.)
        if (14 <= x <= 23 or 42 <= x <= 51) and 22 <= y <= 31:
            return (.10, .31, .38, 1.) if 16 <= x <= 49 and 24 <= y <= 29 else (.24, .13, .07, 1.)
        if (y % 10 == 0 or x in (10, 54)):
            return (.25, .14, .08, 1.)
        return (.67, .45, .20, 1.)
    return (0., 0., 0., 0.)


def canopy_pixel(x, y):
    """Leafy clump with uneven pixel silhouette, not a photographic impostor."""
    dx, dy = (x - 32.) / 29., (y - 30.) / 26.
    edge = .92 + .06 * math.sin(x * .31) * math.cos(y * .57)
    if dx*dx + dy*dy > edge:
        return (0., 0., 0., 0.)
    tint = ((x * 19 + y * 7) % 13) / 13.
    return (.07 + .05 * tint, .28 + .21 * tint, .08 + .02 * tint, 1.)


images = {
    "checker": create_image("checker-ground-64", lambda x, y:
        ((.19, .43, .12, 1.) if ((x // 8 + y // 8) % 2 == 0)
         else (.69, .57, .29, 1.))),
    "wood": create_image("village-wood-64", lambda x, y:
        ((.37, .21, .10, 1.) if y % 12 < 2 else
         (.64, .41, .19, 1.) if (y % 12 == 5 or x % 23 == 0) else
         (.54, .33, .14, 1.))),
    "bark": create_image("village-bark-64", lambda x, y:
        ((.27, .18, .10, 1.) if x % 11 < 2 else
         (.48, .30, .16, 1.) if y % 19 < 2 else
         (.38, .23, .12, 1.))),
    "hut": create_image("village-hut-64", lambda x, y:
        ((.25, .17, .10, 1.) if x % 14 < 2 else
         (.52, .35, .19, 1.) if y % 16 < 3 else
         (.65, .46, .25, 1.))),
    "roof": create_image("village-roof-64", lambda x, y:
        ((.23, .31, .16, 1.) if (y % 10 < 2 or (x + y // 10 * 7) % 13 < 2)
         else (.40, .48, .23, 1.))),
    "palm": create_image("foliage-palms-64", palm_pixel),
    "facade": create_image("village-facade-64", facade_pixel),
    "canopy": create_image("village-canopy-64", canopy_pixel),
    "meadow": create_image("ground-meadow-64", lambda x, y:
        (.19 + .03 * ((x * 3 + y) % 7) / 7., .46 + .06 * ((x + y * 5) % 9) / 9., .15, 1.)),
    "cliff": create_image("gully-cliff-64", lambda x, y:
        ((.30, .29, .20, 1.) if ((x//13 + y//9) % 4 == 0) else
         (.48, .43, .26, 1.) if ((x//9 + y//17) % 3 == 0) else
         (.24, .31, .18, 1.))),
    "spring": create_image("spring-red-64", lambda x, y:
        ((.95, .18, .12, 1.) if 5 < x < 59 and 5 < y < 59 else
         (.97, .83, .16, 1.) if x % 9 < 3 or y % 9 < 3 else
         (.30, .07, .08, 1.)))
}


def textured_material(name, image, transparent=False):
    m = bpy.data.materials.new("JG_" + name)
    m.use_nodes = True
    tree = m.node_tree
    bsdf = tree.nodes.get("Principled BSDF")
    tex = tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if transparent:
        tree.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        if hasattr(m, "surface_render_method"):
            try:
                m.surface_render_method = "DITHERED"
            except (TypeError, ValueError):
                pass
        if hasattr(m, "blend_method"):
            try:
                m.blend_method = "CLIP"
            except (TypeError, ValueError):
                pass
        if hasattr(m, "use_backface_culling"):
            m.use_backface_culling = False
    return m


MATERIALS = {name: textured_material(name, img, name in ("palm","facade","canopy"))
             for name, img in images.items()}


def mesh_object(name, vertices, triangles, material, collection, role,
                sprite_uv=False, collision=False):
    if not vertices or not triangles:
        raise ValueError(name + ": empty mesh")
    if any(len(face) != 3 or len(set(face)) != 3 for face in triangles):
        raise ValueError(name + ": non-triangle or degenerate index face")
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], triangles)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    COLLECTIONS[collection].objects.link(obj)
    if collision:
        obj["saturn_mesh"] = "collision"
        obj.hide_render = True
        obj.hide_set(True)
        obj.display_type = "WIRE"
    else:
        obj["saturn_mesh"] = "render"
        obj.data.materials.append(MATERIALS[material])
        uv = mesh.uv_layers.new(name="UVMap")
        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                index = mesh.loops[loop_idx].vertex_index
                vert = vertices[index]
                if sprite_uv:
                    q = index % 4
                    uv.data[loop_idx].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[q]
                elif abs(poly.normal.z) > .5:
                    uv.data[loop_idx].uv = (vert[0] * .13, vert[1] * .13)
                elif abs(poly.normal.y) > .5:
                    uv.data[loop_idx].uv = (vert[0] * .13, vert[2] * .13)
                else:
                    uv.data[loop_idx].uv = (vert[1] * .13, vert[2] * .13)
    obj["jg_role"] = role
    obj["jg_sector"] = "tree_village"
    return obj


def box_geometry(center, size):
    x, y, z = center
    w, d, h = (q / 2 for q in size)
    v = [(x+dx*w, y+dy*d, z+dz*h) for dz in (-1, 1)
         for dy in (-1, 1) for dx in (-1, 1)]
    f = [(0, 3, 1), (0, 2, 3), (4, 5, 7), (4, 7, 6),
         (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6),
         (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return v, f


def box(name, center, size, material, coll, role, collision_type=None):
    v, f = box_geometry(center, size)
    o = mesh_object(name, v, f, material, coll, role)
    if collision_type == "top":
        mesh_object(name + "_COLL", v, [(4, 5, 7), (4, 7, 6)],
                    None, "JG_COLLISION", "walkable", collision=True)
    elif collision_type == "block":
        mesh_object(name + "_COLL", v, f, None,
                    "JG_COLLISION", "blocking", collision=True)
    return o


def platform(item):
    x, y, z = item["center"]
    # Six-sided platforms retain a readable round silhouette in 320x224.
    # 6 top + 12 skirt triangles instead of 8 + 16: save 30 tris / five pads.
    n = 6
    r = item["diameter"] / 2.
    depth = item["thickness"]
    outer = [(x + r*math.cos(2*math.pi*i/n),
              y + r*math.sin(2*math.pi*i/n), z) for i in range(n)]
    lower = [(px, py, z-depth) for px, py, _ in outer]
    vertices = outer + lower + [(x,y,z)]
    top = [(2*n,i,(i+1)%n) for i in range(n)]
    sides = []
    for i in range(n):
        j = (i+1)%n
        sides.extend([(i,j,n+i),(j,n+j,n+i)])
    mesh_object(item["id"],vertices,top+sides,item["material"],
                item["collection"],item["role"])
    mesh_object(item["id"]+"_COLL",vertices,top,None,"JG_COLLISION",
                "walkable",collision=True)


def bridge(item):
    x1,y1,z1 = item["from"]
    x2,y2,z2 = item["to"]
    dx,dy=x2-x1,y2-y1
    length=math.hypot(dx,dy)
    if length <= .1:
        raise ValueError("zero-length bridge: "+item["id"])
    nx,ny=-dy/length*item["width"]/2.,dx/length*item["width"]/2.
    v=[(x1-nx,y1-ny,z1),(x1+nx,y1+ny,z1),
       (x2+nx,y2+ny,z2),(x2-nx,y2-ny,z2)]
    down=[(x,y,z-item["thickness"]) for x,y,z in v]
    tris=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),
          (0,4,5),(0,5,1),(1,5,6),(1,6,2),
          (2,6,7),(2,7,3),(3,7,4),(3,4,0)]
    mesh_object(item["id"],v+down,tris,item["material"],
                item["collection"],item["role"])
    mesh_object(item["id"]+"_COLL",v,tris[:2],None,"JG_COLLISION",
                "walkable",collision=True)


def trunk(item):
    x,y,z=item["center"]
    r=item["radius"]
    h=item["height"]
    n=8
    verts=[]
    # Keep an 8-sided, tapered collision trunk but offset the top to make
    # an organic silhouette. Root buttresses and branch boughs sit outside it.
    for level,scale,ox,oy in ((0.,1.28,0.,0.), (h*.52,.82,-.7,.4),
                               (h,.60,1.0,.9)):
        verts.extend([(x+ox+r*scale*math.cos(i*2*math.pi/n),
                       y+oy+r*scale*math.sin(i*2*math.pi/n),z+level)
                      for i in range(n)])
    faces=[]
    for row in range(2):
        a,b=row*n,(row+1)*n
        for i in range(n):
            j=(i+1)%n
            faces.extend([(a+i,a+j,b+j),(a+i,b+j,b+i)])
    mesh_object(item["id"],verts,faces,item["material"],
                item["collection"],item["role"])
    mesh_object(item["id"]+"_COLL",verts,faces,None,"JG_COLLISION",
                "blocking",collision=True)
    # Three crossed leafy crowns use six alpha-textured triangles.
    # The old bare trunk read as a spike; the crown is non-collidable decor.
    crown = []
    for angle in (0., math.pi / 3., 2. * math.pi / 3.):
        dx, dy = 5.3 * math.cos(angle), 5.3 * math.sin(angle)
        crown.extend([(x-dx,y-dy,z+h-1.2), (x+dx,y+dy,z+h-1.2),
                      (x+dx,y+dy,z+h+4.7), (x-dx,y-dy,z+h+4.7)])
    faces_crown = [(q,q+1,q+2) for q in (0,4,8)] + [(q,q+2,q+3) for q in (0,4,8)]
    mesh_object(item["id"]+"_canopy",crown,faces_crown,"canopy",
                "JG_TREE_VILLAGE_DECOR","decoration",sprite_uv=True)


def hut(item):
    x,y,z=item["center"]
    w,d,h=item["size"]
    wall_h=h*.72
    v, faces=box_geometry((x,y,z+wall_h/2),(w,d,wall_h))
    mesh_object(item["id"]+"_walls",v,faces,"hut",item["collection"],item["role"])
    left,right=x-w/2,x+w/2
    back,front=y-d/2,y+d/2
    roofbase=z+wall_h
    peak=z+h
    roof_verts=[
        (left,back,roofbase),(right,back,roofbase),(x,back,peak),
        (left,front,roofbase),(right,front,roofbase),(x,front,peak)]
    roof_faces=[(0,3,5),(0,5,2),(2,5,4),(2,4,1),(0,2,1),(3,4,5)]
    mesh_object(item["id"]+"_roof",roof_verts,roof_faces,"roof",
                item["collection"],item["role"])
    # Avoid interior detail; blocker below remains independent of visual UV.
    box_v,box_f=box_geometry((x,y,z+wall_h/2),(w,d,wall_h))
    mesh_object(item["id"]+"_COLL",box_v,box_f,None,"JG_COLLISION",
                "blocking",collision=True)


def cross_planes(item):
    x,y,z=item["center"]
    width=item["width"]
    height=item["height"]
    v=[]
    for angle in (0.,math.pi/2.):
        dx=math.cos(angle)*width/2.
        dy=math.sin(angle)*width/2.
        v.extend([(x-dx,y-dy,z),(x+dx,y+dy,z),
                  (x+dx,y+dy,z+height),(x-dx,y-dy,z+height)])
    triangles=[(0,1,2),(0,2,3),(4,5,6),(4,6,7)]
    mesh_object(item["id"],v,triangles,
                "canopy" if item["kind"] == "foliage_x" else "palm",item["collection"],
                item["role"],sprite_uv=True)


def facade(item):
    x,y,z=item["center"]
    w,d,h=item["size"]
    vertices=[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),
              (x+w/2,y,z+h/2),(x-w/2,y,z+h/2)]
    mesh_object(item["id"],vertices,[(0,1,2),(0,2,3)],
                "facade",item["collection"],item["role"],sprite_uv=True)


def spring(item):
    x,y,z=item["center"]
    w,d,h=item["size"]
    box(item["id"],(x,y,z+h/2),(w,d,h), "spring",
        item["collection"],item["role"])
    # Mesh is visual only. Trigger and velocity need actual runtime code.


def branch(item):
    x1,y1,z1=item["from"]
    x2,y2,z2=item["to"]
    radius=item["radius"]
    dx,dy=x2-x1,y2-y1
    length=math.hypot(dx,dy)
    nx,ny=-dy/length*radius,dx/length*radius
    v=[(x1-nx,y1-ny,z1-radius),(x1+nx,y1+ny,z1-radius),
       (x2+nx,y2+ny,z2-radius),(x2-nx,y2-ny,z2-radius),
       (x1-nx,y1-ny,z1+radius),(x1+nx,y1+ny,z1+radius),
       (x2+nx,y2+ny,z2+radius),(x2-nx,y2-ny,z2+radius)]
    faces=[(0,1,2),(0,2,3),(4,6,5),(4,7,6),
           (0,4,5),(0,5,1),(1,5,6),(1,6,2),
           (2,6,7),(2,7,3),(3,7,4),(3,4,0)]
    mesh_object(item["id"],v,faces,item["material"],item["collection"],item["role"])



def valley_landmass():
    """Contoured 50x70m valley with three distinct textured bands.

    A 7x7 vertex grid makes 72 top triangles. Real collision follows the same
    top, while cliff-edge skirts are art-only, with NO fake collision.
    The terrain stays below the gameplay bridges around the centre.
    """
    xs = (-25., -18., -9., 0., 9., 18., 25.)
    ys = (0., 12., 24., 36., 48., 60., 70.)
    vertices = []
    for y in ys:
        for x in xs:
            bank = 7.2 * (abs(x) / 25.) ** 2.0
            waves = .62 * math.sin(y * .14 + x * .09) + .38 * math.cos(y * .23 - x * .06)
            z = -1.1 + bank + waves
            vertices.append((x, y, z))

    faces = []
    for row in range(len(ys) - 1):
        for col in range(len(xs) - 1):
            a = row * len(xs) + col
            b = a + 1
            c = a + len(xs)
            d = c + 1
            faces.extend(((a, b, d), (a, d, c)))

    # Every top triangle participates in the SAME continuous collision mesh.
    mesh_object("jg_village_contoured_ground_COLL", vertices, faces,
                None, "JG_COLLISION", "walkable", collision=True)

    # Three visual bands avoid the monochrome rectangle that looked like
    # an unfinished sheet; they share exact boundary vertices and heights.
    for first, last, material, name in (
        (0, 2, "cliff", "left_bank"),
        (2, 4, "meadow", "central_valley"),
        (4, 6, "cliff", "right_bank"),
    ):
        ncols = last - first + 1
        local = [vertices[row * len(xs) + col]
                 for row in range(len(ys)) for col in range(first, last + 1)]
        strips = []
        for row in range(len(ys) - 1):
            for col in range(ncols - 1):
                a = row * ncols + col
                b = a + 1
                c = a + ncols
                d = c + 1
                strips.extend(((a, b, d), (a, d, c)))
        mesh_object("jg_village_terrain_" + name, local, strips,
                    material, "JG_TERRAIN", "walkable")

    # Undercuts soften the exposed straight valley sides in isometric view.
    # Each of the left/right skirts is 6 quads = 12 render triangles.
    for col, side in ((0, -1.), (len(xs) - 1, 1.)):
        rim = [vertices[row * len(xs) + col] for row in range(len(ys))]
        skirt_vertices = rim + [(x + side * 3.2, y, z - 5.0)
                                for x, y, z in rim]
        skirt_faces = []
        for k in range(len(ys) - 1):
            upper = len(ys) + k
            skirt_faces.extend(((k, k + 1, upper + 1), (k, upper + 1, upper)))
        mesh_object("jg_village_bank_skirt_" + ("L" if side < 0 else "R"),
                    skirt_vertices, skirt_faces, "cliff", "JG_TERRAIN",
                    "decoration")


def hut_supports():
    """Ultra-cheap non-colliding timber struts joining facade silhouettes
    to the core tree. No free-floating squares in the overview render."""
    tree=(7.5,37.5)
    for item in data["objects"]:
        if item["kind"]!="facade":
            continue
        x,y,z=item["center"]
        bottom=z-item["size"][2]/2.
        x0,y0=tree
        dx,dy=x-x0,y-y0
        length=math.hypot(dx,dy)
        if length<.01:
            continue
        nx,ny=-dy/length*.45,dx/length*.45
        v=[(x0-nx,y0-ny,bottom-.7),(x0+nx,y0+ny,bottom-.7),
           (x+nx,y+ny,bottom-.7),(x-nx,y-ny,bottom-.7)]
        mesh_object(item["id"]+"_support",v,[(0,1,2),(0,2,3)],
                    "bark","JG_TREE_VILLAGE_DECOR","decoration")


def hut_decks_and_boughs():
    """Five collision-free hut landings, plus two real branch-shaped beams.

    Each facade stays 2D and uses just 2 textured triangles; the small deck
    below it gives a physical-looking building foundation from the overview.
    """
    for item in data["objects"]:
        if item["kind"] != "facade":
            continue
        x, y, z = item["center"]
        width, _, height = item["size"]
        floor = z - height / 2. - .35
        w = width / 2. + .55
        v = [(x-w,y-1.8,floor),(x+w,y-1.8,floor),
             (x+w,y+1.8,floor),(x-w,y+1.8,floor)]
        mesh_object(item["id"]+"_balcony",v,[(0,1,2),(0,2,3)],
                    "wood","JG_TREE_VILLAGE_DECOR","decoration")

    for number, target in enumerate(((15.0, 47.0, 11.7),
                                     (-14.0, 40.0, 11.9)), 1):
        branch({
            "id": "jg_tree_lateral_bough_%02d" % number,
            "from": (7.5, 37.5, 10.2),
            "to": target,
            "radius": .72,
            "material": "bark",
            "collection": "JG_TREE_VILLAGE_DECOR",
            "role": "decoration",
        })


def root_buttresses():
    """Three cheap broad root fins help the tree read as an anchored trunk."""
    x, y = 7.5, 37.5
    for idx, angle in enumerate((.36, 2.56, 4.55), 1):
        ux, uy = math.cos(angle), math.sin(angle)
        nx, ny = -uy, ux
        near = 2.6
        far = 6.4
        v = [(x+near*ux+1.05*nx,y+near*uy+1.05*ny,2.5),
             (x+near*ux-1.05*nx,y+near*uy-1.05*ny,2.5),
             (x+far*ux-.32*nx,y+far*uy-.32*ny,-.1),
             (x+far*ux+.32*nx,y+far*uy+.32*ny,-.1)]
        mesh_object("jg_tree_root_%02d" % idx,v,[(0,1,2),(0,2,3)],
                    "bark","JG_TREE_VILLAGE_DECOR","decoration")


BUILDERS={"ground":lambda x: box(x["id"],(x["center"][0],x["center"][1],
                                          x["center"][2]-x["size"][2]/2),
                                  x["size"],x["material"],x["collection"],
                                  x["role"],"top"),
          "bridge":bridge,"platform":platform,"trunk":trunk,"hut":hut,
          "facade":facade,"palm_x":cross_planes,"foliage_x":cross_planes,
          "spring":spring,"branch":branch}
for item in data["objects"]:
    BUILDERS[item["kind"]](item)
valley_landmass()
hut_supports()
hut_decks_and_boughs()
root_buttresses()

for marker in data["entities"]:
    obj=bpy.data.objects.new("JG_ENTITY_"+marker["id"],None)
    COLLECTIONS["JG_HELPERS"].objects.link(obj)
    obj.location=tuple(marker["position"])
    obj.empty_display_type="SPHERE"
    obj.empty_display_size=.6
    obj["saturn_id"]=marker["id"]
    obj["saturn_kind"]=marker["kind"]

# Blue editor-only scale proxy near spawn (not Sonic R model and never exported).
# Render it in both views to reveal real platform/stair proportions.
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=.64, location=(0., 5., 1.24))
proxy = bpy.context.object
proxy.name = "JG_EDITOR_ONLY_SCALE_PROXY_NOT_SONIC"
for collection in list(proxy.users_collection):
    collection.objects.unlink(proxy)
COLLECTIONS["JG_REFERENCE"].objects.link(proxy)
proxy_mat = bpy.data.materials.new("JG_EDITOR_ONLY_BLUE_REFERENCE")
proxy_mat.use_nodes = True
proxy_mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (.04,.18,.85,1.)
proxy.data.materials.append(proxy_mat)
proxy["jg_role"] = "reference_only_not_exported"

# Cameras and scale proxy are Blender-only; no Saturn scene export geometry.
cam_data=bpy.data.cameras.new("TreeVillage_Overview")
camera=bpy.data.objects.new("TreeVillage_Overview",cam_data)
COLLECTIONS["JG_REFERENCE"].objects.link(camera)
camera.location=(64,-67,56)
look=Vector((0,35,7))-camera.location
camera.rotation_euler=look.to_track_quat("-Z","Y").to_euler()
cam_data.type="ORTHO"
cam_data.ortho_scale=90
scene.camera=camera

ground_cam_data=bpy.data.cameras.new("TreeVillage_PlayerHeight")
ground_camera=bpy.data.objects.new("TreeVillage_PlayerHeight",ground_cam_data)
COLLECTIONS["JG_REFERENCE"].objects.link(ground_camera)
ground_camera.location=(-2.,-10.,4.2)
look_ground=Vector((5.5,32.,8.8))-ground_camera.location
ground_camera.rotation_euler=look_ground.to_track_quat("-Z","Y").to_euler()
ground_cam_data.type="PERSP"
ground_cam_data.lens=32
light_data=bpy.data.lights.new("VillageSun","SUN")
sun=bpy.data.objects.new("VillageSun",light_data)
COLLECTIONS["JG_REFERENCE"].objects.link(sun)
sun.rotation_euler=(math.radians(28),math.radians(-21),math.radians(-37))
light_data.energy=2.2
world=bpy.data.worlds.new("Jade Gully Sky")
scene.world=world
world.use_nodes=True
world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.14,.33,.51,1)
world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.8

bpy.context.view_layer.update()
render_items=[o for o in bpy.data.objects if o.type=="MESH" and o.get("saturn_mesh")=="render"]
colliders=[o for o in bpy.data.objects if o.type=="MESH" and o.get("saturn_mesh")=="collision"]
render_faces=sum(len(o.data.polygons) for o in render_items)
render_vertices=sum(len(o.data.vertices) for o in render_items)
collider_faces=sum(len(o.data.polygons) for o in colliders)
if render_faces>data["scene_limits"]["render_faces_max"]:
    raise RuntimeError("visual face budget: %s exceeds 448" % render_faces)
if render_vertices>data["scene_limits"]["vertices_max"]:
    raise RuntimeError("vertex budget: %s exceeds 2048" % render_vertices)
if len(data["entities"])>data["scene_limits"]["entity_markers_max"]:
    raise RuntimeError("too many entities")
report={
  "generator":"tools/create_tree_village_kit.py",
  "status":"Blender authoring source, not yet Saturn runtime",
  "scene_name":data["name"],
  "render_faces":render_faces,
  "render_vertices":render_vertices,
  "collision_faces":collider_faces,
  "render_meshes":len(render_items),
  "collision_meshes":len(colliders),
  "entity_markers":len(data["entities"]),
  "model_definitions":len(data["objects"]),
  "authoring_revision":data.get("authoring_revision",1),
  "per_object_faces":{o.name:len(o.data.polygons) for o in render_items},
  "routes":data["routes"],
  "textures":sorted((p.name for p in TEX.glob("*.png"))),
  "warnings":["spring marker has no in-game impulse",
              "editor blue scale proxy is NOT the Sonic character and is never exported",
              "static X-planes are not camera-facing billboards",
              "LOD/sector streaming not yet active",
              "new textures are Blender-only until Saturn texture pipeline integration"]
}
(OUT/"kit-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
blend_path=OUT/"tree_village_source.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
if PREVIEW:
    try:
        for engine in ("BLENDER_EEVEE_NEXT","BLENDER_EEVEE","BLENDER_WORKBENCH"):
            try:
                scene.render.engine=engine
                break
            except (TypeError,ValueError):
                continue
        scene.render.image_settings.file_format="PNG"
        for cam, filename in ((camera, "tree_village_preview.png"),
                              (ground_camera, "tree_village_ground_preview.png")):
            scene.camera=cam
            scene.render.filepath=str(OUT/filename)
            bpy.ops.render.render(write_still=True)
            print("[Tree Village] preview:",filename)
        scene.camera=camera
    except Exception as exc:
        print("[Tree Village] preview not rendered: "+str(exc))
print("[Tree Village] Blender source:",blend_path)
print("[Tree Village] Render faces:",render_faces,"Vertices:",render_vertices,
      "Collision faces:",collider_faces)
print("[Tree Village] spring gameplay and Saturn renderer integration remain pending")
