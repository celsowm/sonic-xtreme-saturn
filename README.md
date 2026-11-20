# Sonic X-treme: Lost Adventure

Unofficial fan-project concept: an original third-person 3D action platformer for Sega Saturn, inspired by the visual direction of the cancelled Sonic X-treme and the movement of Sonic Adventure.

**Status: bootstrap / hardware smoke test, not a playable game.** Not affiliated with Sega. No proprietary game assets included.

Built on [LibSaturn](https://github.com/celsowm/libsaturn) and the companion [Blender Toolkit](https://github.com/celsowm/libsaturn-blender).

## Build the smoke test
Install the LibSaturn SDK using its documented saturn-release preset. Set SDK to the absolute installation prefix, then:
```sh
cmake -S . -B build -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$SDK/share/libsaturn/toolchains/sh2eb-elf.cmake" \
  -DCMAKE_PREFIX_PATH="$SDK"
cmake --build build --target xtreme_disc
```
This displays an original geometric marker and exits the loop on START. Build/run still requires SH-2 toolchain and emulator qualification. Open the resulting BIN/CUE through the emulator with your own BIOS.

- [Technical roadmap](docs/ROADMAP.md)
- [Jade Gully design](docs/JADE_GULLY.md)
- [Asset research and policy](docs/ASSETS.md)
- [Agent instructions](AGENTS.md)
