"""Original Jade Gully greybox. Run in Blender background mode.

blender -b --factory-startup --python-exit-code 1 --python tools/create_jade_gully.py -- /path/to/libsaturn-blender build/jade-gully
"""
import json
import math
import sys
from pathlib import Path
import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) != 2:
    raise SystemExit("expected TOOLKIT_CHECKOUT OUTPUT_DIRECTORY")
toolkit, out = map(lambda value: Path(value).resolve(), args)
sys.path.insert(0, str(toolkit))
from libsaturn_toolkit.exporter import export_bundle

# (x, y, z, half width). Metres, Blender RH Z-up.
# Deliberately simple open greybox, not a reconstruction of Sega geometry.
MAIN = [
    (0, 0, 10, 4), (0, 12, 9, 4), (3, 25, 5, 4),
    (8, 38, 1, 4), (13, 51, 1, 4), (12, 65, 3, 5),
    (7, 78, 5, 4), (0, 91, 5, 4), (-4, 104, 2, 4),
    (-4, 118, 0, 5), (0, 132, 1, 5),
]
# Diverges from main station 2; rejoins at main station 6.
UPPER = [
    MAIN[2], (-7, 34, 7, 3), (-12, 47, 9, 3),
    (-10, 62, 8, 3), MAIN[6],
]

def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    return mat

def ribbon(name, points, mat):
    verts, faces = [], []
    for i, (x, y, z, width) in enumerate(points):
        before = points[max(0, i - 1)]
        after = points[min(len(points) - 1, i + 1)]
        dx, dy = after[0] - before[0], after[1] - before[1]
        length = math.hypot(dx, dy)
        if length == 0:
            raise ValueError("coincident route stations")
        rx, ry = dy / length * width, -dx / length * width
        verts.extend([(x - rx, y - ry, z), (x + rx, y + ry, z)])
        if i:
            n = i * 2
            faces.append((n - 2, n - 1, n + 1, n))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj["saturn_mesh"] = "render"
    return obj

def collision_copy(obj):
    collision = obj.copy()
    collision.name = obj.name + "_collision"
    # Shared topology intentionally; object-specific role is independent.
    bpy.context.collection.objects.link(collision)
    collision["saturn_mesh"] = "collision"
    collision.hide_render = True
    collision.display_type = "WIRE"
    return collision

def marker(ident, kind, location):
    obj = bpy.data.objects.new(ident, None)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = 0.5
    obj["saturn_id"] = ident
    obj["saturn_kind"] = kind
    return obj

def decor(name, location, dimensions, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    obj.data.materials.append(mat)
    obj["saturn_mesh"] = "render"
    return obj

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    grass = material("Greybox grass", (0.22, 0.56, 0.18))
    upper = material("Greybox upper path", (0.60, 0.45, 0.17))
    stone = material("Greybox stone", (0.35, 0.31, 0.25))
    collision_copy(ribbon("main_route", MAIN, grass))
    collision_copy(ribbon("upper_route", UPPER, upper))
    marker("spawn", "player_spawn", (0, 2, 11))
    marker("checkpoint_01", "checkpoint", (12, 65, 4))
    marker("spring_01", "spring", (0, 91, 5.5))
    marker("enemy_01", "enemy", (8, 38, 2))
    marker("camera_01", "camera_anchor", (0, 80, 12))
    marker("goal", "goal", (0, 129, 2))
    for i, (x, y, z, _) in enumerate(MAIN[1:-1]):
        marker(f"ring_main_{i:02d}", "ring", (x, y, z + 1))
    for i, (x, y, z, _) in enumerate(UPPER[1:-1]):
        marker(f"ring_upper_{i:02d}", "ring", (x, y, z + 1))
    for i in range(3):
        decor(f"ruin_left_{i}", (-11, 104 + 5 * i, 2.5), (2, 2, 5), stone)
        decor(f"ruin_right_{i}", (3, 104 + 5 * i, 2.5), (2, 2, 5), stone)
    bpy.context.view_layer.update()
    out.mkdir(parents=True, exist_ok=True)
    paths = export_bundle(bpy.context, out / "jade_gully.json")
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "jade_gully.blend"))
    data = json.loads(paths[0].read_text())
    assert sum(e["kind"] == "player_spawn" for e in data["entities"]) == 1
    assert sum(e["kind"] == "goal" for e in data["entities"]) == 1
    print(f"Greybox generated: {len(data['entities'])} entities")
    print("Authoring outputs only; no Saturn runtime qualification.")

if __name__ == "__main__":
    main()
