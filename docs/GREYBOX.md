# Jade Gully greybox — iteration 0

Original modular test scene generated from a reviewed Blender Python script. No Sega meshes, textures, music or external downloads. This is the first authoring fixture, not a playable Saturn stage or a faithful copy of the original Jade Gully.

## Generate

Clone sibling checkouts. Toolkit baseline for this recipe:
573fd8aa63c6ef0698f455b7cbd8afaba597d2ce.

```sh
git clone https://github.com/celsowm/libsaturn-blender.git ../libsaturn-blender
git -C ../libsaturn-blender checkout 573fd8aa63c6ef0698f455b7cbd8afaba597d2ce
blender --background --factory-startup --python-exit-code 1 --python tools/create_jade_gully.py -- ../libsaturn-blender build/jade-gully
```

Open build/jade-gully/jade_gully.blend in Blender. The original course has a downhill main path, an elevated alternate route, a temple-proxy finish and markers for gameplay. Render and collision roles are separate. The fork boundaries are provisional and not guaranteed watertight; no loop, waterfall, walls, playable collision or camera logic yet. Preview material colors are not exported in OBJ.

Exported JSON and two greybox OBJ files can be checked into neither source nor release by default; regenerate from the script. Use the toolkit exporter for subsequent edits. Mesh vertices remain in RH Z-up metres. Coordinate conversion, UVs/textures and geometric qualification must happen before SDK import. See LibSaturn's tools/import_model.py and examples/world_lod3d_demo. The game smoke test still does not load this scene.

## Acceptance

CI generates two copies with identical inputs and checks the JSON/OBJ bytes (not binary .blend). Blender version is printed. It publishes the generated preview files as a CI artifact. Local execution and hardware qualification remain separate gates. Next: convert the greybox to an actual SDK mesh, verify axes with an asymmetric reference, load it in a minimal 3D Saturn scene and record Ymir/Mednafen evidence.
