# Jade Gully Act 1 — concept art → Blender scene

**Source:** [Approved 5-region concept art](jade-gully-act1-concept.png).
This is an original **artist-editable offline reconstruction**, not the original cancelled game's geometry and not a Saturn-exported stage.

## Visual contract

The image's actual labeled regions are followed left-to-right (along +Y in Blender):

| Sector (art) | Blender Y (metres) | Authored landmarks and connections |
| --- | ---: | --- |
| Sonic's Base | 0–100 | Starting clearing, dome, watchtower, palms and introductory rings |
| Jade Ridges | 100–205 | Steep checkerboard banks, large hexagonal corkscrew silhouette, lower loop, risk shortcut |
| Bamboo Heights | 205–315 | Three elevated huts on giant trees, suspended bridges, alternative canopy routes |
| Gully Current | 315–415 | River-bottom traversal, two stepped falls, canyon banks, lower exploration branch |
| Jade Summit / Exit | 415–515 | Final ascent, paired hexagonal loops, goal banner, high-risk ridge shortcut |

Authored files:

- `assets/levels/jade_gully_concept_v1.json`: dimensions, full route topology, branches, landmark coordinates, five zone assignments.
- `tools/validate_jade_concept.py`: deterministic validation of topology, bounds, zone order and signature landmarks.
- `tools/create_jade_gully_concept.py`: original Blender geometry for connected terrain, checker cliff skirts, six traversing visual path strips, forest, tree village, bridges, waterfall planes, loop structures, rings and panoramic cameras.
- `tests/test_jade_concept.py`: dependency-free checks used before Blender.
- `scripts/build-jade-concept-mac.sh`: Mac one-command build, producing `.blend`, isometric PNG and plan-view PNG under `build/jade-gully-concept/`.

## Mac

```bash
cd ~/dev/sonic-xtreme-saturn
git fetch origin main
DEST="build/jade-concept-$(date +%s)"
git worktree add --detach "$DEST" origin/main
bash "$DEST/scripts/build-jade-concept-mac.sh"
```

This uses an isolated detached worktree. It does **not** switch, merge, reset, or alter the developer's current experimental branch. Open `$DEST/build/jade-gully-concept/jade_gully_act1_concept.blend` in Blender. The same command also renders isometric and top-down PNGs. The [GitHub Actions workflow](../../.github/workflows/jade-gully-concept.yml) runs the Blender generator in CI and saves the scene and previews as an artifact when successful. Each large landmass is named `sector_<id>_checker_landmass`; route meshes and line guides have `path_*` / `guide_*` prefixes; landmarks keep their map names. The source PNG is a reference alongside the editable scene, not a texture mapped over the entire ground.

## Intentional limits

This scene's world-scale mesh deliberately **exceeds the current single-stage 448-face Saturn budget**. It cannot be dropped into the existing runtime. The playable `adventure` layout and original qualification remain unchanged. First qualify sector streaming / segmentation, fixed-point collision, camera/gravity behavior for actual loops, collision for raised bamboo bridges, texel-density tiling, LOD and Ymir frame pacing *before* using it in a game build. Loops, paths, rings, waterfalls and checkpoints in the concept are **art-only**: geometry does not imply gameplay functionality. Screenshots are generated locally by the Mac script; neither a successful Blender render nor a unit-test pass verifies 30 displayed FPS on Saturn.
