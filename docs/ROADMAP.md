# Technical roadmap

Baseline inspected: LibSaturn af86f8518f0d014f2a752ca43035d2278bc9bf8f. Target stock Saturn, NTSC 320x224 and 30 displayed FPS as initial goals (not measured). PAL and optional RAM cart enhancements follow stock qualification. Prefer bounded data and fixed-point math; no dynamic allocation in frame hot paths.

## P0: bootstrap
Installed CMake package (LibSaturn::Saturn, libsaturn_configure_executable, libsaturn_add_disc); smoke test using saturn/app.h and VDP1 rectangle. Verify ELF/map, BIN/CUE, launch in Ymir and Mednafen. Pin the actual SDK revision in evidence.

## P1: greybox
Original Blender test course: descent, ramp, bank, loop, gap and checkpoint. Export via companion toolkit after M1/M2; before that, use reviewed synthetic geometry and existing converters. Inspect runtime_3d and world_lod3d_demo. Use saturn/scene.h; world LOD, command budget and fade. Verify coordinate conventions, clipping, painter ordering and texture seams. Distinguish face counts, emitted VDP1 commands, frame submissions and field cadence.

## P1.5: debug HUD and reproducible diagnostics (blocking P2 qualification)

Single-step and Mac evidence capture implemented: [DEBUG_CAPTURE.md](DEBUG_CAPTURE.md). Host clock tests, persistent last-ray snapshot and telemetry v2; L pause, R single-step in play mode. Emulator validation remains pending.

Initial implementation in commit e6d7d464f875b8f0b87284ebe27f0eccc5b72a9c: compact, physics, camera/input, renderer/timing, memory/assets and off; Y cycles pages, Z toggles ray/normal/velocity screen-space overlay. Uses SDK HUD/font, reserves at most 456 glyph commands plus three lines, starts final overlay after scene flush. Versioned telemetry symbol `xtreme_debug` (magic XTDB, version 1, byte size, 32-bit big-endian fields; layout in src/main.c). Phase timings in ms, submission rate multiplied by ten; not display FPS. Ray counters valid only when queried that frame; respawns inferred on fall return and counted on manual reset. VDP1 texture bytes free is actual; other memory pools are N/A. No changes to the controller algorithm. Pending: emulator qualification, independent display timing, release compile-out, pause/single step, complete collision draw, replay and ZIP automation.

Test with `bash scripts/run-mac.sh`; capture every page, toggle Z on a slope and while landing, compare with HUD off, report error/command budgets. Do not consider this gate passed until screenshots and repeatable tests confirm it.
First Mednafen screenshot supplied on 2026-11-20 shows the greybox and markers rendering; movement, collision, camera behavior and displayed cadence are not yet qualified. Add instrumentation before replacing the proxy with final art.

Use the existing SDK `saturn/hud.h`, `sat_hud_init_default`, `sat_hud_text/value/bar`, `saturn/time.h` and scene counters, not a second HUD engine. Reserve VDP1 overlay commands in sat_scene_begin before world submission; draw after scene flush and before frame end. Measure glyph/command usage, cap lines and text length (8x8 font, 320x224), reserve only the selected page's worst-case budget and treat diagnostic overflow as a distinct error. Keep normal gameplay HUD separate.

Debug controls: Y cycles OFF -> compact -> physics -> camera/input -> renderer/timing -> memory/assets; Z toggles optional world debug geometry (bounded). X remains camera inspection. L toggles pause and R advances one simulation tick in play mode; resume clears time accumulator, not player state. Compact view defaults ON in debug builds; release defaults OFF and can compile diagnostics out.

| Page | Data and units |
| --- | --- |
| Compact | build ID, mode, grounded/airborne, speed in m/s, ms/frame, completed submissions/s (not display FPS), last error |
| Physics | Q16.16 feet XYZ in metres (signed, fixed decimal), velocity XYZ in m/s, horizontal speed, ground normal XYZ, slope, last ground query hit/miss, face ID, distance, jump buffer, respawn count, tick index, ticks/frame, dropped ms; rolling/homing/loop adhesion when implemented |
| Camera/input | raw digital mask, analog axes and deadzone, normalized input, camera eye/target XYZ, mode, lookahead, occlusion hit and camera transition when implemented |
| Renderer/timing | submitted/culled/clipped/skipped/rejected faces, world VDP1 commands, command capacity, reserved HUD commands, budget blocks, CPU phase timings (physics/camera/scene/flush/HUD), rolling mean/max or p95 with fixed sample window; profile counters only if SDK enables them |
| Memory/assets | actual bytes and capacity per pool (WRAM-H/L, VDP1 command/texture, VDP2 VRAM, SCSP), resident sectors/LOD and disc/audio queues only when those systems expose measurements; otherwise N/A, never fabricated zeros |

