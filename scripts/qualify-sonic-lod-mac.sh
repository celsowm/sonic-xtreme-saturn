#!/usr/bin/env bash
# Regenerate and qualify a version-controlled Sonic R LOD using LibSaturn.
# Source and generated C/H/SKA belong under tracked assets/sonic-r/.
# The Ymir evidence ZIP contains only logs/screenshots/telemetry, not asset data.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEV="$(cd "$ROOT/.." && pwd)"
SRC="$ROOT/assets/sonic-r"
ORIGINAL="$SRC/source/sonic.glb"
SDK="${LIBSATURN_SOURCE:-$DEV/lib-saturn}"
[[ -f "$SDK/tools/import_model.py" ]] || SDK="$DEV/libsaturn"
PY="$ROOT/assets/private/sonic-r/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="$ROOT/build/sonic-venv/bin/python"
  if [[ ! -x "$PY" ]]; then
    python3 -m venv "$ROOT/build/sonic-venv"
    "$PY" -m pip install pillow numpy
  fi
fi
TRIS="${1:-160}"
die(){ printf '[sonic-lod] %s\n' "$*" >&2; exit 1; }
[[ "$TRIS" =~ ^[0-9]+$ ]] || die "triangle target must be an integer, got '$TRIS'"
(( TRIS >= 80 && TRIS < 286 )) || die "triangle target must be 80..285"
[[ -f "$ORIGINAL" ]] || die "source GLB missing: $ORIGINAL"
[[ -f "$SDK/tools/import_model.py" ]] || die "libsaturn importer not found under ~/dev"
[[ -x "$PY" ]] || die "Python venv missing: $PY"
OUT="$SRC/lod-$TRIS"
mkdir -p "$OUT"
cd "$ROOT"
printf '[sonic-lod] Versioned source: %s\n' "$ORIGINAL"
printf '[sonic-lod] Target: %s triangles; SDK: %s\n' "$TRIS" "$SDK"
# Simplification can enlarge UV footprints while reducing triangle count.
# Retry only known face-size/total VDP1-budget failures, preserving animations.
IMPORTED=0
: > "$OUT/import.log"
for TEX_SCALE in 0.25 0.1875 0.125 0.09375 0.0625 0.03125; do
  rm -f "$OUT/sonic.c" "$OUT/sonic.h" "$OUT/sonic.ska" "$OUT/report.json"
  echo "[sonic-lod] Trying texture-scale=$TEX_SCALE, max-face=96x96" | tee -a "$OUT/import.log"
  if "$PY" "$SDK/tools/import_model.py" \
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
    --texture-scale "$TEX_SCALE" \
    --max-texture-width 96 \
    --max-texture-height 96 \
    --sampling area \
    --texture-format indexed8 \
    --report "$OUT/report.json" >"$OUT/import-attempt.log" 2>&1; then
    cat "$OUT/import-attempt.log" | tee -a "$OUT/import.log"
    echo "[sonic-lod] Texture bake succeeded at scale=$TEX_SCALE" | tee -a "$OUT/import.log"
    printf '%s\n' "$TEX_SCALE" > "$OUT/selected-texture-scale.txt"
    IMPORTED=1
    break
  fi
  tail -n 12 "$OUT/import-attempt.log" | tee -a "$OUT/import.log"
  if grep -Eq 'needs [0-9]+x[0-9]+ but the limit is|skeletal texture budget:' "$OUT/import-attempt.log"; then
    echo "[sonic-lod] Texture resolution/budget gate; trying a lower scale" | tee -a "$OUT/import.log"
  else
    die "Importer failed for a non-texture-budget reason; see $OUT/import-attempt.log"
  fi
done
(( IMPORTED == 1 )) || die "No texture scale fits the VDP1 budget; inspect $OUT/import.log"

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
echo "[sonic-lod] Building tracked LOD candidate (source GLB untouched)."
echo "[sonic-lod] LOD output is in tracked assets/sonic-r/lod-$TRIS; commit generated C/H/SKA after validation."
python3 scripts/qualify-ymir.py --require-sonic --case idle
