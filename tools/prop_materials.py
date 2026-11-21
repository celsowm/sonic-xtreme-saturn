"""Source-material partition for Kenney GLB palms before LOD reduction.

Known CC0 GLBs expose woodBark and leafsGreen primitives. Decimating the
whole palm at once collapsed away its trunk; instead assign independent LOD
budgets to each original material. No palette is guessed from geometry.
"""
def split_palm_faces(faces, face_materials, material_names):
    if len(faces)!=len(face_materials):
        raise ValueError("GLB face/material count mismatch")
    wood=[]
    leaves=[]
    for face,mat_id in zip(faces,face_materials):
        if len(face)!=3 or not isinstance(mat_id,int) or not 0<=mat_id<len(material_names):
            raise ValueError("invalid palm face or material")
        name=material_names[mat_id].lower()
        if name.startswith("wood"):
            wood.append(tuple(face))
        elif name.startswith(("leaf","foliage")):
            leaves.append(tuple(face))
        else:
            raise ValueError(f"unknown palm source material: {name}")
    if not wood or not leaves:
        raise ValueError("source GLB lacks palm bark or canopy primitives")
    return wood,leaves
