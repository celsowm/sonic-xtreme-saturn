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



def organic_footprint(cx, cy, width, depth, seed=0, segments=28, roughness=.12):
    """CCW irregular superellipse for scenic cliffs, with bounded authored size.

    Unlike rounded_rect this varies outline at multiple frequencies and uses
    different phases per terrace. It stays star-shaped (no self intersection),
    centred and inside the specified XY bounding rectangle. ART geometry only.
    """
    if width <= 0 or depth <= 0 or segments < 12 or not 0 <= roughness <= .24:
        raise ValueError('bad organic footprint')
    phase = (int(seed) % 997) * (math.tau / 997)
    power = 2.0 / (2.8 + (int(seed) % 5) * .18)
    points = []
    for k in range(segments):
        a = math.tau * k / segments
        # Small-scale coastline irregularity, not random spikes.
        wobble = 1 - roughness * (.48 + .28 * math.sin(3 * a + phase)
                                    + .24 * math.sin(5 * a - 1.3 * phase))
        wobble = min(1.0, max(.75, wobble))
        c, sn = math.cos(a), math.sin(a)
        x = cx + width * .5 * math.copysign(abs(c) ** power, c) * wobble
        y = cy + depth * .5 * math.copysign(abs(sn) ** power, sn) * wobble
        points.append((x, y))
    return points