World overlay: last support ray with hit marker, surface normal, velocity vector, collision mesh edges, player shape, camera target/frustum and sector bounds as implemented. Render through SDK with explicit debug budgets; a debug overlay must not change collision or player state. No unbounded per-frame text formatting or allocation. Preserve last valid snapshot on errors, report stage/error and retain telemetry for dump even if screen output fails. Use signed formatting (SDK fmt helpers or bounded integer conversion), no target float printf.

Add a versioned fixed-width telemetry block with magic/version, simulation counters, current player state, ray hits, scene stats and phase timings; stable map symbol and documented units. Keep counters available independently of overlay visibility. Capture deterministic scripted routes in Ymir, compare Mednafen manually and record real-hardware evidence separately. Disc build/run script should optionally export a return ZIP with build ID, SDK revision, map, logs, screenshots and telemetry (no BIOS/ROM). On-screen submission rates and field cadence must be separate; display FPS only from an independently verified display measurement.

Acceptance: verify on/off/each page and all buttons in both emulators, no text overflow/clipping or VDP1 command starvation, no physics divergence on replay with HUD enabled vs disabled, signed coordinate and fixed-point display tests, known forced errors/respawn, bounded diagnostic overhead with HUD off/on. Capture start, ramp, airborne, landing, fork, fall/reset plus renderer page. Make unavailable counters explicit. P2/P3 gates require these screenshots and replay evidence before final art.

## P2: movement

P2.2 first pass: static friction for shallow slopes, 12 cm downward SDK sphere sweep only after a ray miss, fixed-tick SDK chase camera with speed-aware target offset and reset snap, dark HUD rows, completed-frame XTDB v3 snapshots (84 words / 336 bytes), jump and landing counters. Ymir harness now runs 11 scenarios with additional idle comparison, stationary jump/landing and steered bend. Ymir qualification passed for the current 11 scenarios (game 29ee2b6, SDK 08ad63b, evidence 84e25de51c7f02451a323c8e8ed75600b05e2e8f): all three comparisons passed; zero reported world/HUD errors, late swaps and draw timeouts in terminal snapshots; 60.0 submissions/s in each terminal rate sample. First bend finished grounded at (4.006, 2.514, -33.778) m, without respawn or sphere recovery. Static friction and stationary jump/landing verified. Support selection now favors continuation of the prior ground plane on overlapping branches; airborne misses skip sphere recovery. Sphere recovery itself has no positive-hit evidence yet. Final bend screenshot shows partial proxy occlusion by the upper route; camera occlusion and painter ordering remain open. Moving jump scenarios still end off-course. No full body/wall sweep, loop adhesion, full-course acceptance, independent display timing or physical hardware qualification yet. Baseline return at game 307233d / SDK 184076b: all eight original checks passed, 59.9–60 submissions/s in Ymir, but straight-line jump route left the ribbon. The new tests must establish actual landing and no idle drift; do not equate baseline PASS with full movement qualification.
Create game-specific character controller with grounded/airborne/rolling/homing states, tangent acceleration, slope projection, surface adhesion and separation, jump, braking and coyote/contact tolerance. Fixed simulation tick independent of display, replay input on host. Use SDK collision queries and mesh acceleration; physics3_world is sphere/box-oriented, not assumed to be a complete Sonic controller. Sweep high-speed motion; test loops through full rotation, seams, landing, tunneling and loss of adhesion. No copied proprietary physics code.

## P3: camera and animation
Third-person chase, speed-aware look-ahead, obstruction sweeps, volume constraints, authored camera rails and transitions; avoid mandatory fisheye. Support digital and 3D pads. Original proxy character, evaluate existing GLB, skeletal_animation_3d, CPU skinning and baked pose alternatives. Measure memory and transformation cost.

## P4: action stage
Rings, springs, dash panels, original enemy proxies, homing target scoring, checkpoints, damage/recovery, goal, timer and restart. Stable semantic entity IDs, sector reload rules and replay tests. One polished 3–5 minute target course before new zones. Avoid obligatory scripted movement in normal gameplay.

## P5: production
Use HLOD and sector residency, VDP2 sky/ground/water where appropriate, audio/music through existing music.h and disc scheduler, prefetch around camera routes. Measure contention during transitions; no required cart. Maintain per-pool memory ledger (WRAM-H/L, VDP1, VDP2, SCSP). Compare overdraw, command count, frame-time percentiles, audio underruns and dropped frames at repeatable route checkpoints. Validate hardware timing independently.

## Acceptance evidence
Host tests -> SH-2 build -> deterministic disc -> Ymir captured route -> Mednafen comparison -> physical Saturn. For every run record commit, tool versions, BIOS identifier (never distribute BIOS), inputs, screenshots, frame/field metrics and failures. Include the P1.5 debug HUD pages and telemetry snapshot; compare HUD disabled/enabled replay results. A 30 FPS target is not a result. No unsupported assets in public source or releases.
