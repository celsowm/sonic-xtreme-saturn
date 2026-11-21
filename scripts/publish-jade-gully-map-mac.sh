#!/usr/bin/env bash
# Publish the user-approved full-resolution Jade Gully concept PNG to main,
# without checking out main or touching the developer's current branch.
# Usage: bash scripts/publish-jade-gully-map-mac.sh [path-to-png]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="docs/concepts/jade-gully-act1-concept.png"
fail(){ printf '[jade-map] ERROR: %s\n' "$*" >&2; exit 1; }

if [[ $# -gt 1 ]]; then fail "Pass at most one PNG path"; fi
if [[ $# -eq 1 ]]; then
    SRC="$1"
else
    SRC=""
    for candidate in \
        "$HOME/Downloads/mapa_conceitual_jade_gully_retro.png" \
        "$HOME/Downloads/mapa_conceitual_jade_gully_retro (1).png" \
        "$HOME/Downloads/mapa_de_jade_gully_ato_1.png"; do
        if [[ -f "$candidate" ]]; then SRC="$candidate"; break; fi
    done
fi
[[ -n "$SRC" && -f "$SRC" ]] || fail "Download the approved map image from ChatGPT into Downloads, or pass its full path"
SRC="$(cd "$(dirname "$SRC")" && pwd)/$(basename "$SRC")"
file "$SRC" | grep -q 'PNG image data' || fail "Not a PNG: $SRC"
command -v git >/dev/null || fail "Git is missing"
git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null || fail "Not a Git working tree"
git -C "$ROOT" remote get-url origin | grep -Eq '(^|[:/])celsowm/sonic-xtreme-saturn(\\.git)?$' || fail "Unexpected origin; refusing to push another repository"

echo '[jade-map] Fetching origin/main without switching local branches...'
git -C "$ROOT" fetch origin main
TMP="$(mktemp -d "${TMPDIR:-/tmp}/jade-map-main.XXXXXX")"
cleanup(){
    git -C "$ROOT" worktree remove --force "$TMP" >/dev/null 2>&1 || true
    rmdir "$TMP" >/dev/null 2>&1 || true
}
trap cleanup EXIT
git -C "$ROOT" worktree add --detach "$TMP" origin/main
mkdir -p "$TMP/docs/concepts"
cp "$SRC" "$TMP/$OUT"
python3 - "$TMP/docs/concepts/JADE_GULLY_ACT1_MAP.md" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
s=p.read_text()
picture="![Jade Gully Act 1 — map concept](jade-gully-act1-concept.png)\n\n"
if picture not in s:
    s=s.replace("## Proposed layout\n",picture+"## Proposed layout\n",1)
    p.write_text(s)
PY
git -C "$TMP" add "$OUT" docs/concepts/JADE_GULLY_ACT1_MAP.md
if git -C "$TMP" diff --cached --quiet; then
    echo '[jade-map] The same PNG and documentation are already on origin/main.'
    exit 0
fi
git -C "$TMP" -c user.name="$(git -C "$ROOT" config user.name)" \
  -c user.email="$(git -C "$ROOT" config user.email)" \
  commit -m "art(jade): publish approved full-resolution Act 1 map concept"
git -C "$TMP" push origin HEAD:refs/heads/main
echo "[jade-map] Published: https://github.com/celsowm/sonic-xtreme-saturn/blob/main/$OUT"
