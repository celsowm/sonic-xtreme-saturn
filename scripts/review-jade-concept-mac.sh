#!/usr/bin/env bash
# Pull the current Mac branch and review the latest main without switching it.
# From the existing clone:
#   git fetch origin main && git show origin/main:scripts/review-jade-concept-mac.sh | bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
[[ "$(uname -s)" == "Darwin" ]] || { echo "Run this on macOS" >&2; exit 1; }
echo "[jade-v3] Pulling your currently checked out Mac branch..."
git pull --ff-only
echo "[jade-v3] Fetching the updated main..."
git fetch origin main
DEST="$HOME/dev/sonic-xtreme-concept-$(date +%Y%m%d-%H%M%S)"
[[ ! -e "$DEST" ]] || { echo "Refusing to overwrite $DEST" >&2; exit 1; }
mkdir -p "$(dirname "$DEST")"
git worktree add --detach "$DEST" origin/main
bash "$DEST/scripts/build-jade-concept-mac.sh"
OUT="$DEST/build/jade-gully-concept"
PNG="$OUT/jade-gully-concept-isometric.png"
BLEND="$OUT/jade_gully_act1_concept.blend"
[[ -s "$PNG" && -s "$BLEND" ]] || { echo "Render or Blender file missing" >&2; exit 1; }
for sector in base ridges bamboo current summit; do
  [[ -s "$OUT/jade-gully-concept-$sector.png" ]] || {
    echo "Missing $sector camera render" >&2; exit 1;
  }
done
ZIP="$DEST/build/jade-gully-v3-visual-review.zip"
(cd "$OUT" && zip -q "$ZIP" ./*.png ./concept-contract.json ./jade_gully_act1_concept.blend)
echo "[jade-v3] Overview: $PNG"
echo "[jade-v3] Bamboo details: $OUT/jade-gully-concept-bamboo.png"
echo "[jade-v3] Waterfalls: $OUT/jade-gully-concept-current.png"
echo "[jade-v3] Editable Blender: $BLEND"
echo "[jade-v3] Attach this ZIP here for review: $ZIP"
open -a Preview "$PNG" "$OUT/jade-gully-concept-bamboo.png" "$OUT/jade-gully-concept-current.png"