def stratified_plateau(polygon, top, bottom, lip=1.4):
    """Organic grass ledge with overhang, sloping ochre wall and rocky foot.

    Ring levels are not extruded vertical copies: an offset lip, narrowing
    midsection and tapered foot break the shoebox silhouette. Materials:
    0 grass, 1 checker wall, 2 rocky lower wall/cap. All faces point outward.
    """
    if len(polygon) < 12 or polygon_area(polygon) <= 0 or top - bottom <= 10:
        raise ValueError('bad plateau footprint/height')
    if lip <= 0 or lip >= (top - bottom) * .25:
        raise ValueError('bad ledge lip')
    cx = sum(x for x, _ in polygon) / len(polygon)
    cy = sum(y for _, y in polygon) / len(polygon)
    height = top - bottom
    levels = (
        (top, 1.0),
        (top - lip, 1.045),
        (top - min(height * .32, 17.0), .90),
        (bottom, .62),
    )
    verts = []
    for z, scale in levels:
        verts.extend((cx + (x - cx) * scale, cy + (y - cy) * scale, z)
                     for x, y in polygon)
    n = len(polygon)
    faces = [tuple(range(n)), tuple(range(4*n-1, 3*n-1, -1))]
    mats = [TOP, BOTTOM]
    for band in range(3):
        up, low = band * n, (band + 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces.append((low + i, low + j, up + j, up + i))
            mats.append(SIDE if band < 2 else BOTTOM)
    return verts, faces, mats


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


def canyon_rim_wall(stations, bottom=-52.0):
    """A continuous eroded canyon wall rather than stacked cuboid columns.

    Stations are (x, y, top_z) in increasing Y order on the far/right bank.
    Seven linked strata form overhanging grass lips, inset orange checker
    cliffs and a low rock shelf. Each row shares vertices with adjacent
    segments: no visual gap between authored stations. Blender ART only;
    not automatically walkable and not Saturn collision geometry.
    Material 0 = grass rim, 1 = checker canyon wall, 2 = bedrock.
    """
    if len(stations) < 3 or any(len(p) != 3 for p in stations):
        raise ValueError('canyon wall requires at least three XYZ stations')
    if any(not all(math.isfinite(v) for v in p) for p in stations):
        raise ValueError('canyon wall requires finite station coordinates')
    if any(b[1] <= a[1] for a, b in zip(stations, stations[1:])):
        raise ValueError('canyon stations must progress along Y')
    if bottom >= min(p[2] for p in stations) - 32:
        raise ValueError('canyon foot too high for shelf strata')
    # Heights are relative to the local authored top; the last station may
    # be significantly higher without introducing rigid, flat-topped boxes.
    bands = ((0.0, 0.0), (-2.0, -1.5), (-6.0, 1.6),
             (-17.0, 4.5), (-20.0, 0.4), (-27.0, 3.2),
             (-38.0, 6.0))
    verts = []
    for dx, dz in bands:
        for i, (x, y, top) in enumerate(stations):
            # Checker faces are no longer precisely vertical or planar.
            weather = .8 * math.sin(i * 1.47 + dz * .17)
            verts.append((x + dx + weather, y,
                          top + dz))
    # The fixed foot is deep under the cloud plane, blending into jungle.
    for i, (x, y, top) in enumerate(stations):
        verts.append((x + 8 + 1.4 * math.sin(i * 1.31), y, bottom))
    n = len(stations)
    faces, mats = [], []
    for band in range(len(bands)):
        offset0, offset1 = band*n, (band+1)*n
        for i in range(n-1):
            # Close the wall across every station pair, including ledges;
            # one coherent polygon strip per stratum, no separate cubes.
            faces.append((offset0+i, offset0+i+1,
                          offset1+i+1, offset1+i))
            mats.append(0 if band == 0 else (2 if band >= 5 else 1))
    # A narrow grass cap makes the rim readable against the sky.
    for i in range(n - 1):
        a, b = i, i+1
        faces.append((a, b, len(verts), len(verts)+1))
        # Additional cap vertices follow the same station boundaries.
        mats.append(0)
    # Cap vertices need to be added after main strips: the cap shares the
    # near edge and extends 2.8m back to meet the far-bank vegetation.
    for x, y, z in stations:
        verts.append((x+2.8, y, z-.35))
    cap_start = (len(bands)+1)*n
    for i in range(n-1):
        faces[len(bands)*(n-1)+i] = (i, i+1, cap_start+i+1, cap_start+i)
    return verts, faces, mats


def scenic_walkway_stations(start, end, kind, curvature=0.0, segments=12):
    """Author a real deck centreline, with exact original junction anchors.

    Previously the editor created detached, pencil-straight plank flights.
    The route editor now constructs a single curved deck between the authored
    landing points. Curvature is deliberately bounded; endpoints NEVER move.
    The steepest routes remain gameplay-unverified even if their geometry
    exists. For aerial transfers use navigation_transfers instead, NEVER
    build a faux checker bridge across open sky.
    """
    if kind not in ('stairs', 'rope', 'plank', 'checker'):
        raise ValueError('walkway must have solid surface kind')
    if len(start) != 3 or len(end) != 3:
        raise ValueError('walkway needs XYZ endpoints')
    if not all(math.isfinite(x) for x in tuple(start) + tuple(end)):
        raise ValueError('nonfinite walkway endpoint')
    if segments < 4 or segments > 80:
        raise ValueError('walkway segment count out of range')
    if not math.isfinite(curvature):
        raise ValueError('nonfinite walkway bend')
    dx, dy, dz = (end[i] - start[i] for i in range(3))
    planar = math.hypot(dx, dy)
    if planar < 2:
        raise ValueError('walkway endpoints too close')
    if abs(curvature) > planar * .22:
        raise ValueError('walkway curvature too large for safe deck sweep')
    nx, ny = -dy / planar, dx / planar
    stations = []
    for i in range(segments + 1):
        t = i / segments
        # Bulge to one side with a gentle S near landings; exact anchors
        # avoid unsightly steps or gaps against treehouse and island decks.
        bend = curvature * math.sin(math.pi * t) * (0.7 + 0.3 * math.sin(2*math.pi*t)**2)
        stations.append((start[0] + dx*t + nx*bend,
                         start[1] + dy*t + ny*bend,
                         start[2] + dz*t))
    stations[0], stations[-1] = tuple(start), tuple(end)
    return stations


def bridge_deck(stations, width=7.0, thickness=3.0):
    """Solid, visibly connected approach deck following authored route points.

    Unlike a floating guide line, its grass cap, checker walls and bottom
    all meet *exactly* at the supplied 3D station endpoints. In particular
    the hex-adjacent stations can be tilted by the presentation transform
    BEFORE calling this function. Returns (vertices, faces, materials).
    Offline art only; no collision or gravity-transition implementation.
    """
    if len(stations) < 2 or width <= 0 or thickness <= 0:
        raise ValueError('bridge needs 2+ stations and positive dimensions')
    if any(len(p) != 3 or not all(math.isfinite(v) for v in p) for p in stations):
        raise ValueError('bridge stations must be finite XYZ positions')
    verts = []
    for i, p in enumerate(stations):
        previous = stations[max(0, i - 1)]
        following = stations[min(len(stations) - 1, i + 1)]
        dx, dy = following[0] - previous[0], following[1] - previous[1]
        length = math.hypot(dx, dy)
        if length < 1e-5:
            raise ValueError('bridge has degenerate XY tangent')
        nx, ny = -dy / length * width / 2, dx / length * width / 2
        verts.extend(((p[0] + nx, p[1] + ny, p[2]),
                      (p[0] - nx, p[1] - ny, p[2])))
    n = len(stations) * 2
    verts += [(x, y, z - thickness) for x, y, z in verts]
    faces, mats = [], []
    for i in range(len(stations) - 1):
        a = i * 2
        faces.extend(((a, a+1, a+3, a+2),
                      (n+a+2, n+a+3, n+a+1, n+a),
                      (n+a, a, a+2, n+a+2),
                      (a+1, n+a+1, n+a+3, a+3)))
        mats.extend((TOP, BOTTOM, SIDE, SIDE))
    faces.extend(((n, n+1, 1, 0), (n-2, n-1, 2*n-1, 2*n-2)))
    mats.extend((SIDE, SIDE))
    return verts, faces, mats


def treehouse_thatch_roof(cx, cy, base_z, radius, seed=0, segments=16):
    """Broad uneven tiered-thatched pavilion roof, not a tall cone.

    The eaves turn slightly upward at four organic corner lobes. The top
    rises only 0.46*radius, giving the Tree Village the low, layered roofs
    of the approved painting. 0=gold thatch, 1=shadowed fringe, 2=highlight.
    Deterministic Blender concept ART, not Saturn geometry.
    """
    if radius <= 0 or segments < 12:
        raise ValueError('invalid hut roof shape')
    phase = ((int(seed) % 1021) / 1021.0) * math.tau
    profile = [(1.12, .03), (1.01, .115), (.82, .20),
               (.57, .30), (.28, .405)]
    vertices = []
    for ring, (rr, zz) in enumerate(profile):
        for k in range(segments):
            a = math.tau * k / segments
            lobe = math.sin(4*a + phase)
            wobble = .035 * math.sin(7*a - phase)
            r = radius * rr * (1 + wobble)
            lift = (max(0.0, lobe) * .065 if ring == 0 else
                    .018 * math.sin(3*a + phase))
            vertices.append((cx + r*math.cos(a),
                             cy + r*math.sin(a),
                             base_z + radius*(zz + lift)))
    tip = len(vertices)
    vertices.append((cx, cy, base_z + .46*radius))
    faces, mats = [], []
    for ring in range(len(profile) - 1):
        for k in range(segments):
            n = (k+1) % segments
            faces.append((ring*segments+k, ring*segments+n,
                          (ring+1)*segments+n, (ring+1)*segments+k))
            mats.append(1 if ring == 0 else
                        (2 if ring == 2 and k % 4 == 0 else 0))
    for k in range(segments):
        n = (k+1) % segments
        faces.append(((len(profile)-1)*segments+k,
                      (len(profile)-1)*segments+n, tip))
        mats.append(0)
    return vertices, faces, mats


def river_ribbon(stations, widths, z):
    """Water surface flowing between canyon ledges; not a rectangular slab.

    Centreline stations must progress in Y. Width may vary at each bend.
    Water occupies one continuous strip with exact shared vertices.
    """
    if len(stations) < 3 or len(stations) != len(widths):
        raise ValueError('river requires matching centreline and widths')
    if not math.isfinite(z) or any(not math.isfinite(q) or q <= 0 for q in widths):
        raise ValueError('river requires positive finite widths and elevation')
    if any(len(p) != 2 or not all(math.isfinite(c) for c in p) for p in stations):
        raise ValueError('river stations must be finite XY points')
    if any(b[1] <= a[1] for a, b in zip(stations, stations[1:])):
        raise ValueError('river must progress along Y')
    vertices = []
    for i, (x,y) in enumerate(stations):
        x0,y0 = stations[max(0,i-1)]
        x1,y1 = stations[min(len(stations)-1,i+1)]
        dx,dy = x1-x0,y1-y0
        length = math.hypot(dx,dy)
        if length <= 1e-8:
            raise ValueError('degenerate river centreline')
        nx,ny = -dy/length*widths[i]/2, dx/length*widths[i]/2
        vertices.extend(((x+nx,y+ny,z),(x-nx,y-ny,z)))
    faces = []
    for i in range(len(stations)-1):
        a = i*2
        faces.append((a,a+1,a+3,a+2))
    return vertices, faces, [TOP]*len(faces)


def layered_leaf_canopies(blobs, segments=9):
    """Faceted leafy crowns with irregular radial silhouette, NOT icospheres.

    Each input is (x, y, z, radius, sx, sy, sz, material_index), matching
    Blender's old blob_field data contract. Three height-offset polygonal
    outlines plus an apex produce broad organic leaf fans with dark pockets,
    instead of a uniform field of billiard-ball foliage. No bpy dependency;
    deterministic on all Python implementations.
    """
    if segments < 7 or segments > 24:
        raise ValueError('canopy segments outside low-poly range')
    vertices, faces, mats = [], [], []
    for idx, blob in enumerate(blobs):
        if len(blob) != 8:
            raise ValueError('canopy blob requires eight parameters')
        x, y, z, radius, sx, sy, sz, material = blob
        if not all(isinstance(v, (int, float)) and math.isfinite(v)
                   for v in blob) or min(radius, sx, sy, sz) <= 0:
            raise ValueError('canopy needs finite positive dimensions')
        if int(material) != material or material < 0:
            raise ValueError('canopy material index must be a nonnegative integer')
        n = len(vertices)
        phase = idx * 2.3999632297
        for level, (radial, rise) in enumerate((
                (.66, -.48), (1.05, -.12), (.88, .37))):
            for j in range(segments):
                angle = math.tau * j / segments + phase
                wobble = (1 + .13 * math.sin(3*angle + idx*.77)
                            + .09 * math.sin(5*angle - idx*1.31))
                rr = radius * radial * wobble
                vertices.append((x + math.cos(angle) * rr * sx,
                                 y + math.sin(angle) * rr * sy,
                                 z + radius * sz * (rise
                                        + .045*math.sin(4*angle + idx))))
        tip = n + 3*segments
        vertices.append((x + radius*sx*.09*math.sin(phase),
                         y + radius*sy*.09*math.cos(phase),
                         z + radius*sz*.81))
        bottom = len(vertices)
        vertices.append((x, y, z - radius*sz*.50))
        for ring in range(2):
            for j in range(segments):
                k = (j+1) % segments
                faces.append((n+ring*segments+j,
                              n+ring*segments+k,
                              n+(ring+1)*segments+k,
                              n+(ring+1)*segments+j))
                mats.append(int(material))
        for j in range(segments):
            k = (j+1) % segments
            faces.append((n+2*segments+j, n+2*segments+k, tip))
            mats.append(int(material))
            faces.append((bottom, n+k, n+j))
            mats.append(int(material))
    return vertices, faces, mats


def cumulus_landing_mesh(cx, cy, top, radius, seed=0, segments=20):
    """Layered cloud landing with a *flat* traversable-looking top silhouette.

    The old cloud stage was an extruded round puck. Five connected contours
    give cloud banks a low uneven rim, visible blue underside and distinct
    solid landing surface. This remains concept art, not Saturn collision.
    Material 0: top, 1: lit rim, 2: blue body, 3: underside.
    """
    if not all(math.isfinite(v) for v in (cx, cy, top, radius)):
        raise ValueError('cloud landing coordinates must be finite')
    if not 4.5 <= radius <= 9 or segments < 16 or segments > 48:
        raise ValueError('cloud landing radius or segments out of range')
    poly = organic_footprint(cx, cy, radius*2, radius*1.86,
                             seed=seed, segments=segments, roughness=.16)
    levels = ((top, .94), (top-.62, 1.06), (top-1.70, 1.20),
              (top-3.22, .98), (top-5.30, .54))
    verts = []
    for z, scale in levels:
        verts.extend((cx + (x-cx)*scale, cy + (y-cy)*scale, z)
                     for x, y in poly)
    n = len(poly)
    faces = [tuple(range(n)), tuple(range(len(levels)*n-1, (len(levels)-1)*n-1, -1))]
    mats = [0, 3]
    for band in range(len(levels)-1):
        hi = band*n
        low = (band+1)*n
        for j in range(n):
            k = (j+1) % n
            faces.append((low+j, low+k, hi+k, hi+j))
            mats.append(1 if band==0 else (2 if band < 3 else 3))
    return verts, faces, mats


def village_branch_paths(tree_base, hut_decks):
    """Deterministic woody supports connecting each treehouse to the trunk.

    Returns one tapered-looking curved path per hut with the terminal point
    tucked directly beneath its deck. This is visual infrastructure only.
    """
    if len(tree_base) != 3:
        raise ValueError('tree base must be XYZ')
    bx, by, bz = tree_base
    paths = {}
    for name, deck in hut_decks:
        if name in paths or len(deck) != 3:
            raise ValueError('duplicate or malformed village deck')
        x, y, z = deck
        if z <= bz + 5:
            raise ValueError('treehouse deck must rise above trunk base')
        dx, dy = x - bx, y - by
        paths[name] = [
            (bx, by, bz + (z-bz) * .57),
            (bx + dx*.24, by + dy*.24, bz + (z-bz) * .72),
            (bx + dx*.64, by + dy*.64, z - 5.0),
            (x, y, z - 1.4),
        ]
    return paths


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
