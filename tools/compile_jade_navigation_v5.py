"""V5 presentation navigation graph: actual route/bridge anchors, NOT Saturn collision.

Unlike painted overlays, a supported edge must have real concept walkway
geometry touching BOTH authored 3D stations. This is only a geometry
contract; no jump physics, collision testing, controller, or Saturn export.
"""
from collections import deque
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets/levels/jade_gully_concept_v4.json"

NEW_BRANCHES = (
    "village_north_decks", "village_lookout_decks",
    "sky_high_e", "sky_middle_d",
    "hex_lower_underpass", "canyon_mid_stairs", "canyon_lower_docks",
)
LOWER_ISLANDS = "lower_islands"
SUPPORT_TOLERANCE = 1.4


def distance(a, b):
    return math.dist(a, b)


def matching_walkway(a, b, walkways, tolerance=SUPPORT_TOLERANCE):
    """Match a route edge to TWO walkway endpoints, in either direction."""
    matches = []
    for walkway in walkways:
        # Authored hairpin staircases are multiple real runs, NOT one
        # straight line from first to last landing. Match each run
        # independently against the route graph, including the via points.
        stations = [walkway["from"], *walkway.get("via", []),
                    walkway["to"]]
        for p, q in zip(stations, stations[1:]):
            error = min(max(distance(a, p), distance(b, q)),
                        max(distance(a, q), distance(b, p)))
            if error <= tolerance:
                matches.append((error, walkway))
    return min(matches, key=lambda pair: pair[0])[1] if matches else None


def matching_transfer(a, b, route_id, transfers, tolerance=1e-4):
    """Aerial transfers have landing pads, not invented planks in the void."""
    matches = [t for t in transfers if
               t["route"] == route_id
               and distance(a, t["from"]) <= tolerance
               and distance(b, t["to"]) <= tolerance]
    if len(matches) > 1:
        raise ValueError("duplicate aerial transfer")
    return matches[0] if matches else None


