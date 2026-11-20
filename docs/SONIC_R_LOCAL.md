# Sonic R — versioned repository asset pipeline

The Sonic character is a **repository asset** as requested, not a dependency on `assets/private/`. The original user-supplied files are stored under:

- `assets/sonic-r/source/sonic.glb` (skeletal source, 11 joints, 17 source animations)
- `assets/sonic-r/textures/sonic_add_signed_2.png`
- `assets/sonic-r/lod-160/sonic.c`, `sonic.h`, `sonic.ska`, `report.json` (generated and versioned)

See `assets/sonic-r/ATTRIBUTION.md` for original source URL, SHA-256 values, processing notes, and unverified licensing status. The Sketchfab archive had no license file. Public redistribution rights must be checked; this document is **not** permission to redistribute third-party characters.

## Initial import into main

On the Mac with the previously downloaded model and already generated 160-triangle variant, run:

```sh
cd ~/dev/sonic-xtreme-saturn && git pull --ff-only && bash scripts/vendor-sonic-r-mac.sh
```

The script uses the existing `assets/private/sonic-r/` conversion or the downloaded ZIP, verifies that both original files match the supplied archive SHA-256 values, copies only the known model/texture and generated 160-triangle variant into `assets/sonic-r/`, stages only those files, commits to `main`, and performs a normal (non-force) Git push. It then runs the single `idle` Ymir case and pushes the usual diagnostics to `ymir-evidence`. No ROM, BIOS, disc image or full RAM dump is committed.

## Reproducible build from clone

`CMakeLists.txt` uses `assets/sonic-r/lod-160` by default. Its generated `sonic.c`/`sonic.h` are compiled with `src/sonic_actor.c`, using native LibSaturn skeletal sampling, CPU skinning, immutable indexed8 material bindings and depth-sorted scene submission. GLB and supplemental texture remain available for reimport or offline tooling.

Once the asset commit is pushed, `bash scripts/run-mac.sh --build-only` compiles the character from the tracked files; it does **not** require previous local conversions. The `--require-sonic` flag in `scripts/qualify-ymir.py` fails rather than silently accepting the blue debug proxy if generated files are absent.

For an alternate generated LOD:

```sh
XTREME_SONIC_DIR="$PWD/assets/sonic-r/lod-120" python3 scripts/qualify-ymir.py --require-sonic --case idle
```

Generated paths are versioned: `bash scripts/qualify-sonic-lod-mac.sh 120` reads `assets/sonic-r/source/sonic.glb` and writes `assets/sonic-r/lod-120/`; subsequent commits can add newly qualified variants. The importer may retry smaller texture scales when simplified UV faces exceed the per-face 96x96 default. Resource/texture gates remain mandatory.

## Observed performance and acceptance

The original 286-face variant passed the idle Ymir probe at approximately 30.0 scene submissions/s, 189 skinned vertices, 281 baked textures, scene preparation 17 ms and character submission 6 ms. The 159-face LOD test from 20 November 2026 passed its single `idle` Ymir case with 125 vertices, 148 textures, 11 joints, 264,232 VDP1 VRAM bytes free and 30 scene submissions/s. It **did not** increase frame rate to 60 FPS. This is a submission-rate metric, not an independent LCD/display FPS measurement.

The whole 11-scenario gameplay suite was last completed without the Sonic actor; after repository vendoring, rerun the full suite and inspect actual character screenshots, movement animations, VRAM and scene timings:

```sh
python3 scripts/qualify-ymir.py --require-sonic
```

The `SXAC` v2 character telemetry records state, error, texture registry count, clip, animation/skin/draw times, remaining VRAM and successful draws. The `XBT1` boot telemetry detects early initialization errors independently of `XTDB` v3. The full source asset is versioned in `main` only; `ymir-evidence` stores sanitized logs, screenshots, SHA-256 hashes and JSON but no additional GLB, SKA, ELF, ISO or BIOS copies.

## Remaining technical work

Character direction relative to input, cross-fading clips, animation speed matching, near-plane/occlusion handling, draw-time optimization, derived texture budget, full route qualification, and actual Saturn hardware validation remain open. The original Sega asset permissions and exact contributor license are not yet verified.

## Movement and pacing qualification (candidate)

The actor telemetry is now `SXAC v3` and records a bitmask of animation clips visited, total transitions, physical takeoff/landing events and grounded/airborne simulation ticks. Clip mask bits: 0=idle, 1=highspeed, 2=jump, 3=falling, 4=landing, 5=brake, 6=turn_left, 7=turn_right. This proves a clip *was entered*, not that it looked correct in the screenshot; visual inspection remains necessary.

The 11 Ymir replays now check that `jump_in_place` visits jump/fall/landing with physical takeoff/landing, `curve_route` visits running, and `fall_reset` visits falling. Actor tick/position agreement with the controller, paused/single-step actor determinism and HUD-on/off actor equivalence are also checked. Runtime acceptance demands no world/HUD errors, late swaps, draw timeouts, dropped simulated time or budget overruns.

A new independent WRAM-H record `XFP1 v1` stores a 64-frame circular timing sample (frame interval, simulation, scene and flush, all in ms). `qualify-ymir.py` exports `frame-pacing.json` with measured p50/p95/p99/max, and requires at least 30 samples, p95 no greater than 38 ms, terminal frame <=40 ms and at least 29.0 scene submissions/s. These are emulator instrumentation/diagnostic gates, **not** a hardware-verified 30 FPS displayed cadence or worst-case stage performance proof. The 11-case result with all these new gates remains pending until a new run is published.

Run all scenarios and automatically upload only sanitized ZIP/screenshot/JSON/log evidence to the dedicated `ymir-evidence` branch:

```sh
cd ~/dev/sonic-xtreme-saturn && git pull --ff-only && python3 scripts/qualify-ymir.py --require-sonic
```

If this run reports `review`, inspect `latest/summary.json`, `latest/<case>/sonic-telemetry.json` and `latest/<case>/frame-pacing.json`; retain failures and tighten renderer/animation logic rather than relaxing acceptance numbers without evidence.
