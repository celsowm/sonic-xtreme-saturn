# Sonic X-treme: Lost Adventure

Unofficial original third-person 3D action platformer concept for Sega Saturn, inspired by Sonic X-treme and Sonic Adventure. Not affiliated with Sega; no proprietary assets included.

**Status:** native 3D greybox viewer implemented; target build and emulator validation pending. Not a playable game.

Built on [LibSaturn](https://github.com/celsowm/libsaturn) and [Blender Toolkit](https://github.com/celsowm/libsaturn-blender).

## Build and inspect Jade Gully

Follow [the greybox generation steps](docs/GREYBOX.md) first, then install the LibSaturn SDK from its documented saturn-release preset. With SDK set to the absolute installation prefix:

```sh
cmake -S . -B build -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$SDK/share/libsaturn/toolchains/sh2eb-elf.cmake" \
  -DCMAKE_PREFIX_PATH="$SDK"
cmake --build build --target xtreme_disc
```

Open the resulting BIN/CUE in an emulator with your own BIOS. D-pad pans across the stage, L/R lower/raise the camera, A selects an overhead view, B restores the starting view, START exits. See [viewer technical notes](docs/VIEWER.md).

- [Technical roadmap](docs/ROADMAP.md)
- [Jade Gully design](docs/JADE_GULLY.md)
- [Asset research and policy](docs/ASSETS.md)
- [Agent instructions](AGENTS.md)
