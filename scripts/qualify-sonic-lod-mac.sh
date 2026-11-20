#!/usr/bin/env bash
# Generate and qualify a private, skeletal Sonic R LOD with the existing SDK.
# No GLB/PNG/derived C/H/SKA is copied into the Git repository or evidence ZIP.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEV="$(cd "$ROOT/.." && pwd)"
SRC="$ROOT/assets/private/sonic-r"
ORIGINAL="$SRC/source/sonic.glb"
SDK="${LIBSATURN_SOURCE:-$DEV/lib-saturn}"
[[ -f "$SDK/tools/import_model.py" ]] || SDK="$DEV/libsaturn"
PY="$SRC/.venv/bin/python"
TRIS="${1:-160}"
die(){ printf '[sonic-lod] %s\n' "$*" >&2; exit 1; }
[[ "$TRIS" =~ ^[0-9]+$ ]] || die "triangle target must be an integer, got '$TRIS'"
(( TRIS >= 80 && TRIS < 286 )) || die "triangle target must be 80..285"
[[ -f "$ORIGINAL" ]] || die "source GLB missing: $ORIGINAL"
[[ -f "$SDK/tools/import_model.py" ]] || die "libsaturn importer not found under ~/dev"
[[ -x "$PY" ]] || die "private Python venv missing: $PY (run original import setup)"
OUT="$SRC/lod-$TRIS"
mkdir -p "$OUT"
cd "$ROOT"
printf '[sonic-lod] Source (private): %s\n' "$ORIGINAL"
printf '[sonic-lod] Target: %s triangles; SDK: %s\n' "$TRIS" "$SDK"
"$PY" "$SDK/tools/import_model.py" \
  --input "$ORIGINAL" \
  --out-prefix "$OUT/sonic" \
  --symbol sonic \
  --target skeletal \
  --skeletal-binary "$OUT/sonic.ska" \
  --animation idle,highspeed,jump,falling,landing,brake,turn_left,turn_right \
  --loop-clips idle,highspeed,falling \
  --animation-fps 30 \
  --scale 0.03265 \
  --max-triangles "$TRIS" \
  --quality conservative \
  --skeletal-surface-bake \
  --texture-scale 0.25 \
  --max-texture-width 64 \
  --max-texture-height 64 \
  --sampling area \
  --texture-format indexed8 \
  --report "$OUT/report.json" 2>&1 | tee "$OUT/import.log"
for item in sonic.c sonic.h sonic.ska report.json; do
  [[ -s "$OUT/$item" ]] || die "missing or empty generated $item"
done
"$PY" - "$OUT" "$TRIS" <<'PY'
import json,re,sys
from pathlib import Path
directory=Path(sys.argv[1])
target=int(sys.argv[2])
header=(directory/"sonic.h").read_text()
def constant(name):
    m=re.search(r"^#define\s+"+name+r"\s+(\d+)\b",header,re.M)
    if m is None:raise SystemExit("Missing generated "+name)
    return int(m.group(1))
faces=constant("SONIC_FACE_COUNT")
verts=constant("SONIC_VERTEX_COUNT")
textures=constant("SONIC_TEXTURE_COUNT")
if not (0<faces<286 and faces<=target):
    raise SystemExit(f"Cannot qualify target {target}: generated faces={faces}")
if textures==0:raise SystemExit("No baked materials in output")
report=json.loads((directory/"report.json").read_text())
print(f"[sonic-lod] Generated: faces={faces}, vertices={verts}, textures={textures}")
print(f"[sonic-lod] Source transfer: {report.get('textures',{}).get('surface_transfer')}")
PY
export XTREME_SONIC_DIR="$OUT"
echo "[sonic-lod] Building isolated private variant (source untouched)."
echo "[sonic-lod] Ymir evidence will contain only screenshots, logs, JSON and SHA256 hashes."
python3 scripts/qualify-ymir.py --require-sonic --case idle
