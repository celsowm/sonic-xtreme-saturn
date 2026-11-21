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
from tools.prop_materials import split_palm_faces
from tools.adventure_tiling import refine_first_segments,split_quad_across

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=2:
    raise SystemExit("expected TOOLKIT_CHECKOUT OUTPUT_DIRECTORY")
toolkit,out=(Path(a).resolve() for a in args)
sys.path.insert(0,str(toolkit))
from libsaturn_toolkit.exporter import export_bundle


def _decimate_prop_piece(name,transformed,faces,mat,budget,path):
    """Reduce one original GLB material to a bounded exportable OBJ mesh."""
    obj=base.mesh_prop(name,transformed,faces,mat)
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
            raise RuntimeError(f"{path}: {name} cannot meet {budget} triangles")
    if len(obj.data.polygons)==0:
        raise RuntimeError(f"{path}: {name} lost all triangles")
    # The OBJ baker counts every vertex record, even unreferenced source
    # vertices left by Blender's decimator. Compact to live polygon indices.
    old_mesh=obj.data
    used=sorted({int(idx) for poly in old_mesh.polygons for idx in poly.vertices})
    remap={old:new for new,old in enumerate(used)}
    compact_vertices=[tuple(old_mesh.vertices[idx].co) for idx in used]
    from tools.bake_greybox import convert_xyz
    fixed_vertices=[convert_xyz(p) for p in compact_vertices]
    compact_faces=[]
    removed=0
    for poly in old_mesh.polygons:
        idx=tuple(remap[int(i)] for i in poly.vertices)
        a,b,c=idx[:3]
        va,vb,vc=(fixed_vertices[k] for k in (a,b,c))
        u=tuple(vb[k]-va[k] for k in range(3))
        v=tuple(vc[k]-va[k] for k in range(3))
        normal=(u[1]*v[2]-u[2]*v[1],
                u[2]*v[0]-u[0]*v[2],
                u[0]*v[1]-u[1]*v[0])
        if not any(normal):
            removed+=1
            continue
        compact_faces.append(idx)
    if not compact_faces:
        raise RuntimeError(f"{path}: {name} has no nondegenerate Q16 faces")
    compact=bpy.data.meshes.new(name+"_compact")
    compact.from_pydata(compact_vertices,[],compact_faces)
    compact.update()
    compact.materials.append(mat)
    obj.data=compact
    if old_mesh.users==0:bpy.data.meshes.remove(old_mesh)
    obj["saturn_mesh"]="render"
    print(f"[adventure] {name}: {len(faces)} -> {len(compact_faces)} triangles; {len(used)} live vertices; removed {removed}; cap {budget}")
    return obj


