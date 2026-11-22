#!/usr/bin/env bash
# Review the latest main-branch Blender source without changing local branches.
# Usage: bash scripts/open-tree-village-mac.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/build/tree-village-review"
die() { printf '[tree-village] ERROR: %s\n' "$*" >&2; exit 1; }
command -v git >/dev/null || die "git is missing"
command -v open >/dev/null || die "macOS open command is missing"
git -C "$ROOT" remote get-url origin | grep -Eq '(^|[:/])celsowm/sonic-xtreme-saturn(\.git)?$' \
  || die "unexpected origin"
# Keep the longstanding Mac workflow contract: pull the checked-out branch.
git -C "$ROOT" pull --ff-only
# The experimental work branch intentionally does NOT contain published binary
# .blend assets: read them from origin/main without checkout or merging PR #2.
git -C "$ROOT" fetch origin main
mkdir -p "$OUT"
for name in tree_village_source.blend tree_village_preview.png \
            tree_village_ground_preview.png kit-report.json; do
    ref="origin/main:assets/jade-gully/tree-village/$name"
    git -C "$ROOT" cat-file -e "$ref" || die "Missing on origin/main: $name"
    git -C "$ROOT" show "$ref" > "$OUT/$name"
done
BLEND="$OUT/tree_village_source.blend"
[[ -s "$BLEND" ]] || die "Blender source is empty"
echo "[tree-village] Model: $BLEND"
echo "[tree-village] Report: $OUT/kit-report.json"
echo "[tree-village] Source reference: origin/main (no branch switch)"
open -a Blender "$BLEND"
open "$OUT/tree_village_ground_preview.png"
open "$OUT/tree_village_preview.png"
