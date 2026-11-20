#!/usr/bin/env bash
# Copy the Sonic R source supplied in chat and locally generated LOD into Git,
# then push only this asset set to main. No force-push or unrelated files.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
die(){ printf '[sonic-repo] ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(git branch --show-current)" == "main" ]] ||
  die "Checkout main before committing model assets."
[[ -z "$(git diff --cached --name-only)" ]] ||
  die "Git index has already-staged changes; commit or unstage them first."

SRC="$ROOT/assets/private/sonic-r"
DST="$ROOT/assets/sonic-r"
DOWNLOAD="$HOME/Downloads/sonic-r-full-animations-low-poly-pc-version"
mkdir -p "$DST/source" "$DST/textures" "$DST/lod-160"

copy_input(){
  local item="$1"
  local dest="$DST/$item"
  if [[ -s "$SRC/$item" ]]; then
    cp "$SRC/$item" "$dest"
  elif [[ -s "$DOWNLOAD.zip" ]]; then
    unzip -p "$DOWNLOAD.zip" "$item" > "$dest"
  elif [[ -s "$DOWNLOAD/$item" ]]; then
    cp "$DOWNLOAD/$item" "$dest"
  else
    die "Original asset $item not found in local conversion or Downloads."
  fi
}
copy_input source/sonic.glb
copy_input textures/sonic_add_signed_2.png

for item in sonic.c sonic.h sonic.ska report.json; do
  if [[ -s "$SRC/lod-160/$item" ]]; then
    cp "$SRC/lod-160/$item" "$DST/lod-160/$item"
  elif [[ ! -s "$DST/lod-160/$item" ]]; then
    die "LOD-160 missing $item; first run bash scripts/qualify-sonic-lod-mac.sh."
  fi
done
if [[ -s "$SRC/lod-160/selected-texture-scale.txt" ]]; then
  cp "$SRC/lod-160/selected-texture-scale.txt" "$DST/lod-160/selected-texture-scale.txt"
fi

# Refuse similarly named or accidentally altered source models.
python3 - "$DST" <<'PY'
from pathlib import Path
import hashlib,sys,re
root=Path(sys.argv[1])
expected={
    "source/sonic.glb":"eea3a7c4eded1a430fa941b9f0e510a8858cbf04df4b0650f7754ddaf7e32ea0",
    "textures/sonic_add_signed_2.png":"cac24ed8201039f27b0572f850680473feaa313c596fa081bf44908b244feaa0",
}
for name,sha in expected.items():
    p=root/name
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    if digest!=sha:raise SystemExit(f"[sonic-repo] Unexpected source SHA256: {name}: {digest}")
    print(f"[sonic-repo] Verified {name}: {digest[:16]}")
header=(root/"lod-160/sonic.h").read_text()
counts={}
for key in ("FACE","VERTEX","TEXTURE"):
    m=re.search(r"^#define\s+SONIC_"+key+r"_COUNT\s+(\d+)\b",header,re.M)
    if m is None:raise SystemExit(f"[sonic-repo] Missing SONIC_{key}_COUNT")
    counts[key]=int(m.group(1))
if not 0<counts["FACE"]<=160:raise SystemExit("[sonic-repo] Invalid generated triangle count")
print(f"[sonic-repo] LOD: {counts['FACE']} faces, {counts['VERTEX']} vertices, {counts['TEXTURE']} textures")
PY

git add -- \
  assets/sonic-r/source/sonic.glb \
  assets/sonic-r/textures/sonic_add_signed_2.png \
  assets/sonic-r/lod-160/sonic.c \
  assets/sonic-r/lod-160/sonic.h \
  assets/sonic-r/lod-160/sonic.ska \
  assets/sonic-r/lod-160/report.json
if [[ -s "$DST/lod-160/selected-texture-scale.txt" ]]; then
  git add -- assets/sonic-r/lod-160/selected-texture-scale.txt
fi
git diff --cached --check || die "The selected assets failed git diff --check."
if ! git diff --cached --quiet; then
  git commit -m "Track Sonic R source model, texture and skeletal LOD-160"
else
  echo "[sonic-repo] Assets already tracked at the same versions."
fi
git push origin main
echo "[sonic-repo] GitHub main now contains the actual model, texture and generated character."
unset XTREME_SONIC_DIR
python3 scripts/qualify-ymir.py --require-sonic --case idle
