#!/usr/bin/env bash
# Capture logs, exact revisions and new Mednafen F9 screenshots. No BIOS/disc.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
RUN="$(mktemp -d "$ROOT/build-evidence.XXXXXXXX")" || exit 1
SDK_SOURCE="${LIBSATURN_SOURCE:-$ROOT/../lib-saturn}"
[[ -f "$SDK_SOURCE/CMakeLists.txt" ]] || SDK_SOURCE="$ROOT/../libsaturn"
SNAP="${LIBSATURN_MEDNAFEN_HOME:-$SDK_SOURCE/bios}/snap"
export XTREME_EVIDENCE_DIR="$RUN"
{
    echo "game revision:"; git rev-parse HEAD; git status --porcelain --untracked-files=no
    echo "sdk revision:"; git -C "$SDK_SOURCE" rev-parse HEAD;git -C "$SDK_SOURCE" status --porcelain --untracked-files=no
    echo "system:"; sw_vers; uname -m
    echo "capture UTC:";date -u
} > "$RUN/manifest.txt" 2>&1
touch "$RUN/start.marker"
echo "[xtreme] Press F9 in Mednafen for screenshots, then close emulator to package evidence."
bash scripts/run-mac.sh "$@" 2>&1 | tee "$RUN/run.log"
rc=${PIPESTATUS[0]}
printf '\nexit_code=%s\n' "$rc" >> "$RUN/manifest.txt"
mkdir -p "$RUN/screenshots" "$RUN/build"
if [[ -d "$SNAP" ]]; then
    while IFS= read -r -d '' p; do cp "$p" "$RUN/screenshots/$(basename "$p")"; done < <(find "$SNAP" -maxdepth 1 -type f -iname 'xtreme*.png' -newer "$RUN/start.marker" -print0)
fi
if [[ "$rc" == 0 ]]; then
    while IFS= read -r -d '' p; do cp "$p" "$RUN/build/$(basename "$p")"; done < <(find build/game -type f -name '*.map' -print0)
    for p in build/game/generated/greybox.h build/game/generated/collision.h;do [[ ! -f "$p" ]] || cp "$p" "$RUN/build/";done
    if [[ -f build/game/disc/xtreme.cue ]];then
        for p in build/game/disc/xtreme.cue build/game/disc/xtreme.bin build/game/disc/xtreme.iso;do [[ ! -f "$p" ]] || shasum -a 256 "$p" >> "$RUN/manifest.txt";done
    fi
fi
rm -f "$RUN/start.marker"
ZIP="$ROOT/xtreme-return-$(date +%Y%m%d-%H%M%S).zip"
(cd "$RUN" && /usr/bin/zip -q -r "$ZIP" manifest.txt run.log screenshots build)
echo "[xtreme] Evidence: $ZIP (review logs for local paths before sharing)"
exit "$rc"
