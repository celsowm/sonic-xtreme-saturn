# Sonic X-treme: Lost Adventure

Unofficial original third-person 3D action platformer concept for Sega Saturn, inspired by Sonic X-treme and Sonic Adventure. Not affiliated with Sega; no proprietary assets included.

**Status:** initial native 3D movement prototype; target build and emulator validation pending. Not a complete game.

Built on [LibSaturn](https://github.com/celsowm/libsaturn) and [Blender Toolkit](https://github.com/celsowm/libsaturn-blender).

## Mac quick start

From this checkout inside ~/dev: `bash scripts/run-mac.sh` (or `--build-only`). See [controller notes](docs/CONTROLLER.md). For a return ZIP with logs and F9 screenshots, use `bash scripts/capture-mac.sh`; see [debug capture](docs/DEBUG_CAPTURE.md).

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
