#!/usr/bin/env bash
# Controlled Ymir A/B: same game HEAD + stable, published LibSaturn revision.
# Automatically push the sanitized ZIP and screenshots to a SEPARATE GitHub
# evidence branch. Never reset the developer's SDK or rewrite full-run evidence.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEV="$(cd "$ROOT/.." && pwd)"
PIN="08e39e9dfb235a2ad88c17c690178c5ab0927e6f"
EVIDENCE_BRANCH="ymir-sdk-control-evidence"

# Recover the latest local ZIP without rebuilding or re-running the emulator:
#   bash scripts/qualify-jade-sdk-control-mac.sh --upload-last
# This also uploads the last successful/review run made before auto-upload.
if [[ "${1:-}" == "--upload-last" ]]; then
  cd "$ROOT"
  exec python3 scripts/qualify-ymir.py --publish-latest \
    --evidence-branch "$EVIDENCE_BRANCH" --expected-sdk "$PIN"
fi
[[ $# -eq 0 ]] || { printf '[sdk-control] Unexpected option: %s\n' "$*" >&2; exit 2; }

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

# Isolate the SDK build and install; developer SDK prefix/cache and checkout
# remain untouched. The harness uploads only a *sanitized* ZIP and screenshots
# to the dedicated ymir-sdk-control-evidence branch, including REVIEW/FAILED
# diagnostic runs, leaving the full-run ymir-evidence branch intact.
export LIBSATURN_SOURCE="$WORKTREE"
export LIBSATURN_BUILD="$ROOT/build/sdk-control-build-$PIN"
export LIBSATURN_PREFIX="$ROOT/build/sdk-control-prefix-$PIN"
export XTREME_STAGE_LAYOUT=adventure

cd "$ROOT"
set +e
python3 scripts/qualify-ymir.py --require-sonic \
  --evidence-branch "$EVIDENCE_BRANCH" \
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
    buildlog=z.read("build.log").decode("utf-8","replace") if "build.log" in z.namelist() else ""
print("[sdk-control] Local ZIP:",archive)
print("[sdk-control] Ymir status:",summary.get("status"))
print("[sdk-control] SDK:",summary.get("sdk_commit"))
print("[sdk-control] Game:",summary.get("game_commit"))
if summary.get("failures"):
    print("[sdk-control] Failures:", " | ".join(map(str,summary["failures"])))
if summary.get("build_exit") not in (None,0):
    print("[sdk-control] Build exit:",summary["build_exit"])
    lines=buildlog.splitlines()
    diagnostic=[i for i,line in enumerate(lines) if any(term in line.lower() for term in
        ("error:", "fatal error", "undefined reference", "failed:", "build stopped", "cmake error"))]
    if diagnostic:
        selected=set()
        for i in diagnostic[:12]:
            selected.update(range(max(0,i-3),min(len(lines),i+4)))
        print("[sdk-control] Compiler diagnostics from sanitized ZIP build.log:")
        for i in sorted(selected):
            print(f"[build.log:{i+1}] {lines[i]}")
    elif lines:
        print("[sdk-control] No compiler error marker; last 45 build lines:")
        for i,line in enumerate(lines[-45:],start=max(1,len(lines)-44)):
            print(f"[build.log:{i}] {line}")
    else:
        print("[sdk-control] No build.log included in ZIP")
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
    sw=case.get("frame_sync")
    if sw:
        print(f"[sdk-control] {name} XSW1: begin_p95={sw['begin_ms_p95']}ms "
              f"end_p95={sw['end_ms_p95']}ms work_p95={sw['active_work_ms_p95']}ms "
              f"gap_p95={sw['prior_end_gap_ms_p95']}ms "
              f"begin_fields_p95={sw['begin_fields_p95']} "
              f"end_fields_p95={sw['end_fields_p95']} "
              f"begin_draw_waits={sw['begin_draw_waits_total']} "
              f"end_draw_waits={sw['end_draw_waits_total']}")
        for slow in sw.get("slow_frames",[]):
            print(f"[sdk-control] {name} slow frame {slow['frame']}: "
                  f"interval={slow['interval_ms']}ms "
                  f"begin={slow['begin_call_ms']}ms "
                  f"end={slow['end_call_ms']}ms "
                  f"cpu_work={slow['active_work_ms']}ms "
                  f"begin_fields={slow['begin_fields']} "
                  f"end_fields={slow['end_fields']} "
                  f"begin_draw_waits={slow['begin_draw_waits']} "
                  f"end_draw_waits={slow['end_draw_waits']}")
    else:
        print(f"[sdk-control] {name} XSW1: UNAVAILABLE "
              f"({case.get('frame_sync_decode_error','no record')})")
if summary.get("sdk_commit")!=pin or summary.get("game_commit")!=game:
    raise SystemExit("[sdk-control] Revision mismatch; A/B is invalid")
print("[sdk-control] GitHub evidence: "
      "https://github.com/celsowm/sonic-xtreme-saturn/tree/ymir-sdk-control-evidence/latest")
print("[sdk-control] ZIP and screenshots are published automatically unless a "
      "network/permission error was reported above.")
PY
exit "$rc"
