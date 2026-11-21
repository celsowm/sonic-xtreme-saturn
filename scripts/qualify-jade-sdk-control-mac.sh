#!/usr/bin/env bash
# Controlled Ymir A/B: same game HEAD + stable, published LibSaturn revision.
# Never reset the developer's LibSaturn checkout or rewrite ymir-evidence.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEV="$(cd "$ROOT/.." && pwd)"
PIN="08e39e9dfb235a2ad88c17c690178c5ab0927e6f"
die(){ printf '[sdk-control] %s\n' "$*" >&2; exit 2; }

SOURCE="${LIBSATURN_SOURCE:-$DEV/lib-saturn}"
[[ -f "$SOURCE/CMakeLists.txt" ]] || SOURCE="$DEV/libsaturn"
[[ -f "$SOURCE/CMakeLists.txt" ]] || die "LibSaturn checkout not found (set LIBSATURN_SOURCE)"
SOURCE="$(cd "$SOURCE" && pwd)"
ORIGINAL="$(git -C "$SOURCE" rev-parse HEAD)"
GAME="$(git -C "$ROOT" rev-parse HEAD)"
[[ -z "$(git -C "$ROOT" status --porcelain --untracked-files=no)" ]] || die "game has tracked local changes; A/B would not be reproducible"

echo "[sdk-control] Game revision: $GAME"
echo "[sdk-control] Local SDK (unmodified): $ORIGINAL"
echo "[sdk-control] Control SDK: $PIN"

if ! git -C "$SOURCE" cat-file -e "$PIN^{commit}" 2>/dev/null; then
  git -C "$SOURCE" fetch origin "$PIN" || die "published SDK commit cannot be fetched"
fi

WORKTREE="$ROOT/build/sdk-control-$PIN"
mkdir -p "$ROOT/build"
if [[ ! -d "$WORKTREE" ]]; then
  git -C "$SOURCE" worktree add --detach "$WORKTREE" "$PIN"
fi
[[ "$(git -C "$WORKTREE" rev-parse HEAD)" == "$PIN" ]] || die "SDK control worktree at unexpected revision"
[[ -z "$(git -C "$WORKTREE" status --porcelain --untracked-files=no)" ]] || die "SDK control worktree is modified"

# The existing working SDK has the local Ymir probe/BIOS; the clean control
# worktree is deliberately source-only. Pass the probe explicitly.
if [[ -z "${YMIR_PROBE:-}" ]]; then
  [[ -x "$SOURCE/harness/build-macos/probe" ]] || die "Ymir probe missing; set YMIR_PROBE"
  export YMIR_PROBE="$SOURCE/harness/build-macos/probe"
fi
if [[ -z "${LIBSATURN_BIOS:-}" && -f "$SOURCE/bios/firmware/mpr-17933.bin" ]]; then
  export LIBSATURN_BIOS="$SOURCE/bios/firmware/mpr-17933.bin"
fi

# Isolate the SDK build and install; the developer's SDK prefix/cache and
# checkout are never touched. qualify-ymir.py already writes its own ZIP.
export LIBSATURN_SOURCE="$WORKTREE"
export LIBSATURN_BUILD="$ROOT/build/sdk-control-build-$PIN"
export LIBSATURN_PREFIX="$ROOT/build/sdk-control-prefix-$PIN"
export XTREME_STAGE_LAYOUT=adventure

cd "$ROOT"
set +e
python3 scripts/qualify-ymir.py --require-sonic --no-publish \
  --case idle --case curve_route --case offroad_right
rc=$?
set -e
python3 - "$ROOT/build" "$PIN" "$GAME" <<'PY'
import glob,json,sys,zipfile
from pathlib import Path
out,pin,game=Path(sys.argv[1]),sys.argv[2],sys.argv[3]
zips=sorted(out.glob("ymir-evidence-*-return.zip"),key=lambda x:x.stat().st_mtime)
if not zips:
    raise SystemExit("[sdk-control] No evidence ZIP produced")
archive=zips[-1]
with zipfile.ZipFile(archive) as z:
    summary=json.loads(z.read("summary.json"))
print("[sdk-control] Local ZIP:",archive)
print("[sdk-control] Ymir status:",summary.get("status"))
print("[sdk-control] SDK:",summary.get("sdk_commit"))
print("[sdk-control] Game:",summary.get("game_commit"))
for name,case in summary.get("cases",{}).items():
    t=case.get("telemetry",{})
    f=case.get("frame_pacing",{})
    checks=case.get("checks",{})
    failed=[k for k,v in checks.items() if not v]
    print(f"[sdk-control] {name}: rate={t.get('submission_rate_hz')} scene/s "
          f"p95={f.get('frame_ms_p95')}ms scene={f.get('scene_ms_p95')}ms "
          f"checks_failed={failed}")
    rp=case.get("render_profile")
    if rp:
        last=rp.get("terminal") or {}
        print(f"[sdk-control] {name} XRH1: begin={rp['scene_begin_ms_p95']}ms "
              f"stage={rp['stage_ms_p95']}ms actor={rp['actor_ms_p95']}ms "
              f"flush={rp['flush_ms_p95']}ms (all p95); "
              f"stage_submit={last.get('stage_submitted')} "
              f"marker_submit={last.get('marker_submitted')} "
              f"actor_submit={last.get('actor_submitted')} "
              f"vis_skip={last.get('stage_visibility_skipped')} "
              f"lod_skip={last.get('stage_lod_skipped')} "
              f"painter_culled={last.get('painter_culled')}")
    else:
        print(f"[sdk-control] {name} XRH1: UNAVAILABLE "
              f"({case.get('render_profile_decode_error','no record')})")
if summary.get("sdk_commit")!=pin or summary.get("game_commit")!=game:
    raise SystemExit("[sdk-control] Revision mismatch; A/B is invalid")
print("[sdk-control] Compare with the previous Ymir 20/s / p95 50–51ms. "
      "This ZIP was NOT published.")
PY
exit "$rc"
