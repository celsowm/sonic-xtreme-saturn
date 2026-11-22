"""Pure-Python mesh generators for the Jade Gully concept v4 (painting-faithful).

No bpy import: every function is deterministic and unit-tested on the host.
All meshes are OFFLINE ART for the Blender concept scene; they are not Saturn
collision, not exported triangles and not gameplay.

Material index conventions are documented per function so the Blender
builder can bind the painting's palette (grass checker tops, ochre/brown
checker cliffs, rocky undersides, blue hex interior, ...).
"""
import math

TOP, SIDE, BOTTOM, UNDERSIDE = 0, 1, 2, 3


def rounded_rect(cx, cy, width, depth, corner, segments=3):
    """Counter-clockwise footprint with rounded corners (XY plane)."""
    if width <= 0 or depth <= 0:
        raise ValueError("footprint needs positive size")
    corner = max(0.0, min(corner, width / 2 - 1e-6, depth / 2 - 1e-6))
    if corner == 0 or segments < 1:
        hw, hd = width / 2, depth / 2
        return [(cx - hw, cy - hd), (cx + hw, cy - hd),
                (cx + hw, cy + hd), (cx - hw, cy + hd)]
    hw, hd = width / 2 - corner, depth / 2 - corner
    centres = ((cx + hw, cy - hd, -math.pi / 2), (cx + hw, cy + hd, 0.0),
               (cx - hw, cy + hd, math.pi / 2), (cx - hw, cy - hd, math.pi))
    points = []
    for ox, oy, start in centres:
        for k in range(segments + 1):
            angle = start + (math.pi / 2) * k / segments
            points.append((ox + corner * math.cos(angle),
                           oy + corner * math.sin(angle)))
    return points


def polygon_area(polygon):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1]
                     for a, b in zip(polygon, polygon[1:] + polygon[:1]))


def prism(polygon, top, bottom):
    """Grass-capped checker column. Materials: TOP cap, SIDE walls, BOTTOM cap."""
    if top <= bottom:
        raise ValueError("prism top must be above bottom")
    if len(polygon) < 3 or polygon_area(polygon) <= 0:
        raise ValueError("prism footprint must be counter-clockwise")
    n = len(polygon)
    verts = [(x, y, top) for x, y in polygon] + [(x, y, bottom) for x, y in polygon]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    mats = [TOP, BOTTOM]
    for i in range(n):
        j = (i + 1) % n
        faces.append((n + i, n + j, j, i))
        mats.append(SIDE)
    return verts, faces, mats


def floating_island(polygon, top, band, depth):
    """Sky-bridge island: grass TOP, a vertical checker SIDE band, then a
    tapered rocky UNDERSIDE ending in a point, as painted under the clouds."""
    if band <= 0 or depth <= band:
        raise ValueError("island needs band > 0 and depth > band")
    if len(polygon) < 3 or polygon_area(polygon) <= 0:
        raise ValueError("island footprint must be counter-clockwise")
    n = len(polygon)
    cx = sum(p[0] for p in polygon) / n
    cy = sum(p[1] for p in polygon) / n
    mid = [(cx + (x - cx) * .55, cy + (y - cy) * .55) for x, y in polygon]
    verts = ([(x, y, top) for x, y in polygon] +
             [(x, y, top - band) for x, y in polygon] +
             [(x, y, top - band - (depth - band) * .55) for x, y in mid] +
             [(cx, cy, top - depth)])
    tip = len(verts) - 1
    faces = [tuple(range(n))]
    mats = [TOP]
    for i in range(n):
        j = (i + 1) % n
        faces.append((n + i, n + j, j, i))
        mats.append(SIDE)
        faces.append((2 * n + i, 2 * n + j, n + j, n + i))
        mats.append(UNDERSIDE)
        faces.append((tip, 2 * n + j, 2 * n + i))
        mats.append(UNDERSIDE)
    return verts, faces, mats


