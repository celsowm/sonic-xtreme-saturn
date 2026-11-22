#!/usr/bin/env bash
# Build a Tree Village source .blend in a clean worktree and publish to main.
# No checkout of main and no changes to the user's existing branch or edits.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { printf '[tree-village] ERROR: %s\n' "$*" >&2; exit 1; }
command -v git >/dev/null || die "git missing"
command -v python3 >/dev/null || die "python3 missing"
git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null || die "not a Git checkout"
git -C "$ROOT" remote get-url origin | grep -Eq '(^|[:/])celsowm/sonic-xtreme-saturn(\.git)?$' \
    || die "unexpected origin; refusing to publish to an unrelated repo"

# Always pull the user's checked-out branch before running the workflow.
git -C "$ROOT" pull --ff-only
git -C "$ROOT" fetch origin main
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
if [[ ! -x "$BLENDER" ]]; then BLENDER="$(command -v blender || true)"; fi
[[ -n "$BLENDER" && -x "$BLENDER" ]] || die "Blender not found; install Blender or export BLENDER=/path/to/blender"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/tree-village-main.XXXXXX")"
cleanup() {
    git -C "$ROOT" worktree remove --force "$TMP" >/dev/null 2>&1 || true
    rmdir "$TMP" >/dev/null 2>&1 || true
}
trap cleanup EXIT
git -C "$ROOT" worktree add --detach "$TMP" origin/main
cd "$TMP"
python3 tools/validate_tree_village_kit.py
python3 -m unittest discover -s tests -p 'test_tree_village_kit.py' -v
mkdir -p build/tree-village
"$BLENDER" --background --factory-startup --python-exit-code 1 \
    --python tools/create_tree_village_kit.py -- \
    assets/jade-gully/tree-village/kit-manifest.json \
    build/tree-village --preview

python3 - <<'PY'
import json
from pathlib import Path
out = Path("build/tree-village")
report = json.loads((out/"kit-report.json").read_text())
assert report["render_faces"] <= 448, report
assert report["render_vertices"] <= 2048, report
assert report["model_definitions"] == 28, report
assert report["entity_markers"] == 7, report
blend = out/"tree_village_source.blend"
assert blend.is_file() and blend.stat().st_size > 4000, "Blender file missing/empty"
pngs = list((out/"textures").glob("*.png"))
assert len(pngs) == 10, f"expected ten art source PNGs, got {len(pngs)}"
for p in pngs:
    assert p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", f"bad PNG: {p}"
print("[tree-village] Source .blend validated; stage faces:",
      report["render_faces"], "collision faces:", report["collision_faces"])
PY

TARGET="assets/jade-gully/tree-village"
mkdir -p "$TARGET/source"
cp build/tree-village/tree_village_source.blend "$TARGET/tree_village_source.blend"
cp build/tree-village/kit-report.json "$TARGET/kit-report.json"
cp build/tree-village/textures/*.png "$TARGET/source/"
if [[ -f build/tree-village/tree_village_preview.png ]]; then
    cp build/tree-village/tree_village_preview.png "$TARGET/tree_village_preview.png"
else
    echo '[tree-village] WARNING: Blender preview unavailable; edit the .blend in GUI.'
fi
git add "$TARGET/tree_village_source.blend" "$TARGET/kit-report.json" "$TARGET/source"
if [[ -f "$TARGET/tree_village_preview.png" ]]; then git add "$TARGET/tree_village_preview.png"; fi
if git diff --cached --quiet; then
    echo '[tree-village] Same authored files already published to origin/main.'
    exit 0
fi
GIT_NAME="$(git -C "$ROOT" config user.name || true)"
GIT_EMAIL="$(git -C "$ROOT" config user.email || true)"
[[ -n "$GIT_NAME" && -n "$GIT_EMAIL" ]] || die "configure git user.name and user.email to publish"
git -c user.name="$GIT_NAME" -c user.email="$GIT_EMAIL" \
    commit -m "art(jade): publish Blender Tree Village source, texture kit and preview"
git push origin HEAD:refs/heads/main
printf '\n[tree-village] PUBLISHED to main: https://github.com/celsowm/sonic-xtreme-saturn/tree/main/assets/jade-gully/tree-village\n'
printf '[tree-village] Current working branch preserved: %s\n' "$(git -C "$ROOT" branch --show-current)"
