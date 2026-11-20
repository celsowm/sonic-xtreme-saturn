# Jade Gully greybox — iteration 0

Original modular test scene generated from a Blender Python script. No Sega meshes, textures, music or external downloads. Not a playable stage or faithful reproduction.

## Generate

Toolkit baseline: 573fd8aa63c6ef0698f455b7cbd8afaba597d2ce.

```sh
git clone https://github.com/celsowm/libsaturn-blender.git ../libsaturn-blender
git -C ../libsaturn-blender checkout 573fd8aa63c6ef0698f455b7cbd8afaba597d2ce
blender --background --factory-startup --python-exit-code 1 --python tools/create_jade_gully.py -- ../libsaturn-blender build/jade-gully
```

Open build/jade-gully/jade_gully.blend in Blender. Downhill main path, elevated alternate route, temple-proxy finish, gameplay markers. Fork boundaries are provisional, not guaranteed watertight. No loop, waterfall, walls, complete collision or dynamic camera logic yet. Preview material colors are not exported in OBJ.

Generated files stay under build/. The game CMake build now bakes the rendered OBJ and JSON into a native solid-color viewer; collision OBJ is baked independently for the ground-query prototype. See [VIEWER.md](VIEWER.md) and the README for build and validation.

CI compares authoring and baked exports across repeated headless Blender runs, checks Python tests and C syntax, and uploads the preview files. Emulator and physical hardware acceptance remain separate.

## Lightweight set dressing — qualification candidate

The Blender generator now authors three low-poly palms (a rectangular trunk and eight triangles in the canopy), four four-triangle rock silhouettes, and one two-triangle cyan waterfall plane. They are built from new source geometry in `tools/create_jade_gully.py` and have deterministic suffixes `_trunk`, `_canopy`, `_rock`, `_water`. The narrow OBJ converter assigns flat palette colors to these groups; the playable ribbons retain their calibrated route palettes.

**Collision isolation:** only `main_route` and `upper_route` are duplicated with `saturn_mesh="collision"`, before any props are constructed. All new props use `saturn_mesh="render"`; they are purely visual and have no physical collision yet. The exporter supports 256 rendered faces in this vertical slice; do not silently raise this budget if a scene overflows. Run the Blender export, Python host tests, SH-2 compile and Ymir probe to validate the generated geometry and painter. No completed emulator qualification of this new set dressing has been recorded yet.

Textures, rock/tropical terrain detail, fog, low-water surfaces, animated vegetation and VDP2 sky remain separate future stages. This first scenic layer is intentionally inexpensive, not a claim of final visual quality.
