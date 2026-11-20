# Technical roadmap

Baseline inspected: LibSaturn af86f8518f0d014f2a752ca43035d2278bc9bf8f. Target stock Saturn, NTSC 320x224 and 30 displayed FPS as initial goals (not measured). PAL and optional RAM cart enhancements follow stock qualification. Prefer bounded data and fixed-point math; no dynamic allocation in frame hot paths.

## P0: bootstrap
Installed CMake package (LibSaturn::Saturn, libsaturn_configure_executable, libsaturn_add_disc); smoke test using saturn/app.h and VDP1 rectangle. Verify ELF/map, BIN/CUE, launch in Ymir and Mednafen. Pin the actual SDK revision in evidence.

## P1: greybox
Original Blender test course: descent, ramp, bank, loop, gap and checkpoint. Export via companion toolkit after M1/M2; before that, use reviewed synthetic geometry and existing converters. Inspect runtime_3d and world_lod3d_demo. Use saturn/scene.h; world LOD, command budget and fade. Verify coordinate conventions, clipping, painter ordering and texture seams. Distinguish face counts, emitted VDP1 commands, frame submissions and field cadence.

## P2: movement
Create game-specific character controller with grounded/airborne/rolling/homing states, tangent acceleration, slope projection, surface adhesion and separation, jump, braking and coyote/contact tolerance. Fixed simulation tick independent of display, replay input on host. Use SDK collision queries and mesh acceleration; physics3_world is sphere/box-oriented, not assumed to be a complete Sonic controller. Sweep high-speed motion; test loops through full rotation, seams, landing, tunneling and loss of adhesion. No copied proprietary physics code.

## P3: camera and animation
Third-person chase, speed-aware look-ahead, obstruction sweeps, volume constraints, authored camera rails and transitions; avoid mandatory fisheye. Support digital and 3D pads. Original proxy character, evaluate existing GLB, skeletal_animation_3d, CPU skinning and baked pose alternatives. Measure memory and transformation cost.

## P4: action stage
Rings, springs, dash panels, original enemy proxies, homing target scoring, checkpoints, damage/recovery, goal, timer and restart. Stable semantic entity IDs, sector reload rules and replay tests. One polished 3–5 minute target course before new zones. Avoid obligatory scripted movement in normal gameplay.

## P5: production
Use HLOD and sector residency, VDP2 sky/ground/water where appropriate, audio/music through existing music.h and disc scheduler, prefetch around camera routes. Measure contention during transitions; no required cart. Maintain per-pool memory ledger (WRAM-H/L, VDP1, VDP2, SCSP). Compare overdraw, command count, frame-time percentiles, audio underruns and dropped frames at repeatable route checkpoints. Validate hardware timing independently.

## Acceptance evidence
Host tests -> SH-2 build -> deterministic disc -> Ymir captured route -> Mednafen comparison -> physical Saturn. For every run record commit, tool versions, BIOS identifier (never distribute BIOS), inputs, screenshots, frame/field metrics and failures. A 30 FPS target is not a result. No unsupported assets in public source or releases.
