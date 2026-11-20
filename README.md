# Sonic X-treme: Lost Adventure

Unofficial original third-person 3D action platformer concept for Sega Saturn, inspired by Sonic X-treme and Sonic Adventure. Not affiliated with Sega; no proprietary assets included.

**Status:** native Jade Gully greybox and controller have passed 11 Ymir probe scenarios. Optional locally generated Sonic R skeletal actor integration is implemented but awaits Mac build and emulator qualification. Not a complete game.

Built on [LibSaturn](https://github.com/celsowm/libsaturn) and [Blender Toolkit](https://github.com/celsowm/libsaturn-blender).

## Mac quick start

From this checkout inside ~/dev: `bash scripts/run-mac.sh` (or `--build-only`). See [controller notes](docs/CONTROLLER.md). The automated Ymir harness (`python3 scripts/qualify-ymir.py`) publishes logs, screenshots and telemetry in the separate `ymir-evidence` GitHub branch.

If `assets/private/sonic-r/saturn/sonic.c` and `sonic.h` exist, CMake automatically builds the skinned and animated Sonic prototype instead of the blue diamond. **No private asset files are committed or uploaded.** To explicitly verify that the character is actually rendering, run `python3 scripts/qualify-ymir.py --require-sonic`. See [local Sonic R integration](docs/SONIC_R_LOCAL.md). GitHub evidence screenshots are public; only use assets you are authorized to publish images of.

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