def validate_transfers(data):
    """Require explicit aerial mode, landing object, and unverified physics."""
    transfers = data.get("navigation_transfers", [])
    names = {t["id"] for t in transfers}
    if len(names) != len(transfers):
        raise ValueError("duplicate aerial transfer id")
    routes = {r["id"]: r for r in data["routes"]}
    islands = {i["id"]: i for i in data["islands"]}
    cloud_stages = {i["id"]: i for i in data.get("sky_cloud_landings", [])}
    canyon_pads = {i["id"]: i for i in data.get("canyon_route_landings", [])}
    canyon_decks = {i["id"]: i for i in data.get("platforms", [])}
    if len(cloud_stages) != len(data.get("sky_cloud_landings", [])):
        raise ValueError("duplicate cloud landing IDs")
    if len(canyon_pads) != len(data.get("canyon_route_landings", [])):
        raise ValueError("duplicate canyon landing IDs")
    if (set(canyon_pads) & (set(cloud_stages) | set(islands) | set(canyon_decks))):
        raise ValueError("landing identifiers may not overlap")
    for pad in canyon_pads.values():
        x, y, z = pad["center"]
        if not all(math.isfinite(p) for p in (x, y, z)):
            raise ValueError("nonfinite canyon landing")
        if not 5 <= pad["radius"] <= 9:
            raise ValueError("canyon landing must have visible landing radius")
        if pad.get("material") not in ("wood", "checker_rock"):
            raise ValueError("invalid canyon landing material")
        if pad.get("collision_verified") is not False:
            raise ValueError("canyon landing is unverified for Saturn collision")
        if pad.get("region") == "hex_loop":
            if not (56 <= x <= 111 and 152 <= y <= 212):
                raise ValueError("hex lower landing outside hex footprint")
        elif pad.get("region") == "canyon_basin":
            if not (134 <= x <= 219 and 116 <= y <= 286):
                raise ValueError("canyon landing outside basin")
        else:
            raise ValueError("canyon landing in unsupported region")
    for stage in cloud_stages.values():
        if stage.get("structure") != "cloud_landing" or stage.get("tier") not in ("high", "middle", "low"):
            raise ValueError("invalid cloud landing structure/tier")
        if stage.get("region") != "sky_bridges":
            raise ValueError("cloud stages belong to Sky Bridges")
        x, y, z = stage["center"]
        if not all(math.isfinite(p) for p in (x, y, z)):
            raise ValueError("nonfinite cloud landing center")
        if not 4.5 <= stage["radius"] <= 9:
            raise ValueError("cloud landing requires a visible platform radius")
    for transfer in transfers:
        if transfer["mode"] not in ("spring", "jump", "drop"):
            raise ValueError("invalid transfer motion")
        if transfer.get("physics_verified") is not False:
            raise ValueError("transfer may not claim tested physics")
        route = routes.get(transfer["route"])
        if not route:
            raise ValueError("aerial transfer refers to absent route")
        if not any(distance(a, transfer["from"]) < 1e-4
                   and distance(b, transfer["to"]) < 1e-4
                   for a, b in zip(route["points"], route["points"][1:])):
            raise ValueError("aerial transfer must match consecutive route points")
        if transfer["landing"] == "main":
            if transfer["to"] not in data["routes"][0]["points"]:
                raise ValueError("aerial transfer must rejoin main at a real route node")
        else:
            island = islands.get(transfer["landing"])
            cloud = cloud_stages.get(transfer["landing"])
            pad = canyon_pads.get(transfer["landing"])
            deck = canyon_decks.get(transfer["landing"])
            if island is None and cloud is None and pad is None and deck is None:
                raise ValueError("aerial transfer has no named solid landing surface")
            x, y, z = transfer["to"]
            if island:
                cx, cy = island["center"]
                sx, sy = island["size"]
                if abs(x-cx) > sx*.35 or abs(y-cy) > sy*.35 or abs(z-island["top"]-.6) > 1e-3:
                    raise ValueError("aerial transfer misses its landing island")
            elif cloud:
                cx, cy, top = cloud["center"]
                if math.hypot(x-cx, y-cy) > cloud["radius"]*.35 or abs(z-top-.6) > 1e-3:
                    raise ValueError("aerial transfer misses its landing cloud platform")
            elif pad:
                cx, cy, top = pad["center"]
                if math.hypot(x-cx, y-cy) > pad["radius"]*.35 or abs(z-top-.6) > 1e-3:
                    raise ValueError("aerial transfer misses its landing canyon platform")
            else:
                cx, cy, top = deck["deck"]
                if math.hypot(x-cx, y-cy) > deck["size"]*.5 or abs(z-top-.6) > 1e-3:
                    raise ValueError("aerial transfer misses its wooden canyon deck")
        # These are design envelopes, deliberately NOT a verified ballistic
        # solution. The source painting shows short hop/spring sequences.
        dx = math.hypot(transfer["to"][0]-transfer["from"][0],
                        transfer["to"][1]-transfer["from"][1])
        if transfer["mode"] != "drop" and dx > 34:
            raise ValueError("aerial jump too long without an intermediate landing")
    return transfers


def node_id(p):
    return "p_" + "_".join(str(round(v * 10)).replace("-", "m") for v in p)


