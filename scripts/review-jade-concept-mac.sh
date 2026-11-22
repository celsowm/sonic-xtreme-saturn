#!/usr/bin/env bash
# Use directly on Mac even when the developer is on an experimental branch:
#   git fetch origin main && git show origin/main:scripts/review-jade-concept-mac.sh | bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
[[ "$(uname -s)" == "Darwin" ]] || { echo "Run this preview on macOS" >&2; exit 1; }
echo "[jade-v2] Pulling the Mac's CURRENT branch, without switching branches..."
git pull --ff-only
echo "[jade-v2] Fetching the latest verified main source..."
git fetch origin main
DEST="$HOME/dev/sonic-xtreme-concept-$(date +%Y%m%d-%H%M%S)"
[[ ! -e "$DEST" ]] || { echo "Refusing to overwrite $DEST" >&2; exit 1; }
mkdir -p "$(dirname "$DEST")"
git worktree add --detach "$DEST" origin/main
bash "$DEST/scripts/build-jade-concept-mac.sh"
PNG="$DEST/build/jade-gully-concept/jade-gully-concept-isometric.png"
BLEND="$DEST/build/jade-gully-concept/jade_gully_act1_concept.blend"
[[ -s "$PNG" && -s "$BLEND" ]] || { echo "Render or Blender file missing" >&2; exit 1; }
echo "[jade-v2] Preview: $PNG"
echo "[jade-v2] Editable Blender scene: $BLEND"
open "$PNG"
