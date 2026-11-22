#!/usr/bin/env bash
# Painting-faithful Jade Gully concept v4 (offline Blender art, Blender 5.2).
# Leaves the Saturn game build, the v1-v3 concept and the Adventure layout alone.
#   bash scripts/build-jade-concept-v4-mac.sh            # all 10 images
#   JADE_V4_QUICK=1 bash scripts/build-jade-concept-v4-mac.sh   # map + compare
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 -m unittest tests.test_jade_concept_v4 tests.test_jade_concept_v5 -v
python3 -m py_compile tools/create_jade_gully_concept_v4.py tools/jade_concept_v4_geometry.py tools/validate_jade_concept_v4.py
python3 tools/validate_jade_concept_v4.py
BLENDER="${BLENDER:-blender}"
command -v "$BLENDER" >/dev/null 2>&1 || { echo '[jade v4] Blender 5.2 not found (set BLENDER=...)' >&2; exit 1; }
"$BLENDER" --version | head -1
OUT="$ROOT/build/jade-gully-concept-v4"
"$BLENDER" -b --factory-startup --python-exit-code 1 \
  --python tools/create_jade_gully_concept_v4.py -- "$OUT"
printf '%s\n' \
  "[jade v4] Side-by-side with the painting: $OUT/jade-gully-v4-compare.png" \
  "[jade v4] Painting framing: $OUT/jade-gully-v4-map.png (clean: jade-gully-v4-clean.png)" \
  "[jade v4] Editable scene: $OUT/jade_gully_act1_concept_v4.blend" \
  "[jade v4] Metrics: $OUT/concept-v4-contract.json"
if [[ "$(uname -s)" == "Darwin" && -z "${CI:-}" ]]; then
  open -a Preview "$OUT/jade-gully-v4-compare.png" || true
fi
