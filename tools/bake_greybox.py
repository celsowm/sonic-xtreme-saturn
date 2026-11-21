"""Narrow untextured greybox adapter; no target-side OBJ parser.

Input is the companion toolkit's RH Z-up world-space OBJ and scene JSON.
Output is immutable Q16.16 C tables for LibSaturn's public scene interface.
"""
import argparse
import hashlib
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

MAX_VERTICES = 2048
MAX_FACES = 256
MAX_ENTITIES = 64
LIMIT = Decimal(256)
# A pair per object group: alternating faces get subtly different shades.
# Decorative geometry is presentation-only; its semantic groups never appear
# in the collision mesh. Indices must match src/main.c colors[].
PALETTE = {
    "main_route": (0, 3),
    "upper_route": (1, 4),
    "river_route": (0, 3),
    "ruins_route": (2, 4),
    "trunk": (2, 4),
    "canopy": (3, 3),
    "rock": (2, 4),
    "water": (5, 5),
    "meadow": (6, 6),
    "terrace": (7, 7),
}
KINDS = ("player_spawn", "ring", "spring", "checkpoint", "enemy", "goal", "camera_anchor", "prop")

def fixed(value):
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid coordinate") from exc
    if not v.is_finite() or abs(v) > LIMIT:
        raise ValueError("coordinate outside greybox range +/-256 m")
    return int((v * 65536).to_integral_value(rounding=ROUND_HALF_UP))

def convert_xyz(xyz):
    # RH Z-up -> RH Y-up via -90 degrees about X.
    x, y, z = map(fixed, xyz)
    return x, z, -y

def parse_obj(raw):
    vertices, faces = [], []
    group, serial = None, 0
    for number, line in enumerate(raw.splitlines(), 1):
        tokens = line.partition("#")[0].split()
        if not tokens:
            continue
        tag, *args = tokens
        if tag == "o" and len(args) == 1:
            group, serial = args[0], 0
        elif tag == "v" and len(args) == 3:
            vertices.append(convert_xyz(args))
            if len(vertices) > MAX_VERTICES:
                raise ValueError("vertex capacity exceeded")
        elif tag == "f" and len(args) in (3, 4) and group:
            if any(not a.isascii() or not a.isdecimal() for a in args):
                raise ValueError("only positive bare OBJ indices are supported")
            indices = [int(a) - 1 for a in args]
            if len(set(indices)) != len(indices) or any(i < 0 or i >= len(vertices) for i in indices):
                raise ValueError("invalid face indices")
            # The SDK uses cross(D-A,B-A), opposite ordinary OBJ normal.
            # Triangulate the ribbon/boxes so non-planar quads cannot warp.
            color = next((pair[serial % 2] for suffix, pair in PALETTE.items() if group.endswith("_" + suffix)), 2)
            for k in range(1, len(indices) - 1):
                a, b, c = (indices[0], indices[k+1], indices[k])
                u = tuple(vertices[b][i] - vertices[a][i] for i in range(3))
                v = tuple(vertices[c][i] - vertices[a][i] for i in range(3))
                cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
                if not any(cross):
                    raise ValueError(f"line {number}, mesh {group}, triangle {k-1}: degenerate triangle after quantization")
                faces.append((a, b, c, c, color))
                if len(faces) > MAX_FACES:
                    raise ValueError("face capacity exceeded")
            serial += 1
        else:
            raise ValueError(f"line {number}: unsupported OBJ record")
    if not vertices or not faces:
        raise ValueError("empty render mesh")
    return vertices, faces