def hex_tube(cx, cy, cz, radius, inner_ratio, depth):
    """The painting's massive hexagonal loop, facing the camera along -Y.

    Materials: 0 outer green-checker shell, 1 blue running surface inside,
    2 front/back rims. The opening is in the XZ plane; depth runs along +Y.
    """
    if radius <= 0 or not 0 < inner_ratio < 1 or depth <= 0:
        raise ValueError("bad hex tube dimensions")
    rings = []
    for y in (cy - depth / 2, cy + depth / 2):
        for r in (radius, radius * inner_ratio):
            rings.append([(cx + r * math.sin(math.tau * i / 6 + math.pi / 6), y,
                           cz - r * math.cos(math.tau * i / 6 + math.pi / 6))
                          for i in range(6)])
    verts = [p for ring in rings for p in ring]
    of, inf, ob, ib = 0, 6, 12, 18  # outer/inner front, outer/inner back
    faces, mats = [], []
    for i in range(6):
        j = (i + 1) % 6
        faces.append((of + i, ob + i, ob + j, of + j)); mats.append(0)
        faces.append((inf + j, ib + j, ib + i, inf + i)); mats.append(1)
        faces.append((of + j, inf + j, inf + i, of + i)); mats.append(2)
        faces.append((ob + i, ib + i, ib + j, ob + j)); mats.append(2)
    return verts, faces, mats


def arch(cx, cy, base_z, outer_radius, thickness, width, segments=12):
    """Semicircular grass arch (Entry Hills). Span along X, extruded along Y.
    Materials: 0 grass top/outer, 1 checker sides, 2 underside."""
    if thickness <= 0 or thickness >= outer_radius or width <= 0 or segments < 3:
        raise ValueError("bad arch dimensions")
    inner = outer_radius - thickness
    verts = []
    for y in (cy - width / 2, cy + width / 2):
        for k in range(segments + 1):
            a = math.pi * k / segments
            for r in (outer_radius, inner):
                verts.append((cx - r * math.cos(a), y, base_z + r * math.sin(a)))
    per = 2 * (segments + 1)
    faces, mats = [], []
    for k in range(segments):
        o0, i0, o1, i1 = 2 * k, 2 * k + 1, 2 * k + 2, 2 * k + 3
        faces.append((o0, o1, per + o1, per + o0)); mats.append(0)
        faces.append((per + i0, per + i1, i1, i0)); mats.append(2)
        faces.append((i0, i1, o1, o0)); mats.append(1)
        faces.append((per + o0, per + o1, per + i1, per + i0)); mats.append(1)
    return verts, faces, mats


def catmull_rom(points, samples=6):
    """Smooth guide curve through every authored station (endpoints kept)."""
    if len(points) < 2 or samples < 1:
        raise ValueError("curve needs two stations and samples >= 1")
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t +
                                   (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 +
                                   (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)
                             for k in range(3)))
    out.append(tuple(points[-1]))
    return out


def polyline_length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def sample_along(points, spacing, offset=0.0):
    """Evenly spaced positions along a polyline (for rings and arrowheads)."""
    if spacing <= 0:
        raise ValueError("spacing must be positive")
    result, travelled, target = [], 0.0, offset
    for a, b in zip(points, points[1:]):
        seg = math.dist(a, b)
        while seg > 0 and target <= travelled + seg:
            t = (target - travelled) / seg
            pos = tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
            direction = tuple((b[k] - a[k]) / seg for k in range(3))
            result.append((pos, direction))
            target += spacing
        travelled += seg
    return result


def grass_mound(cx, cy, base_z, rx, ry, height, rings=6, segments=16, skirt=2.0):
    """Rolling grass hill (Entry Hills). Cosine profile: flat at the crest and
    tangent to the terrace at the rim, plus a short skirt that sinks into the
    terrace so no gap shows. Material 0 everywhere (grass checker)."""
    if rx <= 0 or ry <= 0 or height <= 0 or rings < 2 or segments < 6 or skirt <= 0:
        raise ValueError("bad mound dimensions")
    verts = [(cx, cy, base_z + height)]
    for k in range(1, rings + 1):
        s = k / rings
        z = base_z + height * .5 * (1 + math.cos(math.pi * s))
        for i in range(segments):
            a = math.tau * i / segments
            verts.append((cx + rx * s * math.cos(a), cy + ry * s * math.sin(a), z))
    for i in range(segments):
        a = math.tau * i / segments
        verts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), base_z - skirt))
    faces = []
    for i in range(segments):
        faces.append((0, 1 + i, 1 + (i + 1) % segments))
    for k in range(rings):        # ring k+1 -> ring k+2; the last pair is rim -> skirt
        a0, b0 = 1 + k * segments, 1 + (k + 1) * segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((a0 + i, b0 + i, b0 + j, a0 + j))
    return verts, faces, [TOP] * len(faces)


