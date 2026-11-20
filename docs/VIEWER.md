# Native greybox viewer

Inspected SDK revision: af86f8518f0d014f2a752ca43035d2278bc9bf8f. Uses the installed LibSaturn package, sat_camera3d_init/update and sat_scene_init/begin/submit_quad/flush. The SDK owns all projection, clipping, painter sorting and VDP1 command emission. No alternate renderer.

The deliberately narrow, game-side bake_greybox.py adapter converts untextured toolkit OBJ and JSON to immutable C tables. Right-handed Blender (X,Y,Z) becomes LibSaturn (X,Z,-Y), then Q16.16, bounded +/-256 m. Source OBJ triangle winding is reversed for cross(D-A,B-A), with triangles encoded A,B,C,C. Quads are triangulated to avoid non-planar face issues. No UVs/textures or mesh optimizer; the full textured asset pipeline should use the existing SDK importer, not extend this viewer adapter into another general-purpose importer. Collision OBJ is now baked separately for the player ground probe. See [CONTROLLER.md](CONTROLLER.md).

Colors distinguish main path, upper path, ruins and marker kinds. Two crossed solid diamonds per marker. Single canonical scene pass; no Z-buffer and crossing route polygons may show painter artifacts. Bounded scene storage: stage triangles plus two faces per entity, max 384. The camera is a debug pan, frame-driven, not gameplay or a physics tick. No stock hardware performance measured.

## Gates
- python -m unittest discover -s tests
- Generate the authoring outputs twice; bake both and compare headers.
- Host syntax compilation against pinned SDK headers (CI).
- Build SH-2 ELF + disc via installed SDK.
- Open in Ymir and Mednafen; screenshot start/overview/end; verify path colors, axes, markers, no clipping failures. Record xtreme_error, xtreme_frames, xtreme_world_commands from map/WRAM if available. Counter is completed submissions, not displayed FPS.
- Confirm on physical Saturn before performance claims.

Next: qualify viewer and controller on target, then implement swept collision and advanced movement. For scenery expansion, use LibSaturn's HLOD example and texture importer.
