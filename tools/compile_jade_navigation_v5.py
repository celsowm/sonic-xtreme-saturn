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
)
LOWER_ISLANDS = "lower_islands"
SUPPORT_TOLERANCE = 1.4


def distance(a, b):
    return math.dist(a, b)


def matching_walkway(a, b, walkways, tolerance=SUPPORT_TOLERANCE):
    """Match a route edge to TWO walkway endpoints, in either direction."""
    matches = []
    for walkway in walkways:
        p, q = walkway["from"], walkway["to"]
        error = min(max(distance(a, p), distance(b, q)),
                    max(distance(a, q), distance(b, p)))
        if error <= tolerance:
            matches.append((error, walkway))
    return min(matches, key=lambda pair: pair[0])[1] if matches else None


def node_id(p):
    return "p_" + "_".join(str(round(v * 10)).replace("-", "m") for v in p)


def compile_navigation(data):
    routes, walkways = data["routes"], data["walkways"]
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
            if route["id"] in required and support is None:
                raise ValueError("new alternate has an unsupported segment: " + route["id"])
            edge = {"from": first, "to": second, "route": route["id"],
                    "walkway_id": support["id"] if support else None,
                    "mode": support["kind"] if support else "unverified",
                    "visual_only": True, "collision_verified": False}
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
        "intent": "art-only walkability candidate; NOT exported Saturn collision or verified gameplay",
        "start": start, "goal": goal,
        "nodes": [{"id": name, **node} for name, node in sorted(vertices.items())],
        "edges": edges,
        "summary": {
            "route_count": len(routes),
            "alternate_count": sum(r["kind"] == "alternate" for r in routes),
            "walkway_count": len(walkways),
            "supported_edges": sum(e["walkway_id"] is not None for e in edges),
            "unsupported_edges": sum(e["walkway_id"] is None for e in edges),
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
