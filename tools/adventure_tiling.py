"""Deterministic render-only tiling helpers for Jade Gully.

The Saturn scene API maps each whole CC0 64x64 texture across a polygon.
To reduce extreme stretching without new texture bytes, subdivide ONLY
near-camera render patches. Caller must retain unsplit collision geometry.
"""

def midpoint(a,b):
    if len(a)!=len(b):
        raise ValueError("different coordinate dimensions")
    return tuple((x+y)*0.5 for x,y in zip(a,b))

def refine_first_segments(points, count):
    if not isinstance(count,int) or not 0<=count<len(points):
        raise ValueError("invalid prefix count")
    if len(points)<2:
        raise ValueError("need >=2 stations")
    result=[]
    for i,point in enumerate(points):
        result.append(tuple(point))
        if i<count:
            result.append(midpoint(point,points[i+1]))
    return result

def split_quad_across(a,b,c,d):
    """Two 4-corner patches sharing exact midpoint vertices.

    Original winding: (a,b,c,d) with a,b on the first row, d,c on
    the next row. Subdivision is render-only; collision retains a,b,c,d.
    """
    mid_ab=midpoint(a,b)
    mid_dc=midpoint(d,c)
    return (tuple(a),mid_ab,mid_dc,tuple(d)),(mid_ab,tuple(b),tuple(c),mid_dc)

def make_valley_grid(main):
    """Exact source strip geometry shared by render, collision and prop snap.

    Each cross-section is 5 points, left to right. Coordinate system Blender
    RH Z-up metres. This intentionally preserves the v3 valley profile.
    """
    if len(main)<2:
        raise ValueError("need >=2 valley stations")
    rows=[(main[0][0],-12,main[0][2],main[0][3]),*main]
    refined=refine_first_segments(rows,min(4,len(rows)-1))
    offsets=(-48.0,-20.0,0.0,20.0,48.0)
    grid=[]
    for x,y,z,width in refined:
        left=4.0 if 24<=y<=95 else 2.0
        river=-4.5 if 35<=y<=79 else 1.3
        levels=(left+6.0,left,-0.5,river,river+6.0)
        grid.append([(x+dx,y,z+dz) for dx,dz in zip(offsets,levels)])
    return grid

def sample_valley_height(grid,x,y):
    """Sample the authored surface for visual-only props.

    Interpolate between the same two cross-sections and neighbouring strip
    columns used by the terrain mesh; do not change collision/raycast math.
    Out-of-bounds placement must be corrected by the author, not clamped.
    """
    if not grid or len(grid[0])!=5:
        raise ValueError("invalid valley grid")
    if y<grid[0][0][1] or y>grid[-1][0][1]:
        raise ValueError("prop outside valley longitudinal bounds")
    row_idx=len(grid)-2
    for i in range(len(grid)-1):
        if grid[i][0][1]<=y<=grid[i+1][0][1]:
            row_idx=i
            break
    row_a,row_b=grid[row_idx],grid[row_idx+1]
    dy=row_b[0][1]-row_a[0][1]
    if dy<=0:
        raise ValueError("non-increasing terrain rows")
    t=(y-row_a[0][1])/dy
    interpolated=[
        (a[0]+(b[0]-a[0])*t,a[2]+(b[2]-a[2])*t)
        for a,b in zip(row_a,row_b)
    ]
    if x<interpolated[0][0] or x>interpolated[-1][0]:
        raise ValueError("prop outside valley lateral bounds")
    col=len(interpolated)-2
    for i in range(len(interpolated)-1):
        if interpolated[i][0]<=x<=interpolated[i+1][0]:
            col=i
            break
    left,right=interpolated[col],interpolated[col+1]
    dx=right[0]-left[0]
    if dx<=0:
        raise ValueError("non-increasing terrain columns")
    u=(x-left[0])/dx
    return left[1]+(right[1]-left[1])*u
