"""Static, dependency-free integrity checks for the Tree Village Blender source manifest.

The checks run in host CI without Blender and do not prove Saturn runtime
compatibility, rendered frame rate, playable spring traversal or texture alpha.
"""
import json
import math
from pathlib import Path

DEFAULT = (Path(__file__).resolve().parents[1] /
           "assets/jade-gully/tree-village/kit-manifest.json")

KINDS = {"ground", "bridge", "platform", "trunk", "branch", "hut",
         "facade", "palm_x", "foliage_x", "spring"}
COLLECTIONS = {"JG_TERRAIN", "JG_TREE_VILLAGE_CORE", "JG_TREE_VILLAGE_DECOR",
               "JG_BILLBOARDS"}
RENDER_MATERIALS = {"checker", "wood", "bark", "hut", "roof", "palm", "spring"}
ROLES = {"walkable", "blocking", "decoration", "trigger_placeholder"}


def validate(data):
    if data.get("schema_version") != 1 or data.get("axes") != "RH_Z_UP" or data.get("units") != "m":
        raise ValueError("unsupported Tree Village manifest")
    if data.get("runtime_status") != "blender_authoring_only":
        raise ValueError("manifest must not claim in-game integration")
    if data.get("targets") != {"visual_fps": 30, "physics_hz": 60}:
        raise ValueError("expected Saturn 30/60 visual/physics intent")
    limits = data["scene_limits"]
    if any(limits[key] != expected for key, expected in
           (("render_faces_max", 448), ("vertices_max", 2048),
            ("entity_markers_max", 64), ("coordinates_absolute_max_m", 256))):
        raise ValueError("manifest must track the actual single-stage export ceilings")
    bounds = data["cell_bounds"]
    if any(len(bounds[axis]) != 2 or bounds[axis][0] >= bounds[axis][1] for axis in "xyz"):
        raise ValueError("invalid cell bounds")

    def point(p):
        if not isinstance(p, list) or len(p) != 3:
            raise ValueError("expected 3D point")
        if any(type(v) not in (float, int) or not math.isfinite(v) for v in p):
            raise ValueError("non-finite or non-numeric position")
        for value, axis in zip(p, "xyz"):
            low, high = bounds[axis]
            if value < low or value > high or abs(value) > limits["coordinates_absolute_max_m"]:
                raise ValueError(f"position outside bounds: {p}")
        return tuple(p)

    objects = data["objects"]
    object_map = {o["id"]: o for o in objects}
    if len(object_map) != len(objects) or len(objects) < 20:
        raise ValueError("duplicate or incomplete geometry IDs")
    count_by_kind = {}
    for o in objects:
        kind = o["kind"]
        count_by_kind[kind] = count_by_kind.get(kind, 0) + 1
        if kind not in KINDS or o["collection"] not in COLLECTIONS or o["role"] not in ROLES:
            raise ValueError("unknown mesh type/collection/role")
        if o["material"] not in RENDER_MATERIALS:
            raise ValueError("missing texture/material")
        if kind in {"bridge", "branch"}:
            point(o["from"]); point(o["to"])
            if o["from"] == o["to"]:
                raise ValueError("zero-length connection")
        else:
            point(o["center"])
        for key in ("radius", "height", "diameter", "thickness", "width"):
            if key in o and (type(o[key]) not in (int, float) or
                             not math.isfinite(o[key]) or o[key] <= 0):
                raise ValueError("invalid positive geometry dimension")
        if "size" in o:
            if len(o["size"]) != 3 or any(type(v) not in (int, float) or v <= 0
                                           for v in o["size"]):
                raise ValueError("invalid geometry dimensions")
        if kind in {"ground", "platform", "bridge"} and o["role"] != "walkable":
            raise ValueError("walking surfaces must be marked collidable")
        if kind in {"palm_x", "foliage_x", "facade", "branch"} and o["role"] != "decoration":
            raise ValueError("fake scenery cannot be collidable")
        if kind == "spring" and o["role"] != "trigger_placeholder":
            raise ValueError("spring has no active in-game trigger")
    for kind in ("ground", "platform", "bridge", "trunk", "hut",
                 "facade", "spring", "palm_x", "foliage_x"):
        if count_by_kind.get(kind, 0) < 1:
            raise ValueError("missing essential hybrid kit type: "+kind)

    routes = data["routes"]
    if len(routes) != 2 or {r["id"] for r in routes} != {"main", "upper"}:
        raise ValueError("both main and optional upper paths are required")
    for r in routes:
        if len(r["waypoints"]) < 3:
            raise ValueError("route too short")
        for p in r["waypoints"]:
            point(p)
        for a, b in zip(r["waypoints"], r["waypoints"][1:]):
            if a == b:
                raise ValueError("duplicate route waypoint")
        if any(part not in object_map for part in r["parts"]):
            raise ValueError("route refers to nonexistent geometry")
        if any(object_map[part]["role"] not in {"walkable", "trigger_placeholder"}
               for part in r["parts"]):
            raise ValueError("route includes non-walkable scenery")
    main, upper = next(r for r in routes if r["id"] == "main"), next(r for r in routes if r["id"] == "upper")
    if main["mode"] != "walkable" or upper["mode"] != "spring_launch_required":
        raise ValueError("do not misstate the spring-required optional route")
    if main["waypoints"][1] != upper["waypoints"][0] or main["waypoints"][3] != upper["waypoints"][-1]:
        raise ValueError("upper route must branch and rejoin the main route")
    for part in ("entry_ramp", "platform_lower", "bridge_main_lower", "platform_middle",
                 "bridge_main_upper", "platform_upper", "exit_ramp", "platform_exit"):
        if part not in main["parts"]:
            raise ValueError("main route not complete: "+part)

    entities = data["entities"]
    if len(entities) > limits["entity_markers_max"] or len({x["id"] for x in entities}) != len(entities):
        raise ValueError("entity budget or IDs")
    for e in entities:
        point(e["position"])
    if sum(e["kind"] == "player_spawn" for e in entities) != 1 or sum(e["kind"] == "goal" for e in entities) != 1:
        raise ValueError("one spawn and goal required")
    if not any(e["kind"] == "spring" for e in entities):
        raise ValueError("spring marker is required")

    return {"objects": len(objects), "entities": len(entities),
            "routes": len(routes), "kinds": count_by_kind,
            "runtime_status": data["runtime_status"]}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=DEFAULT)
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.path.read_text(encoding="utf-8"))),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
