#!/usr/bin/env bash
# Review the Jade Gully V5 art-direction candidate without modifying the
# current checkout's branch. Always pull the Mac checkout before rendering.
# Run from the existing repo:
# git fetch origin work/jade-v5-art-direction && \
# git show origin/work/jade-v5-art-direction:scripts/review-jade-v5-mac.sh | bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
[[ "$(uname -s)" == "Darwin" ]] || { echo 'macOS required' >&2; exit 1; }
echo '[jade-v5] Pulling current Mac checkout...'
git pull --ff-only
echo '[jade-v5] Fetching V5 art review...'
git fetch origin work/jade-v5-art-direction
DEST="$HOME/dev/sonic-xtreme-v5-review-$(date +%Y%m%d-%H%M%S)"
[[ ! -e "$DEST" ]] || { echo "Existing worktree destination: $DEST" >&2; exit 1; }
mkdir -p "$(dirname "$DEST")"
git worktree add --detach "$DEST" origin/work/jade-v5-art-direction
echo '[jade-v5] Testing and rendering isolated Blender art source...'
bash "$DEST/scripts/build-jade-concept-v4-mac.sh"
OUT="$DEST/build/jade-gully-concept-v4"
for file in jade-gully-v4-compare.png jade-gully-v4-clean.png jade-gully-v4-top.png \
  jade-gully-v4-entry_hills.png jade-gully-v4-tree_village.png \
  jade-gully-v4-sky_bridges.png jade-gully-v4-hex_loop.png \
  jade-gully-v4-canyon_basin.png jade_gully_act1_concept_v4.blend \
  concept-v4-contract.json; do
  [[ -s "$OUT/$file" ]] || { echo "Missing generated output: $OUT/$file" >&2; exit 1; }
done
ZIP="$DEST/build/jade-v5-review.zip"
(cd "$OUT" && zip -q "$ZIP" ./*.png ./*.json ./*.blend)
echo "[jade-v5] Comparison: $OUT/jade-gully-v4-compare.png"
echo "[jade-v5] Clean artwork: $OUT/jade-gully-v4-clean.png"
echo "[jade-v5] Tree Village: $OUT/jade-gully-v4-tree_village.png"
echo "[jade-v5] Canyon: $OUT/jade-gully-v4-canyon_basin.png"
echo "[jade-v5] ZIP for visual review: $ZIP"
echo "[jade-v5] Source review: $DEST/docs/concepts/JADE_GULLY_V5_VISUAL_REVIEW.md"
open -a Preview "$OUT/jade-gully-v4-compare.png" \
  "$OUT/jade-gully-v4-clean.png" \
  "$OUT/jade-gully-v4-tree_village.png" \
  "$OUT/jade-gully-v4-canyon_basin.png"
