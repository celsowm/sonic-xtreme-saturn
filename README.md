# Sonic X-treme: Lost Adventure

Unofficial third-person 3D action platformer concept for Sega Saturn, inspired by Sonic X-treme and Sonic Adventure. Not affiliated with Sega. The repository owner has requested that the third-party Sonic R model source and generated LOD be versioned; see [asset provenance and rights](assets/sonic-r/ATTRIBUTION.md). Redistribution permission has not been verified.

**Status:** native Jade Gully greybox/controller passed 11 Ymir probe scenarios; the Sonic R skeletal actor and a 159-face LOD separately passed single-case idle probes at approximately 30 scene submissions/s. Original model and generated LOD are tracked under `assets/sonic-r/`; full-game/physical-Saturn qualification remains open. Not a complete game.

**Performance design target:** stable **30 displayed FPS** at NTSC 320×224, with **60 Hz fixed-step physics**. A displayed frame has ~33.33 ms of total budget. The measured 30 scene submissions/s in the Ymir idle probe are not an independent measurement of output display cadence, and dense-stage stress testing remains pending. See [performance acceptance and roadmap](docs/ROADMAP.md#performance-target-decision-stable-30-fps).

Built on [LibSaturn](https://github.com/celsowm/libsaturn) and [Blender Toolkit](https://github.com/celsowm/libsaturn-blender).

## Real landscape textures (new, Ymir qualification pending)

Jade Gully Adventure now uses **eight real 64×64 Kenney Retro Textures Fantasy CC0 PNGs**, checked into [assets/textures/jade-gully](assets/textures/jade-gully/ATTRIBUTION.md), replacing the temporary generated/noise materials. Their unchanged source pixels are converted by `tools/bake_stage_textures.py` into **32 KiB of VDP1 indexed8 textures** and one shared 256-entry palette; all Adventure stage faces now submit indexed8 textured materials, not flat RGB. The old classic greybox remains selectable. The complete authoring/host CI passed [run 44847714151](https://github.com/celsowm/sonic-xtreme-saturn/actions/runs/44847714151) (26 Python tests, deterministic PNG conversion, C syntax, Blender stage export).

The **new material build has not yet been measured in Ymir or on Saturn hardware**: the earlier 5/5 gameplay PASS predates these indexed textures. The level still needs UV tiling, stronger geography/foliage and final camera polish. For historical reference, see [Sonic X-treme prototype texture preservation](https://textures.spriters-resource.com/saturn/sonicxtreme/)—those original Sega textures were **not** copied into this public repository.

## Jade Gully — experimental Action Adventure layout

The original, Ymir-qualified greybox remains the default. The alternative [Action Adventure stage design](docs/JADE_GULLY_ADVENTURE.md) uses a branching 3D map with forest speed route, upper canopy ridge, exploratory river basin, temple ascent and two broad walkable clearings. **Nine real Kenney CC0 low-poly environment models** (palms, rocks, vegetation, bridge, cliff and ruins) are checked in at [`assets/kenney/`](assets/kenney/ATTRIBUTION.md), with source/license documentation. Blender renders/deforms selected authored GLB props offline; the Saturn binary never loads GLBs at runtime.

Try the new stage separately on a Mac with the established SDK, Blender and Ymir probe:

```sh
cd ~/dev/sonic-xtreme-saturn && git pull --ff-only && bash scripts/qualify-jade-adventure-mac.sh
```

This passes `XTREME_STAGE_LAYOUT=adventure`, validates the graph and per-asset face limits, compiles the alternative stage into a new disc and automatically pushes sanitized screenshots/diagnostics to `ymir-evidence`. The **four-case Adventure smoke qualification passed** in Ymir at 30 scene submissions/s and 34 ms p95; this is not a full traversal, stress test or hardware-displayed FPS verification. To return to the qualified classic stage, unset `XTREME_STAGE_LAYOUT` and run the normal build/probe. Gameplay rings, springs and checkpoints are still stage markers, not implemented collectible/interactive systems.

## Mac quick start

From this checkout inside ~/dev: `bash scripts/run-mac.sh` (or `--build-only`). See [controller notes](docs/CONTROLLER.md). The automated Ymir harness (`python3 scripts/qualify-ymir.py`) publishes logs, screenshots and telemetry in the separate `ymir-evidence` GitHub branch.

CMake uses the tracked `assets/sonic-r/lod-160/sonic.c` and `sonic.h` by default. The one-time `bash scripts/vendor-sonic-r-mac.sh` command copies the original downloaded GLB/texture and generated LOD into the repository, commits them and pushes to `main`. For an explicit actor probe, run `python3 scripts/qualify-ymir.py --require-sonic`; see [Sonic R asset/build notes](docs/SONIC_R_LOCAL.md). The repository and evidence screenshots are public; confirm third-party redistribution rights before publishing.

## Build and inspect Jade Gully

Follow [the greybox generation steps](docs/GREYBOX.md) first, then install the LibSaturn SDK from its documented saturn-release preset. With SDK set to the absolute installation prefix:

```sh
cmake -S . -B build -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$SDK/share/libsaturn/toolchains/sh2eb-elf.cmake" \
  -DCMAKE_PREFIX_PATH="$SDK"
cmake --build build --target xtreme_disc
```

Open the resulting BIN/CUE in an emulator with your own BIOS. D-pad or analog moves, A/C jumps, B respawns, X toggles debug viewer, START exits. See [viewer technical notes](docs/VIEWER.md).

- [Technical roadmap](docs/ROADMAP.md)
- [Jade Gully design](docs/JADE_GULLY.md)
- [Asset research and policy](docs/ASSETS.md)
- [Agent instructions](AGENTS.md)
