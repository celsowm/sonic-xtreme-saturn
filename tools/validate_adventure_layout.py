"""Validate branching Jade Gully authoring layout before Blender or SH-2 build."""
import argparse
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/"assets/levels/jade_gully_adventure_v1.json"

def validate(data, asset_root=None):
    asset_root=Path(asset_root) if asset_root is not None else ROOT/"assets/kenney"
    if data.get("schema_version")!=1 or data.get("axes")!="RH_Z_UP" or data.get("units")!="m":
        raise ValueError("unsupported layout contract")
    if data.get("target_visual_fps")!=30 or data.get("physics_hz")!=60:
        raise ValueError("stage must use 30 FPS visual and 60Hz fixed-step physics")
    bounds=data["world_bounds"]
    def point(p):
        if not isinstance(p,list) or len(p)!=3:
            raise ValueError("position must have x,y,z")
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in p):
            raise ValueError("non-finite coordinate")
        if any(p[i]<bounds[k][0] or p[i]>bounds[k][1] for i,k in enumerate("xyz")):
            # Stations use x,y,z with z-up; bounds also use x,y,z.
            raise ValueError("coordinate outside scene bounds")
        return tuple(p)
    paths=data["routes"]
    if len(paths)<3 or len({r["id"] for r in paths})!=len(paths):
        raise ValueError("need distinct branching routes")
    routes={}
    junctions={}
    for r in paths:
        if not r.get("collision") or len(r["stations"])<2:
            raise ValueError("every route must have real top-surface collision")
        stations=[]
        for s in r["stations"]:
            if len(s)!=4 or type(s[3]) not in (int,float) or not 2<=s[3]<=8:
                raise ValueError("invalid ribbon width")
            xyz=point(s[:3])
            stations.append(xyz)
            junctions.setdefault(xyz,set()).add(r["id"])
        if any(a==b for a,b in zip(stations,stations[1:])):
            raise ValueError("route contains coincident stations")
        routes[r["id"]]=stations
    if "main" not in routes:
        raise ValueError("main route is required")
    main=routes["main"]
    for r in paths:
        if r["id"]!="main":
            if tuple(r["stations"][0][:3]) not in main and len(junctions[tuple(r["stations"][0][:3])])==1:
                raise ValueError("branch begins without connection")
            if tuple(r["stations"][-1][:3]) not in main and len(junctions[tuple(r["stations"][-1][:3])])==1:
                raise ValueError("branch ends without rejoining")
    zone_ids=set()
    for zone in data["zones"]:
        if zone["id"] in zone_ids:raise ValueError("duplicate zone")
        zone_ids.add(zone["id"]);point(zone["anchor"])
        if not 2<=zone["radius_m"]<=40:raise ValueError("zone radius")
    entities=data["entities"]
    if len(entities)>data["budgets"]["entities_max"]:
        raise ValueError("too many entities")
    if len({e["id"] for e in entities})!=len(entities):
        raise ValueError("duplicate entity ID")
    for e in entities:
        point(e["position"])
        if e["zone"] not in zone_ids:raise ValueError("unknown entity zone")
    if sum(e["kind"]=="player_spawn" for e in entities)!=1 or sum(e["kind"]=="goal" for e in entities)!=1:
        raise ValueError("one spawn and one goal required")
    props=data["set_dressing"]
    if len({x["id"] for x in props})!=len(props):
        raise ValueError("duplicate prop ID")
    used_budget=0
    for prop in props:
        point(prop["position"])
        rel=Path(prop["asset"])
        if rel.is_absolute() or ".." in rel.parts or rel.suffix!=".glb":
            raise ValueError("unsafe asset path")
        if not (asset_root/rel).is_file():
            raise ValueError(f"missing curated CC0 model: {rel}")
        if not (3<=prop["triangles_max"]<=16):
            raise ValueError("unbounded imported prop LOD")
        used_budget+=prop["triangles_max"]
    limit=data["budgets"]["max_imported_prop_triangles"]
    if used_budget>limit:raise ValueError("prop budget exceeded")
    segments=sum(len(x["stations"])-1 for x in paths)
    estimated_render_faces=segments*6+used_budget
    if estimated_render_faces>data["budgets"]["render_faces_max"]:
        raise ValueError("render budget exceeded: routes+cliff skirts+props")
    if data["budgets"]["render_faces_max"]>256:
        raise ValueError("unsupported single-stage face capacity")
    return {
        "routes":len(paths),
        "zones":len(zone_ids),
        "entities":len(entities),
        "props":len(props),
        "path_segments":segments,
        "corridor_triangles":segments*2,
        "cliff_triangles":segments*4,
        "prop_triangle_budget":used_budget,
        "face_budget_total":estimated_render_faces,
        "face_capacity":data["budgets"]["render_faces_max"],
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest",type=Path,nargs="?",default=DEFAULT)
    args=p.parse_args()
    result=validate(json.loads(args.manifest.read_text()))
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
