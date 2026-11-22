"""Visual setpieces for the full five-sector Jade Gully Blender concept.

Art-only geometry. Never feed the combined scene into the single-stage
Saturn baker: the classic/adventure Ymir-validated routes are separate.
"""
import math
import bpy
from mathutils import Vector

from tools.jade_concept_geometry import mesa_mesh, ribbon_mesh, halfpipe_mesh


def _tree_crown(name, x, y, z, radius, material):
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1, radius=radius, location=(x, y, z))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (1.2, 1.05, .58)
    obj.data.materials.append(material)
    obj["stage_role"] = "concept_visual_only"
    return obj


def build_setpieces(data, materials, at_z, tree, mesh, cylinder, box,
                    line, ring):
    """Build the missing landmarks in the same coordinates as the manifest.

    Functions are explicit dependencies for easy reuse and for keeping the
    main Blender authoring script small. All objects are decorative only.
    """
    stats = {"mesas": 0, "half_pipes": 0, "river_surfaces": 0,
             "large_tree_crowns": 0, "springs": 0, "monitors": 0,
             "bonus_rings": 0, "summit_gems": 0}

    # Break the vertical striped terrain wall into layered checkerboard
    # landmarks. A plateau is positioned relative to the actual terrain
    # surface rather than at a fixed, possibly buried, absolute altitude.
    mesas = (
        ("base_garden", -56, 70, 18, 15),
        ("base_lookout", 55, 87, 16, 15),
        ("ridge_north", -60, 124, 23, 24),
        ("ridge_loop_buttress", 58, 188, 25, 22),
        ("bamboo_canopy_left", -62, 229, 19, 17),
        ("bamboo_balcony", 63, 301, 20, 18),
        ("gully_high_bank", -62, 337, 26, 25),
        ("gully_wide_bank", 64, 395, 26, 21),
        ("summit_mid", -58, 438, 22, 21),
        ("summit_peak", 56, 481, 23, 22),
    )
    for name, x, y, radius, rise in mesas:
        foot = at_z(x, y, data) - 3.5
        verts, faces, slots = mesa_mesh(x, y, foot, radius, rise)
        plateau = mesh("scenic_mesa_" + name, verts, faces,
                       [materials["grass"], materials["checker_brown"],
                        materials["checker_green"]], slots)
        plateau["concept_sector"] = next(
            sec["id"] for sec in data["sectors"]
            if sec["y_range"][0] <= y <= sec["y_range"][1])
        tree("scenic_palm_" + name, x + radius * .27,
             y - radius * .18, foot + rise,
             11 + len(name) % 5 * 2, materials)
        stats["mesas"] += 1

    # Actual U-shaped troughs instead of narrow green lines. These are
    # visual references, not a validated loop/gravity movement controller.
    for ident, start, end, radius in (
        ("bamboo_halfpipe_main", (-12, 211, 49), (-3, 297, 88), 6.5),
        ("bamboo_halfpipe_upper", (24, 241, 78), (3, 291, 88), 4.4),
    ):
        verts, faces, slots = halfpipe_mesh(start, end, radius)
        mesh(ident + "_curved_gutter", verts, faces,
             [materials["bamboo"], materials["roof"]], slots)
        for side in (-1, 1):
            line(ident + "_rim_" + str(side), [
                (start[0] + side * radius, start[1], start[2] + radius),
                (end[0] + side * radius, end[1], end[2] + radius)],
                materials["wood"], .23)
        stats["half_pipes"] += 1

    # A river must be a visible surface, not a thin debug curve. Its deck
    # follows the authored terrain so none of the wide sheets gets buried.
    river_xy = ((37, 320), (43, 337), (47, 351), (35, 369),
                (28, 384), (27, 395), (17, 410))
    river = [(x, y, at_z(x, y, data) + 2.0) for x, y in river_xy]
    verts, faces = ribbon_mesh(river, 5.4)
    mesh("gully_current_broad_river", verts, faces, [materials["water"]])
    for side in (-1, 1):
        line("river_foam_edge_" + str(side),
             [(p[0] + side * 5.5, p[1], p[2] + .45) for p in river],
             materials["foam"], .17)
    stats["river_surfaces"] += 1

    # The prior tree village was three huts on isolated upright sticks.
    # Build one recognizable central ancient tree and a layered broad crown.
    gx, gy = 49, 268
    base = at_z(gx, gy, data) - 5
    cylinder("ancient_bamboo_worldtree_trunk", gx, gy, base + 32,
             6.8, 69, materials["wood"], 12)
    for i in range(8):
        angle = 2 * math.pi * i / 8
        _tree_crown(
            "ancient_bamboo_worldtree_crown_%02d" % i,
            gx + math.cos(angle) * 16,
            gy + math.sin(angle) * 17,
            base + 74 + (i % 3) * 4,
            17, materials["foliage"])
        stats["large_tree_crowns"] += 1

    # A recognizable starting base: dome exists in the manifest already.
    bx, by = -48, 39
    bz = at_z(bx, by, data) + 12
    cylinder("sonic_base_satellite_mast", bx, by, bz + 4,
             .65, 9, materials["rock"], 8)
    bpy.ops.mesh.primitive_cone_add(
        vertices=20, radius1=6, radius2=.5,
        depth=2.2, location=(bx, by, bz + 9))
    dish = bpy.context.object
    dish.name = "sonic_base_satellite_dish"
    dish.rotation_euler[1] = -.38
    dish.data.materials.append(materials["foam"])
    dish["stage_role"] = "concept_visual_only"

    # The missing visible gameplay vocabulary. These are scenery markers,
    # not working spring impulses or item-collection logic.
    for j in (2, 5, 10, 15, 20, 23):
        x, y, z = data["routes"][0]["points"][j]
        cylinder("spring_%02d_housing" % j, x + 5, y, z + 1.0,
                 2.3, 1.5, materials["rock"], 10)
        cylinder("spring_%02d_red_pad" % j, x + 5, y, z + 1.95,
                 2.25, .45, materials["red"], 10)
        stats["springs"] += 1
    for j in (3, 8, 14, 19):
        x, y, z = data["routes"][0]["points"][j]
        box("monitor_%02d_body" % j,
            (x - 5, y, z + 1.8), (3.3, 3.3, 3.6), materials["rock"])
        box("monitor_%02d_screen" % j,
            (x - 3.27, y, z + 2.0), (.21, 2.5, 2.4), materials["cyan"])
        stats["monitors"] += 1

    # Route-based ring arcs are visible from the panorama. Flat debug
    # editor markers from the old implementation remain untouched.
    for route in data["routes"]:
        fractions = (.33, .66) if route["kind"] == "risk" else (
            .25, .5, .75)
        for i, (a, b) in enumerate(zip(route["points"], route["points"][1:])):
            for j, t in enumerate(fractions):
                x = a[0] + (b[0] - a[0]) * t
                y = a[1] + (b[1] - a[1]) * t
                z = a[2] + (b[2] - a[2]) * t
                ring("route_bonus_ring_%s_%02d_%d" % (route["id"], i, j),
                     x, y, z + 3.7, materials, radius=1.12)
                stats["bonus_rings"] += 1

    # A large visible summit reward above the finish; this is a visual
    # emerald sculpture, not a real game pickup.
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1, radius=9, location=(3, 512, 158))
    gem = bpy.context.object
    gem.name = "jade_summit_goal_emerald"
    gem.scale = (.8, .8, 1.58)
    gem.data.materials.append(materials["emerald"])
    gem["stage_role"] = "concept_visual_only"
    stats["summit_gems"] += 1
    return stats
