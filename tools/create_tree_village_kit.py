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
    if 4 <= y < 47 and abs(x - cx) < 2.8:
        return (.34, .20, .08, 1.)
    origin = (32., 46.)
    tips = ((5, 36), (10, 54), (23, 61), (42, 61),
            (55, 53), (61, 36), (12, 40), (54, 40))
    for a, b in tips:
        vx, vy = a - origin[0], b - origin[1]
        t = ((x - origin[0]) * vx + (y - origin[1]) * vy) / (vx * vx + vy * vy)
        if 0 <= t <= 1:
            dist = abs((x - origin[0]) * vy - (y - origin[1]) * vx) / math.hypot(vx, vy)
            if dist < 4.4 * (1 - .60 * t):
                return (.04 + .06 * ((x + y) % 3) / 2, .30 + .14 * (y % 4) / 4, .09, 1.)
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
    n = 8
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
    for level,scale in ((0.,1.), (h*.52,.84), (h,.52)):
        verts.extend([(x+r*scale*math.cos(i*2*math.pi/n),
                       y+r*scale*math.sin(i*2*math.pi/n),z+level)
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
    """Scenic, collision-enabled ground beneath the bridges so the village isn't
    floating in blue emptiness. This is the 50x70m authoring cell only."""
    xs=(-24.,-12.,0.,12.,24.)
    ys=(18.,32.,46.,58.,70.)
    vertices=[]
    for iy,y in enumerate(ys):
        for ix,x in enumerate(xs):
            # Under the playable decks. Smooth edge rises frame the middle route.
            edge = max(0., (abs(x)-8.) / 16.)
            z = -.8 + 2.8*edge*edge + .20*math.sin(iy*.9 + ix*.6)
            vertices.append((x,y,z))
    top=[]
    for row in range(len(ys)-1):
        for col in range(len(xs)-1):
            a=row*len(xs)+col
            b=a+1
            c=a+len(xs)
            d=c+1
            top.extend(((a,b,d),(a,d,c)))
    mesh_object("jg_village_connected_terrain",vertices,top,
                "meadow","JG_TERRAIN","walkable")
    mesh_object("jg_village_connected_terrain_COLL",vertices,top,
                None,"JG_COLLISION","walkable",collision=True)


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

for marker in data["entities"]:
    obj=bpy.data.objects.new("JG_ENTITY_"+marker["id"],None)
    COLLECTIONS["JG_HELPERS"].objects.link(obj)
    obj.location=tuple(marker["position"])
    obj.empty_display_type="SPHERE"
    obj.empty_display_size=.6
    obj["saturn_id"]=marker["id"]
    obj["saturn_kind"]=marker["kind"]

# Reference axis and camera are Blender-only; no export geometry.
cam_data=bpy.data.cameras.new("TreeVillage_Overview")
camera=bpy.data.objects.new("TreeVillage_Overview",cam_data)
COLLECTIONS["JG_REFERENCE"].objects.link(camera)
camera.location=(64,-67,56)
look=Vector((0,35,7))-camera.location
camera.rotation_euler=look.to_track_quat("-Z","Y").to_euler()
cam_data.type="ORTHO"
cam_data.ortho_scale=85
scene.camera=camera
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
  "per_object_faces":{o.name:len(o.data.polygons) for o in render_items},
  "routes":data["routes"],
  "textures":sorted((p.name for p in TEX.glob("*.png"))),
  "warnings":["spring marker has no in-game impulse",
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
        scene.render.filepath=str(OUT/"tree_village_preview.png")
        bpy.ops.render.render(write_still=True)
    except Exception as exc:
        print("[Tree Village] preview not rendered: "+str(exc))
print("[Tree Village] Blender source:",blend_path)
print("[Tree Village] Render faces:",render_faces,"Vertices:",render_vertices,
      "Collision faces:",collider_faces)
print("[Tree Village] spring gameplay and Saturn renderer integration remain pending")
