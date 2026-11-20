# Sonic X-treme: Lost Adventure

Unofficial third-person 3D action platformer concept for Sega Saturn, inspired by Sonic X-treme and Sonic Adventure. Not affiliated with Sega. The repository owner has requested that the third-party Sonic R model source and generated LOD be versioned; see [asset provenance and rights](assets/sonic-r/ATTRIBUTION.md). Redistribution permission has not been verified.

**Status:** native Jade Gully greybox/controller passed 11 Ymir probe scenarios; the Sonic R skeletal actor and a 159-face LOD separately passed single-case idle probes at approximately 30 scene submissions/s. The model and generated LOD are intended to be tracked under `assets/sonic-r/`; full-game/physical-Saturn qualification remains open. Not a complete game.

Built on [LibSaturn](https://github.com/celsowm/libsaturn) and [Blender Toolkit](https://github.com/celsowm/libsaturn-blender).

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
