#!/usr/bin/env bash
# Isolated first qualification of the branching Adventure Act 1 map.
# Does NOT overwrite or alter the previously Ymir-qualified classic scene.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[[ -s "assets/kenney/nature-kit/tree-palm.glb" ]] || {
  echo "[adventure] Kenney CC0 assets missing; git pull --ff-only" >&2
  exit 1
}
python3 -m unittest discover -s tests -p 'test_adventure_layout.py' -v
python3 tools/validate_adventure_layout.py
export XTREME_STAGE_LAYOUT=adventure
echo "[adventure] Building authored multi-route scene and running Ymir."
echo "[adventure] 30 submissions/s is an emulator diagnostic, NOT verified video FPS."
python3 scripts/qualify-ymir.py --require-sonic \
  --case idle --case jump_in_place --case curve_route --case hud_pages \
  --case offroad_right
