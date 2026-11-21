"""Deterministic palette segmentation for decimated CC0 palm silhouettes.

The narrow OBJ baker chooses VDP1 indexed8 art by object-name suffix, not
by source GLB face materials. Split existing palm geometry into a darker
wood-like lower silhouette and bright foliage above without adding faces.
"""
def split_palm_faces(vertices, faces, base_z, height_m):
    if height_m <= 0:
        raise ValueError("palm height must be positive")
    threshold=base_z+height_m*0.62
    wood=[]
    leaves=[]
    for face in faces:
        if len(face)!=3 or any(i<0 or i>=len(vertices) for i in face):
            raise ValueError("invalid decimated triangle")
        z=sum(vertices[i][2] for i in face)/3.0
        (wood if z<threshold else leaves).append(tuple(face))
    return wood,leaves