def parse_entities(raw):
    scene = json.loads(raw, parse_float=Decimal)
    if not isinstance(scene, dict) or set(scene) != {"version","units","axes","entities"}:
        raise ValueError("invalid metadata")
    if type(scene["version"]) is not int or scene["version"] != 0 or scene["units"] != "m" or scene["axes"] != "RH_Z_UP":
        raise ValueError("unsupported scene metadata")
    if not isinstance(scene["entities"], list) or len(scene["entities"]) > MAX_ENTITIES:
        raise ValueError("entity capacity exceeded")
    entities = {}
    for item in scene["entities"]:
        if not isinstance(item, dict) or set(item) != {"id","kind","position"}:
            raise ValueError("invalid entity")
        ident, kind, pos = item["id"], item["kind"], item["position"]
        if not isinstance(ident, str) or not ident.strip() or ident in entities or kind not in KINDS:
            raise ValueError("invalid entity ID or kind")
        if not isinstance(pos, list) or len(pos) != 3 or any(type(x) not in (int, Decimal) for x in pos):
            raise ValueError("invalid entity position")
        entities[ident] = (*convert_xyz(pos), KINDS.index(kind))
    values = [entities[k] for k in sorted(entities)]
    if sum(e[3] == 0 for e in values) != 1 or sum(e[3] == 5 for e in values) != 1:
        raise ValueError("expected exactly one spawn and goal")
    return values

def emit(obj_raw, json_raw):
    vertices, faces = parse_obj(obj_raw.decode("utf-8"))
    entities = parse_entities(json_raw.decode("utf-8"))
    lines = [
        "/* Generated by bake_greybox.py; do not edit. */",
        "/* OBJ sha256: " + hashlib.sha256(obj_raw).hexdigest() + " */",
        "/* JSON sha256: " + hashlib.sha256(json_raw).hexdigest() + " */",
        "#ifndef XTREME_GENERATED_GREYBOX_H",
        "#define XTREME_GENERATED_GREYBOX_H",
        "#include <stdint.h>",
        "#include <saturn/math3d.h>",
        f"#define STAGE_FACE_COUNT {len(faces)}u",
        f"#define STAGE_ENTITY_COUNT {len(entities)}u",
        "typedef struct { uint16_t v[4]; uint8_t color; } stage_face_t;",
        "typedef struct { sat_vec3_t pos; uint8_t kind; } stage_entity_t;",
        "static const sat_vec3_t stage_vertices[] = {",
    ]
    lines += ["    {" + ", ".join(map(str, v)) + "}," for v in vertices]
    lines += ["};", "static const stage_face_t stage_faces[] = {"]
    lines += ["    {{" + ", ".join(map(str, f[:4])) + "}, " + str(f[4]) + "}," for f in faces]
    lines += ["};", "static const stage_entity_t stage_entities[] = {"]
    lines += ["    {{" + ", ".join(map(str, e[:3])) + "}, " + str(e[3]) + "}," for e in entities]
    lines += ["};", "#endif", ""]
    return "\n".join(lines).encode("ascii")

def emit_collision(raw):
    vertices, faces = parse_obj(raw.decode("utf-8"))
    lines = ["/* Generated collision mesh; SDK winding. */",
             "/* OBJ sha256: " + hashlib.sha256(raw).hexdigest() + " */",
             "#ifndef XTREME_COLLISION_H", "#define XTREME_COLLISION_H",
             "#include <saturn/collide3d.h>",
             f"#define COLLISION_VERTEX_COUNT {len(vertices)}u",
             f"#define COLLISION_FACE_COUNT {len(faces)}u",
             "static sat_vec3_t collision_vertices[] = {"]
    lines += ["    {" + ", ".join(map(str, v)) + "}," for v in vertices]
    lines += ["};", "static uint16_t collision_indices[] = {"]
    lines += ["    " + ", ".join(map(str, f[:4])) + "," for f in faces]
    lines += ["};", "#endif", ""]
    return "\n".join(lines).encode("ascii")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("obj", type=Path)
    parser.add_argument("scene", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--collision", type=Path)
    parser.add_argument("--collision-output", type=Path)
    args = parser.parse_args()
    try:
        data = emit(args.obj.read_bytes(), args.scene.read_bytes())
        if bool(args.collision) != bool(args.collision_output):
            raise ValueError("both collision paths are required")
        collision = emit_collision(args.collision.read_bytes()) if args.collision else None
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
        if collision is not None:
            args.collision_output.parent.mkdir(parents=True, exist_ok=True)
            args.collision_output.write_bytes(collision)
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))

if __name__ == "__main__":
    main()
