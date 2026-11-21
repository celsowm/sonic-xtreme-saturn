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
