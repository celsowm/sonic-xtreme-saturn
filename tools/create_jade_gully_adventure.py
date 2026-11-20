"""Jade Gully Adventure v1: branching Blender scene with CC0 Kenney props.

Runs independently of the Ymir-qualified legacy greybox:
blender -b --factory-startup --python-exit-code 1 \
  --python tools/create_jade_gully_adventure.py -- <toolkit> <output>

All walkable/collidable surfaces are game-authored ribbon meshes. Imported
Kenney GLB assets provide visual scenery only. Each asset is explicitly
decimated and has a strict face budget; no glTF is read on Saturn.
"""
import json
import sys
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tools"))

import create_jade_gully as base
from tools.validate_adventure_layout import DEFAULT,validate
from tools.read_kenney_glb import read_glb_triangles

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=2:
    raise SystemExit("expected TOOLKIT_CHECKOUT OUTPUT_DIRECTORY")
toolkit,out=(Path(a).resolve() for a in args)
sys.path.insert(0,str(toolkit))
from libsaturn_toolkit.exporter import export_bundle


def import_cc0_prop(item,materials):
    """Read a curated GLB with its node transforms, then decimate it.

    The original model, textures and provenance remain unchanged in assets/.
    Render mesh is stored in world coordinates; it has NO collision marker.
    """
    path=ROOT/"assets/kenney"/item["asset"]
    # Read only the already-vetted, uncompressed GLB geometry. The generic
    # Blender glTF importer requires numpy on some Linux builds; the pure
    # standard-library parser makes CI and Mac authoring reproducible.
    verts,faces=read_glb_triangles(path)
    mins=tuple(min(p[i] for p in verts) for i in range(3))
    maxs=tuple(max(p[i] for p in verts) for i in range(3))
    extent=maxs[2]-mins[2]
    if extent<1e-6:
        raise RuntimeError(f"{path}: zero-height mesh")
    cx=(maxs[0]+mins[0])/2
    cy=(maxs[1]+mins[1])/2
    scale=item["height_m"]/extent
    x,y,z=item["position"]
    transformed=[(x+(p[0]-cx)*scale,y+(p[1]-cy)*scale,z+(p[2]-mins[2])*scale) for p in verts]
    name=f'{item["id"]}_{item["palette"]}'
    obj=base.mesh_prop(name,transformed,faces,materials[item["palette"]])
    budget=item["triangles_max"]
    if len(obj.data.polygons)>budget:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        for _ in range(5):
            count=len(obj.data.polygons)
            if count<=budget:break
            dec=obj.modifiers.new(name="SaturnTriangleBudget",type="DECIMATE")
            dec.decimate_type="COLLAPSE"
            dec.ratio=max(0.005,min(0.98,(budget/max(1,count))*0.92))
            bpy.ops.object.modifier_apply(modifier=dec.name)
        if len(obj.data.polygons)>budget:
            raise RuntimeError(f"{path}: cannot meet face budget {budget} (got {len(obj.data.polygons)})")
    if len(obj.data.polygons)==0:
        raise RuntimeError(f"{path}: face reduction removed model")
    obj["saturn_mesh"]="render"
    print(f'[adventure] {item["id"]}: {len(faces)} -> {len(obj.data.polygons)} triangles; budget {budget}')
    return obj


def cliff_skirt(route,mat,depth=5.0):
    """Visual underside beneath every ribbon segment, with no wall physics."""
    points=route["stations"]
    left=[]
    right=[]
    import math
    for i,(x,y,z,width) in enumerate(points):
        a=points[max(0,i-1)];b=points[min(len(points)-1,i+1)]
        dx=b[0]-a[0];dy=b[1]-a[1]
        norm=math.hypot(dx,dy)
        if norm<1e-6:raise ValueError("coincident cliff station")
        rx,ry=dy/norm*width,-dx/norm*width
        left.append((x-rx,y-ry,z))
        right.append((x+rx,y+ry,z))
    verts=[]
    faces=[]
    for side in (left,right):
        for i in range(len(side)-1):
            a=side[i];b=side[i+1]
            j=len(verts)
            verts.extend((a,b,(b[0],b[1],b[2]-depth),(a[0],a[1],a[2]-depth)))
            faces.append((j,j+1,j+2,j+3))
    return base.mesh_prop(f'{route["id"]}_cliff_rock',verts,faces,mat)


def clearing_pad(pad,materials):
    """Broad *walkable* open area connected to a route station, with cliff skirt."""
    x,y,z=pad["center"]
    wx,wy=pad["half_extents"]
    corners=[
        (x-wx,y-wy,z), (x+wx,y-wy,z),
        (x+wx,y+wy,z), (x-wx,y+wy,z)
    ]
    top=base.mesh_prop(f'{pad["id"]}_{pad["theme"]}_route',corners,
                       ((0,1,2,3),),materials[pad["theme"]])
    base.collision_copy(top)
    vertices=[]
    quads=[]
    for i in range(4):
        a=corners[i]; b=corners[(i+1)%4]
        n=len(vertices)
        d=pad["depth_m"]
        vertices.extend((a,b,(b[0],b[1],b[2]-d),(a[0],a[1],a[2]-d)))
        quads.append((n,n+1,n+2,n+3))
    base.mesh_prop(f'{pad["id"]}_skirt_rock',vertices,quads,materials["rock"])
    return top


def main():
    data=json.loads(DEFAULT.read_text())
    report=validate(data)
    print("[adventure] Contract validated:",report)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.unit_settings.system="METRIC"
    scene.unit_settings.scale_length=1.0
    materials={
        "main":base.material("Fast route grass",(0.18,0.53,0.12)),
        "upper":base.material("Canopy path",(0.63,0.49,0.18)),
        "river":base.material("Basin grass",(0.13,0.48,0.22)),
        "ruins":base.material("Temple path",(0.48,0.47,0.34)),
        "canopy":base.material("CC0 foliage flat",(0.09,0.42,0.14)),
        "rock":base.material("CC0 rock flat",(0.35,0.32,0.26)),
        "water":base.material("Waterfall cyan",(0.19,0.71,0.83)),
    }
    for route in data["routes"]:
        top=base.ribbon(route["id"]+"_route",route["stations"],materials[route["id"]])
        base.collision_copy(top)
        cliff_skirt(route,materials["rock"],depth=5.0)
    for pad in data.get("clearings",[]):
        clearing_pad(pad,materials)
    for entity in data["entities"]:
        base.marker(entity["id"],entity["kind"],tuple(entity["position"]))
    for prop in data["set_dressing"]:
        import_cc0_prop(prop,materials)
    # A paper-thin water surface is intentionally visual only, no water physics.
    base.waterfall("gully",-18,77,-4,12,materials["water"])
    bpy.context.view_layer.update()
    out.mkdir(parents=True,exist_ok=True)
    generated=export_bundle(bpy.context,out/"jade_gully.json")
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"jade_gully.blend"))
    info=json.loads(generated[0].read_text())
    if len(info["entities"])!=len(data["entities"]):
        raise RuntimeError("entity export mismatch")
    (out/"adventure-contract.json").write_text(json.dumps(report,indent=2)+"\n")
    print(f'[adventure] {len(info["entities"])} markers, render/collision exports ready')
    print("[adventure] This candidate is NOT qualified on Saturn until Ymir passes.")


if __name__=="__main__":
    main()
