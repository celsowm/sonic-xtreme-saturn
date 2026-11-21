#!/usr/bin/env python3
"""Verify Adventure's contiguous navigable landmass survives OBJ -> Saturn bake."""
import re
import sys
from pathlib import Path

def count(text,macro):
    m=re.search(r"^#define\s+"+re.escape(macro)+r"\s+(\d+)u\s*$",text,re.M)
    if not m:raise ValueError(f"missing {macro}")
    return int(m.group(1))

def verify(render,collision):
    stage=Path(render).read_text()
    ground=Path(collision).read_text()
    faces=count(stage,"STAGE_FACE_COUNT")
    vertices=count(ground,"COLLISION_VERTEX_COUNT")
    surface_faces=count(ground,"COLLISION_FACE_COUNT")
    entities=count(stage,"STAGE_ENTITY_COUNT")
    lod_groups=count(stage,"STAGE_LOD_GROUP_COUNT")
    if not 420<=faces<=512:
        raise ValueError(f"Adventure stage render faces out of budget: {faces}")
    if not 160<=surface_faces<=512:
        raise ValueError(f"Continuous collision landmass absent or over budget: {surface_faces}")
    if not 0<vertices<=2048:
        raise ValueError(f"Collision vertices out of budget: {vertices}")
    if lod_groups!=7:
        raise ValueError(f"Expected seven source-backed two-tone palm LOD groups, got {lod_groups}")
    if surface_faces!=168:
        raise ValueError(f"Original collision topology changed unexpectedly: {surface_faces} vs 168")
    if entities!=13:
        raise ValueError(f"Expected 13 action-stage markers, got {entities}")
    result={"render_triangles":faces,"collision_triangles":surface_faces,"collision_vertices":vertices,"markers":entities,"palm_lod_groups":lod_groups}
    print(f"[adventure] Baked continuous landscape verified: {result}")
    return result

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: check_adventure_bake.py GREYBOX_H COLLISION_H")
    verify(sys.argv[1],sys.argv[2])