def slope(start, end, width, foot):
    """Grass ramp joining two terrace levels. start/end are (x, y, z) centres
    of the low and high lips. Materials: TOP grass, SIDE checker, BOTTOM."""
    (x0, y0, z0), (x1, y1, z1) = start, end
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length <= 0 or width <= 0 or foot >= min(z0, z1):
        raise ValueError("bad slope")
    sx, sy = -dy / length * width / 2, dx / length * width / 2
    top = [(x0 - sx, y0 - sy, z0), (x1 - sx, y1 - sy, z1),
           (x1 + sx, y1 + sy, z1), (x0 + sx, y0 + sy, z0)]
    if polygon_area([p[:2] for p in top]) < 0:
        top = [top[0], top[3], top[2], top[1]]
    verts = top + [(x, y, foot) for x, y, _ in top]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4)]
    mats = [TOP, BOTTOM]
    for i in range(4):
        j = (i + 1) % 4
        faces.append((4 + i, 4 + j, j, i))
        mats.append(SIDE)
    return verts, faces, mats


def spiral_steps(cx, cy, radius, z0, z1, turns, steps):
    """Stations of a spiral stair wrapped around the giant tree trunk.
    Returns [(position, tangent)], climbing counter-clockwise."""
    if radius <= 0 or z1 <= z0 or turns <= 0 or steps < 2:
        raise ValueError("bad spiral")
    out = []
    for k in range(steps):
        t = k / (steps - 1)
        a = math.tau * turns * t
        pos = (cx + radius * math.cos(a), cy + radius * math.sin(a), z0 + (z1 - z0) * t)
        rise = (z1 - z0) / (math.tau * turns * radius)
        tangent = (-math.sin(a), math.cos(a), rise)
        norm = math.sqrt(sum(c * c for c in tangent))
        out.append((pos, tuple(c / norm for c in tangent)))
    return out


def star_prism(cx, cy, cz, outer, inner, thickness, points=5):
    """Five-point bonus star facing the viewer (XZ plane, extruded along Y)."""
    if not 0 < inner < outer or thickness <= 0 or points < 3:
        raise ValueError("bad star")
    outline = []
    for k in range(points * 2):
        r = outer if k % 2 == 0 else inner
        a = math.pi / 2 + math.pi * k / points
        outline.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    n = len(outline)
    front, back = cy - thickness / 2, cy + thickness / 2
    verts = [(cx, front, cz)] + [(x, front, z) for x, z in outline] + \
            [(cx, back, cz)] + [(x, back, z) for x, z in outline]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((0, 1 + i, 1 + j))                       # front, normal -Y
        faces.append((n + 1, n + 2 + j, n + 2 + i))           # back, normal +Y
        faces.append((1 + i, n + 2 + i, n + 2 + j, 1 + j))    # side, outward
    return verts, faces, [0] * len(faces)


def mountain_range(x0, x1, y, base_z, peaks, seed=7, scale=1.0):
    """Far snow-capped range strip. Returns (verts, faces, mats) where material
    1 marks snow-cap triangles above 72% of the tallest peak, 0 rock."""
    if peaks < 2 or x1 <= x0 or scale <= 0:
        raise ValueError("mountain range needs >= 2 peaks, x1 > x0, scale > 0")
    state = seed

    def rnd():
        nonlocal state
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        return state / 0x7FFFFFFF

    step = (x1 - x0) / peaks
    ridge = []
    for i in range(peaks + 1):
        x = x0 + i * step
        ridge.append((x, y + (rnd() - .5) * 40, base_z + (70 + rnd() * 110) * scale))
        if i < peaks:
            ridge.append((x + step / 2, y + (rnd() - .5) * 30, base_z + (30 + rnd() * 40) * scale))
    top = max(p[2] for p in ridge)
    verts, faces, mats = [], [], []
    for a, b in zip(ridge, ridge[1:]):
        n = len(verts)
        verts.extend((a, b, (b[0], b[1] - 60, base_z), (a[0], a[1] - 60, base_z)))
        faces.append((n + 3, n + 2, n + 1, n))
        mats.append(0)
        peak = a if a[2] > b[2] else b
        if peak[2] > top * .72 + base_z * .28:
            n = len(verts)
            drop = (peak[2] - base_z) * .22
            # The rock face slopes 60 m toward the camera over its full
            # height; keep the cap just in front of that slope, not inside it.
            front = 60 * .22 + 1.5
            verts.extend((peak, (peak[0] - drop * .6, peak[1] - front, peak[2] - drop),
                          (peak[0] + drop * .6, peak[1] - front, peak[2] - drop)))
            faces.append((n + 1, n + 2, n))
            mats.append(1)
    return verts, faces, mats
