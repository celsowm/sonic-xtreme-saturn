"""Small deterministic source-geometry generators for Jade Gully concept v2.

No Blender import: the functions are unit-testable on the host, and their
meshes are ART ONLY. The stock Saturn collision and 448-face budget are
intentionally unaffected.
"""
import math


def mesa_mesh(x, y, base_z, radius, rise, sides=8):
    """Organic-ish capped plateau and checkerboard cliff faces."""
    if sides < 6 or radius <= 0 or rise <= 0:
        raise ValueError("mesa needs >=6 sides and positive dimensions")
    low = []
    high = []
    for i in range(sides):
        phi = math.tau * i / sides
        shape = 0.89 + (i % 3) * .075
        low.append((x + radius * shape * math.cos(phi),
                    y + radius * shape * math.sin(phi), base_z))
        high.append((x + radius * .87 * shape * math.cos(phi),
                     y + radius * .87 * shape * math.sin(phi), base_z + rise))
    verts = low + high
    faces = [tuple(range(sides, 2*sides))]
    material_indices = [0]  # grass cap
    for i in range(sides):
        j = (i+1) % sides
        # Extra horizontal midpoint band makes the giant checker squares
        # legible without relying on per-face UVs.
        a, b = low[i], low[j]
        c, d = high[i], high[j]
        n = len(verts)
        verts.extend((
            ((a[0]+c[0])/2, (a[1]+c[1])/2, (a[2]+c[2])/2),
            ((b[0]+d[0])/2, (b[1]+d[1])/2, (b[2]+d[2])/2),
        ))
        faces.extend((
            (i, j, n+1, n),
            (n, n+1, sides+j, sides+i),
        ))
        material_indices.extend((1+(i%2), 1+((i+1)%2)))
    return verts, faces, material_indices


def ribbon_mesh(points, half_width):
    """One quad per progressive station, wide enough to read as a river."""
    if half_width <= 0 or len(points) < 2:
        raise ValueError("ribbon needs positive width and 2+ points")
    vertices, faces = [], []
    for i, (x, y, z) in enumerate(points):
        prev = points[max(0, i-1)]
        nxt = points[min(len(points)-1, i+1)]
        dx, dy = nxt[0]-prev[0], nxt[1]-prev[1]
        length = math.hypot(dx,dy)
        if length < .001:
            raise ValueError("coincident river stations")
        nx, ny = dy/length * half_width, -dx/length * half_width
        vertices.extend(((x-nx, y-ny, z), (x+nx, y+ny, z)))
        if i:
            n = 2*i
            faces.append((n-2, n-1, n+1, n))
    return vertices, faces


def halfpipe_mesh(start, end, radius, segments=14, cross_steps=7):
    """Low-poly U-shaped bamboo gutter, visibly 3D in an oblique render."""
    if radius <= 0 or segments < 2 or cross_steps < 3:
        raise ValueError("bad halfpipe dimensions")
    vertices, faces, material_indices = [], [], []
    for i in range(segments+1):
        t = i / segments
        x = start[0] + (end[0]-start[0])*t
        y = start[1] + (end[1]-start[1])*t
        z = start[2] + (end[2]-start[2])*t
        for j in range(cross_steps+1):
            angle = -math.pi*.5 + math.pi*j/cross_steps
            vertices.append((x+radius*math.sin(angle),
                             y, z+radius*(1-math.cos(angle))))
    for i in range(segments):
        for j in range(cross_steps):
            a = i*(cross_steps+1)+j
            b = a+cross_steps+1
            faces.append((a,b,b+1,a+1))
            material_indices.append((i//2+j//2)%2)
    return vertices, faces, material_indices
