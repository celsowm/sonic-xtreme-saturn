#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEV="$(cd "$ROOT/.." && pwd)"
cd "$ROOT"
die(){ printf '[xtreme] %s\n' "$*" >&2; exit 1; }
SDK_SOURCE="${LIBSATURN_SOURCE:-$DEV/lib-saturn}"
[[ -f "$SDK_SOURCE/CMakeLists.txt" ]] || SDK_SOURCE="$DEV/libsaturn"
[[ -f "$SDK_SOURCE/CMakeLists.txt" ]] || die "LibSaturn checkout not found; set LIBSATURN_SOURCE"
TOOLKIT="$DEV/libsaturn-blender"
PIN=573fd8aa63c6ef0698f455b7cbd8afaba597d2ce
if [[ ! -d "$TOOLKIT/.git" ]]; then git clone https://github.com/celsowm/libsaturn-blender.git "$TOOLKIT"; fi
# Preserve local edits and the user's branch; use a clean pinned worktree.
git -C "$TOOLKIT" fetch origin
mkdir -p "$ROOT/build"
PINNED="$ROOT/build/toolkit-$PIN"
if [[ ! -d "$PINNED" ]]; then git -C "$TOOLKIT" worktree add --detach "$PINNED" "$PIN"; fi
[[ "$(git -C "$PINNED" rev-parse HEAD)" == "$PIN" ]] || die "toolkit revision mismatch"
[[ -z "$(git -C "$PINNED" status --porcelain --untracked-files=no)" ]] || die "pinned toolkit modified"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
if [[ ! -x "$BLENDER" ]]; then BLENDER="$(command -v blender || true)"; fi
[[ -x "$BLENDER" ]] || die "Blender not found; install Blender or set BLENDER"
for cmd in cmake ninja python3; do command -v "$cmd" >/dev/null || die "missing $cmd (Homebrew: brew install cmake ninja python)"; done
if ! command -v sh2eb-elf-gcc >/dev/null && [[ -z "${LIBSATURN_TOOLCHAIN_ROOT:-}" ]]; then
    for p in "$DEV/saturn-tools/bin" "$DEV/sh2eb-elf/bin" "$HOME/saturn-tools/bin" "$SDK_SOURCE/saturn-tools/bin" /opt/local/bin /opt/homebrew/bin /usr/local/bin; do
        if [[ -x "$p/sh2eb-elf-gcc" ]]; then export LIBSATURN_TOOLCHAIN_ROOT="$p"; break; fi
    done
    if [[ -z "${LIBSATURN_TOOLCHAIN_ROOT:-}" ]]; then
        found="$(find "$DEV" -type f -name sh2eb-elf-gcc -print -quit 2>/dev/null || true)"
        [[ -z "$found" ]] || export LIBSATURN_TOOLCHAIN_ROOT="$(dirname "$found")"
    fi
fi
if [[ -n "${LIBSATURN_TOOLCHAIN_ROOT:-}" ]]; then
    [[ -x "$LIBSATURN_TOOLCHAIN_ROOT/sh2eb-elf-gcc" ]] || die "invalid LIBSATURN_TOOLCHAIN_ROOT"
    export PATH="$LIBSATURN_TOOLCHAIN_ROOT:$PATH"
fi
command -v sh2eb-elf-gcc >/dev/null || die "SH-2 toolchain missing; set LIBSATURN_TOOLCHAIN_ROOT to its bin directory"
if ! command -v mkisofs >/dev/null && ! command -v genisoimage >/dev/null && ! command -v xorrisofs >/dev/null; then die "ISO tool missing (brew install xorriso)"; fi
# One shared LibSaturn install for every Saturn project under $DEV.
SDK_BUILD="${LIBSATURN_BUILD:-$SDK_SOURCE/build/sdk}"
SDK="${LIBSATURN_PREFIX:-$DEV/saturn-prefix}"
echo "[xtreme] SDK source: $SDK_SOURCE"
git -C "$SDK_SOURCE" rev-parse HEAD
python3 -m unittest discover -s tests
cc -std=c11 -Wall -Wextra -Werror -I "$SDK_SOURCE/include" -I src src/controller.c tests/test_controller.c -o build/controller-test
cc -std=c11 -Wall -Wextra -Werror -I src tests/test_debug_clock.c -o build/debug-clock-test
build/debug-clock-test
build/controller-test
"$BLENDER" --background --factory-startup --python-exit-code 1 --python tools/create_jade_gully.py -- "$PINNED" "$ROOT/build/jade-gully"
cmake -S "$SDK_SOURCE" -B "$SDK_BUILD" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE="$SDK_SOURCE/cmake/toolchains/sh2eb-elf.cmake" -DLIBSATURN_BUILD_TESTS=OFF -DLIBSATURN_INSTALL=ON -DCMAKE_INSTALL_PREFIX="$SDK"
cmake --build "$SDK_BUILD"
cmake --install "$SDK_BUILD"
# Reconfigure the game from a fresh cache: CMakeSystem.cmake otherwise retains
# the absolute toolchain path from the previous per-project SDK installation.
# Do not touch the shared SDK build cache or delete project files.
GAME_TOOLCHAIN="$SDK/share/libsaturn/toolchains/sh2eb-elf.cmake"
[[ -f "$GAME_TOOLCHAIN" ]] || die "installed toolchain not found: $GAME_TOOLCHAIN"
[[ -f "$SDK/lib/cmake/LibSaturn/LibSaturnConfig.cmake" ]] || die "installed LibSaturn package missing: $SDK"
echo "[xtreme] Fresh game configuration with SDK: $SDK"
cmake --fresh -S "$ROOT" -B "$ROOT/build/game" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE="$GAME_TOOLCHAIN" -DCMAKE_PREFIX_PATH="$SDK" -DLibSaturn_DIR="$SDK/lib/cmake/LibSaturn" -DXTREME_GREYBOX_DIR="$ROOT/build/jade-gully"
cmake --build "$ROOT/build/game" --target xtreme_disc
CUE="$ROOT/build/game/disc/xtreme.cue"
[[ -f "$CUE" ]] || die "disc missing"
echo "[xtreme] Disc: $CUE"
echo "[xtreme] Blender: $ROOT/build/jade-gully/jade_gully.blend"
if [[ "${1:-}" == "--build-only" ]]; then exit 0; fi
LAUNCH="$SDK_SOURCE/emulators/mednafen/run-mednafen.sh"
[[ -f "$LAUNCH" ]] || die "Mednafen launcher missing; open $CUE manually"
if [[ -n "${LIBSATURN_BIOS:-}" ]]; then exec bash "$LAUNCH" "$CUE" --bios "$LIBSATURN_BIOS"; fi
exec bash "$LAUNCH" "$CUE"
