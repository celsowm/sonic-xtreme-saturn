"""Presentation pass for Jade Gully's editable, OFFLINE Blender concept.

The five-sector concept is not a Saturn runtime stage. This module changes
visual staging, material readability and camera previews only; it does not
touch collision, gameplay, or the qualified Adventure layout.
"""
import math


def hex_outline_points(x, y, z, radius, front_x=0.0):
    """Six-sided YZ loop facing a camera on the positive-X side."""
    if radius <= 0:
        raise ValueError("loop radius must be positive")
    vertices = [
        (x + front_x, y + radius * math.sin(2 * math.pi * i / 6 + math.pi / 6),
         z + radius * math.cos(2 * math.pi * i / 6 + math.pi / 6))
        for i in range(6)
    ]
    return vertices + [vertices[0]]


def apply_presentation(data, materials, artist):
    """Expose loops, houses and water, and keep editing annotations off renders."""
    import bpy
    from mathutils import Vector

    counts = {"showcase_loops": 0, "hut_windows": 0,
              "water_curtains": 0, "hidden_editor_labels": 0}

    # Far-side loops were partly concealed behind the terrain and the canopy.
    # Move the *visual art* group toward the positive-X camera, leaving the
    # manifest's gameplay-independent source layout unchanged.
    relocations = {
        "ridge_hex_loop": (63.0, 0.0),
        "ridge_lower_loop": (10.0, 5.0),
        "summit_loop_1": (38.0, 4.0),
        "summit_loop_2": (9.0, 5.0),
    }
    for item in data["landmarks"]:
        if item["kind"] != "hex_loop":
            continue
        ident = item["id"]
        dx, dz = relocations[ident]
        existing = [obj for obj in bpy.data.objects
                    if obj.name.startswith(ident + "_")]
        if not existing:
            raise RuntimeError("No Blender geometry for " + ident)
        for obj in existing:
            obj.location.x += dx
            obj.location.z += dz
        x, y, z = item["position"]
        radius = item["size"] * 1.10
        cx, cy, cz = x + dx, y, z + item["size"] * .72 + dz
        # Original loop is 7m deep. A wide bright edge makes the iconic
        # six-sided opening readable from a 2200px panorama and at close range.
        for face_offset in (8.8, -.3):
            for factor in (1.0, .70):
                artist.line(
                    ident + "_showcase_rim_%d_%d" % (
                        int(face_offset * 10), int(factor * 100)),
                    hex_outline_points(cx, cy, cz, radius * factor,
                                       face_offset),
                    materials["loop_border"], .87 if factor == 1 else .44)
        ground = artist.at_z(cx, cy, data)
        bottom = cz - radius
        if bottom > ground + 1:
            depth = bottom - ground
            artist.cylinder(ident + "_plinth", cx, cy, ground + depth / 2,
                            3.2, depth, materials["rock"], 8)
        counts["showcase_loops"] += 1

    # Thatch windows face the near (+X) camera, instead of vanishing beneath
    # unlit foliage. Compute each deck elevation exactly as the builder does.
    for item in data["landmarks"]:
        if item["kind"] != "treehouse":
            continue
        x, y, z = item["position"]
        size = item["size"]
        deck = max(z, artist.at_z(x, y, data) + size * 1.45)
        for k, shift in enumerate((-.26, .26)):
            window = artist.box(
                item["id"] + "_lit_window_" + str(k),
                (x + size * .625, y + size * shift, deck + 4.4),
                (.24, size * .19, 2.9), materials["warm_window"])
            window["stage_role"] = "concept_visual_only"
            counts["hut_windows"] += 1

    # The 10:17 screenshot shows almost no recognizable waterfalls.
    # Make three wide, bright near-bank curtains (YZ plane) visible on the
    # nearer canyon wall, with foam and a splash pool at the base.
    for n, (x, y, top_z, fall_height, width) in enumerate((
            (94, 343, 54, 37, 18),
            (95, 376, 48, 46, 22),
            (94, 402, 61, 43, 15))):
        vertices = (
            (x, y - width / 2, top_z),
            (x, y + width / 2, top_z),
            (x + 2.4, y + width / 2, top_z - fall_height),
            (x + 2.4, y - width / 2, top_z - fall_height))
        artist.mesh("foreground_falls_%d_turquoise"%n,
                    vertices, ((0,1,2,3),), [materials["water"]])
        for k in range(4):
            yy = y + width * (k / 3 - .5)
            artist.line("foreground_falls_%d_whitewater_%d"%(n,k),
                        [(x + .15, yy, top_z),
                         (x + 2.75, yy, top_z - fall_height)],
                        materials["foam"], .25)
        artist.cylinder("foreground_falls_%d_splash"%n,
                        x + 3, y, top_z - fall_height + .75,
                        width * .56, 1.4, materials["water"], 14)
        counts["water_curtains"] += 1

    # One broad, warmly coloured path makes the intended route visible over
    # the grass. Keep the existing three semantic line colours for branches.
    artist.line("showcase_golden_main_route",
                [(x, y, z + 1.4) for x,y,z in data["routes"][0]["points"]],
                materials["gold"], .83)

    # The five names in the screenshot were painted across the landscape.
    # Preserve them as editable Blender objects but exclude from output art.
    for obj in bpy.data.objects:
        if obj.get("stage_role") == "concept_editor_annotation":
            obj.hide_render = True
            counts["hidden_editor_labels"] += 1

    # Source Kenney terrain remains packed. Principled emission adds enough
    # cyan to distinguish running water from very dark rocks and shadows.
    def glow(key, color, strength):
        shader = materials[key].node_tree.nodes.get("Principled BSDF")
        if shader is None:
            return
        inputs = shader.inputs
        socket = inputs.get("Emission Color") or inputs.get("Emission")
        if socket is not None:
            socket.default_value = (*color,1)
        intensity = inputs.get("Emission Strength")
        if intensity is not None:
            intensity.default_value = strength
    glow("water", (.08,.68,.78), .65)
    glow("foam", (.75,.95,.96), .23)
    glow("gold", (.99,.59,.08), .42)
    glow("loop_border", (.99,.52,.07), .66)
    glow("warm_window", (1.0,.48,.09), .85)
    glow("emerald", (.05,.88,.35), .90)
    return counts


def create_region_cameras(data, artist):
    """Named sector-portrait cameras for genuine, inspectable Blender renders."""
    import bpy
    from mathutils import Vector
    cameras = {}
    for sector in data["sectors"]:
        mid_y = sum(sector["y_range"]) / 2
        mid_z = artist.at_z(0, mid_y, data) + 19
        location = (210, mid_y - 104, mid_z + 158)
        target = Vector((0, mid_y, mid_z))
        bpy.ops.object.camera_add(location=location)
        cam = bpy.context.object
        cam.name = "JG_Preview_" + sector["id"]
        cam.rotation_euler = (target-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = 208
        cameras[sector["id"]] = cam
    return cameras