def import_cc0_prop(item,materials):
    """Import actual Kenney geometry and preserve *source* material boundaries.

    Trees have separate woodBark / leafsGreen GLB primitives. Each primitive
    receives its own decimation budget, otherwise a single 17-triangle mesh
    can erase the trunk and leave a green floating crown. No new polygons
    or guessed height classification are introduced after decimation.
    """
    path=ROOT/"assets/kenney"/item["asset"]
    verts,faces,face_materials,material_names=read_glb_triangles(path,with_materials=True)
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
    budget=item["triangles_max"]
    if item["asset"].startswith("nature-kit/tree-"):
        wood,leaves=split_palm_faces(faces,face_materials,material_names)
        # Near and far are two completely separate derived meshes. Do not
        # choose LOD per triangle: otherwise foliage and bark switch at
        # different distances, producing "floating" tree fragments.
        trunk_budget=max(4,budget//4)
        low_budget=json.loads(DEFAULT.read_text())["budgets"]["far_palm_lod_faces_per_instance"]
        groups=(
            ("lod_near_wood",wood,trunk_budget,"wood"),
            ("lod_near_canopy",leaves,budget-trunk_budget,"canopy"),
            ("lod_far_wood",wood,2,"wood"),
            ("lod_far_canopy",leaves,low_budget-2,"canopy"),
        )
    else:
        groups=((item["palette"],faces,budget,item["palette"]),)
    built=[]
    total=0
    near_total=0
    far_total=0
    for label,group_faces,limit,material in groups:
        obj=_decimate_prop_piece(f'{item["id"]}_{label}',transformed,group_faces,
                                 materials[material],limit,path)
        built.append(obj)
        count=len(obj.data.polygons)
        if label.startswith("lod_far_"):
            far_total+=count
        else:
            near_total+=count
        total+=count
    if near_total>budget:
        raise RuntimeError(f"{path}: near LOD exceeds authored {budget}-triangle cap")
    if item["asset"].startswith("nature-kit/tree-"):
        if far_total>low_budget:
            raise RuntimeError(f"{path}: far LOD exceeds authored {low_budget} triangles")
        print(f'[adventure] {item["id"]}: original Kenney wood/foliage retained; near={near_total} far={far_total} faces')
    return built[0]


def valley_landmass(main,materials,tiling):
    """Independent render-only near texture repeats over unchanged collision.

    The original four collision bands remain exactly as before. Replace only
    the foreground render object for specified material bands with smaller
    polygons, each mapped to the existing 64x64 Kenney indexed8 source art.
    No extra VDP1 texture storage, bespoke UV hardware or collision triangles.
    """
    rows=[(main[0][0],-12,main[0][2],main[0][3]),*main]
    refined=[]
    for i,point in enumerate(rows):
        refined.append(point)
        if i<4 and i+1<len(rows):
            following=rows[i+1]
            refined.append(tuple((point[k]+following[k])*0.5 for k in range(4)))
    offsets=(-48.0,-20.0,0.0,20.0,48.0)
    bands=("canopy","terrace","meadow","rock")
    grid=[]
    for x,y,z,width in refined:
        left=4.0 if 24<=y<=95 else 2.0
        river=-4.5 if 35<=y<=79 else 1.3
        levels=(left+6.0,left,-0.5,river,river+6.0)
        grid.append([(x+dx,y,z+dz) for dx,dz in zip(offsets,levels)])
    for col,material in enumerate(bands):
        verts=[]
        quads=[]
        for row in grid:
            verts.extend((row[col],row[col+1]))
        for i in range(len(grid)-1):
            n=2*i
            quads.append((n,n+1,n+3,n+2))
        obj=base.mesh_prop(f"jade_valley_band_{col}_{material}",verts,quads,materials[material])
        base.collision_copy(obj)
        if material in tiling["valley_bands"]:
            render_verts=[]
            render_quads=[]
            for i in range(len(grid)-1):
                a,b=grid[i][col],grid[i][col+1]
                c,d=grid[i+1][col+1],grid[i+1][col]
                pieces=(split_quad_across(a,b,c,d)
                        if i<tiling["valley_prefix_segments"]
                        else ((a,b,c,d),))
                for piece in pieces:
                    start=len(render_verts)
                    render_verts.extend(piece)
                    render_quads.append((start,start+1,start+2,start+3))
            tiled_mesh=bpy.data.meshes.new(obj.name+"_near_tiles")
            tiled_mesh.from_pydata(render_verts,[],render_quads)
            tiled_mesh.update()
            tiled_mesh.materials.append(materials[material])
            # Copy of the ORIGINAL mesh was already marked as collision.
            obj.data=tiled_mesh
            print(f"[adventure] {material}: {len(render_quads)} render tiles vs {len(quads)} collision quads")
    return len(grid)-1


def branch_terrace(route,mat,side):
    """One low-poly sloping edge for elevated branches (not a vertical wall)."""
    import math
    points=route["stations"]
    verts=[]
    faces=[]
    for i,(x,y,z,width) in enumerate(points):
        before=points[max(0,i-1)]
        after=points[min(len(points)-1,i+1)]
        dx=after[0]-before[0]
        dy=after[1]-before[1]
        length=math.hypot(dx,dy)
        if length<=0.0001:raise ValueError("coincident branch stations")
        nx=side*dy/length
        ny=-side*dx/length
        verts.extend((
            (x+nx*width,y+ny*width,z),
            (x+nx*(width+7),y+ny*(width+7),z-2.8),
        ))
        if i:
            n=2*i
            faces.append((n-2,n-1,n+1,n))
    return base.mesh_prop(f'{route["id"]}_terrace',verts,faces,mat)


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
        # Slope the bank OUTWARD rather than hanging vertical walls in air.
        # The walkable valley below remains independent collision geometry.
        extend=1.45
        bottom_b=(x+(b[0]-x)*extend,y+(b[1]-y)*extend,b[2]-d)
        bottom_a=(x+(a[0]-x)*extend,y+(a[1]-y)*extend,a[2]-d)
        vertices.extend((a,b,bottom_b,bottom_a))
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
        "wood":base.material("Palm trunk palette using existing Kenney sandstone",(0.53,0.37,0.20)),
        "rock":base.material("CC0 rock flat",(0.35,0.32,0.26)),
        "water":base.material("Waterfall cyan",(0.19,0.71,0.83)),
        "meadow":base.material("Connected canyon grass",(0.20,0.48,0.13)),
        "terrace":base.material("Raised route embankment",(0.34,0.44,0.15)),
    }
    # Build surrounding solid ground first. Main and branching ribbons are
    # kept at their exact old coordinates; the valley is a separate walkable
    # mesh for exploration and safe landings beyond the track edges.
    valley_landmass(data["routes"][0]["stations"],materials,data["visual_tiling"])
    for route in data["routes"]:
        top=base.ribbon(route["id"]+"_route",route["stations"],materials[route["id"]])
        base.collision_copy(top)
        if route["id"]=="main":
            fine=refine_first_segments(route["stations"],
                                        data["visual_tiling"]["main_route_prefix_segments"])
            base.ribbon("main_tiled_route",fine,materials["main"])
            # Original collision copy remains independent. Remove only the
            # redundant coarse *render* ribbon, not its collision mesh.
            bpy.data.objects.remove(top,do_unlink=True)
        if route["id"] in ("upper","river","ruins"):
            branch_terrace(route,materials["terrace"], -1 if route["id"]!="river" else 1)
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