def compile_navigation(data):
    routes, walkways = data["routes"], data["walkways"]
    transfers = validate_transfers(data)
    cloud_stages = {stage["id"]: stage for stage in data.get("sky_cloud_landings", [])}
    canyon_pads = {pad["id"]: pad for pad in data.get("canyon_route_landings", [])}
    names = {route["id"] for route in routes}
    required = set(NEW_BRANCHES) | {LOWER_ISLANDS}
    if not required <= names:
        raise ValueError("missing essential village or sky circulation route")
    main = routes[0]
    if main["id"] != "main" or main["kind"] != "main":
        raise ValueError("primary line must lead the navigation graph")
    main_points = [tuple(x) for x in main["points"]]
    main_index = {p: i for i, p in enumerate(main_points)}
    all_walkway_names = [w["id"] for w in walkways]
    if len(all_walkway_names) != len(set(all_walkway_names)):
        raise ValueError("duplicate walkway ID")

    vertices, edges = {}, []
    graph = {}

    def add_vertex(point):
        key = node_id(point)
        value = list(point)
        if key in vertices and vertices[key]["position"] != value:
            raise ValueError("route nodes collide at 0.1 world units")
        vertices[key] = {"position": value,
                         "collision_verified": False}
        graph.setdefault(key, set())
        return key

    for route in routes:
        points = [tuple(p) for p in route["points"]]
        if len(points) < 2:
            raise ValueError("route must have 2+ stations")
        if route["id"] in NEW_BRANCHES:
            if tuple(points[0]) not in main_index or tuple(points[-1]) not in main_index:
                raise ValueError("new branch must split/rejoin at existing main nodes")
            if main_index[points[0]] >= main_index[points[-1]]:
                raise ValueError("new branch must rejoin AFTER departure")
            if len(points) < 3 or all(p in main_index for p in points[1:-1]):
                raise ValueError("new branch needs an off-main waypoint")
            if route.get("visual_only") is not True:
                raise ValueError("new branch may not claim collision readiness")
        if route["id"] == LOWER_ISLANDS:
            if len(points) < 6:
                raise ValueError("lower islands must have the complete 4-island chain")
        for start, finish in zip(points, points[1:]):
            first, second = add_vertex(start), add_vertex(finish)
            support = matching_walkway(start, finish, walkways)
            transfer = matching_transfer(start, finish, route["id"], transfers)
            if support and transfer:
                raise ValueError("route edge may not be both bridge and aerial jump")
            if route["id"] in required and support is None and transfer is None:
                raise ValueError("new alternate has an unsupported segment: " + route["id"])
            edge = {"from": first, "to": second, "route": route["id"],
                    "walkway_id": support["id"] if support else None,
                    "transfer_id": transfer["id"] if transfer else None,
                    "mode": support["kind"] if support else
                            (transfer["mode"] if transfer else "unverified"),
                    "landing": transfer["landing"] if transfer else None,
                    "visual_only": True, "collision_verified": False,
                    "physics_verified": False}
            edges.append(edge)
            graph[first].add(second)

    start, goal = node_id(main_points[0]), node_id(main_points[-1])
    visited = {start}
    queue = deque([start])
    while queue:
        for other in graph[queue.popleft()]:
            if other not in visited:
                visited.add(other)
                queue.append(other)
    if goal not in visited:
        raise ValueError("GOAL must remain reachable from START in presentation graph")
    if any(node_id(tuple(p)) not in visited for name in required
           for route in routes if route["id"] == name for p in route["points"]):
        raise ValueError("a new navigation branch has disconnected nodes")

    return {
        "schema_version": 1,
        "intent": "art-only route intent: walkway surfaces, untested aerial transitions; NOT Saturn collision/gameplay",
        "start": start, "goal": goal,
        "nodes": [{"id": name, **node} for name, node in sorted(vertices.items())],
        "edges": edges,
        "summary": {
            "route_count": len(routes),
            "alternate_count": sum(r["kind"] == "alternate" for r in routes),
            "walkway_count": len(walkways),
            "aerial_transfer_definitions": len(transfers),
            "cloud_landing_platforms": len(cloud_stages),
            "canyon_landing_platforms": len(canyon_pads),
            "lower_canyon_branches": sum(r["id"] in (
                "hex_lower_underpass", "canyon_mid_stairs", "canyon_lower_docks"
            ) for r in routes),
            "long_unverified_drop_edges": sum(
                e["mode"] == "drop"
                and distance(vertices[e["from"]]["position"], vertices[e["to"]]["position"]) > 36
                for e in edges
            ),
            "supported_edges": sum(e["walkway_id"] is not None for e in edges),
            "aerial_transfer_edges": sum(e["transfer_id"] is not None for e in edges),
            "unsupported_edges": sum(e["walkway_id"] is None
                                     and e["transfer_id"] is None for e in edges),
            "new_supported_branches": list(NEW_BRANCHES) + [LOWER_ISLANDS],
            "reachable_nodes_in_presentation_graph": len(visited),
        },
    }


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = compile_navigation(data)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
