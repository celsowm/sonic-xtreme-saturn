# Jade Gully greybox — iteration 0

Original modular test scene generated from a Blender Python script. No Sega meshes, textures, music or external downloads. Not a playable stage or faithful reproduction.

## Generate

Toolkit baseline: 573fd8aa63c6ef0698f455b7cbd8afaba597d2ce.

```sh
git clone https://github.com/celsowm/libsaturn-blender.git ../libsaturn-blender
git -C ../libsaturn-blender checkout 573fd8aa63c6ef0698f455b7cbd8afaba597d2ce
blender --background --factory-startup --python-exit-code 1 --python tools/create_jade_gully.py -- ../libsaturn-blender build/jade-gully
```

Open build/jade-gully/jade_gully.blend in Blender. Downhill main path, elevated alternate route, temple-proxy finish, gameplay markers. Fork boundaries are provisional, not guaranteed watertight. No loop, waterfall, walls, playable collision or camera logic yet. Preview material colors are not exported in OBJ.

Generated files stay under build/. The game CMake build now bakes the rendered OBJ and JSON into a native solid-color viewer; collision OBJ is still authoring-only. See [VIEWER.md](VIEWER.md) and the README for build and validation.

CI compares authoring and baked exports across repeated headless Blender runs, checks Python tests and C syntax, and uploads the preview files. Emulator and physical hardware acceptance remain separate.
