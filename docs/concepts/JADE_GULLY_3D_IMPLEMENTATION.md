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

## Visual pass v2 — 22 November 2026

The previous render confirmed that the v1 scene was only a uniform checkerboard strip with tiny pine-like placeholders, nearly invisible loops, small suspended huts, threadlike water and vertical labels. The new committed source corrects the Blender **art blockout**:

- Hex loops and collectible-look rings now lie in the YZ traversal plane, facing the oblique panoramic camera; loops are enlarged and raised above terrain.
- Tropical eight-frond palms replace conical pine proxies. A large ancient broadleaf world tree anchors the Bamboo Heights village; its three raised hut decks are linked with segmented planks, posts and sagging ropes.
- Ten scenic checkerboard mesas break the ridge silhouette into plateaus. Two geometrically curved bamboo halfpipes cross the elevated section.
- Gully Current receives a wide water surface, foam banks, multi-curtain waterfalls and recognizable pools instead of a single colored line.
- The starting communications dish, springs, item monitors, additional rings and final emerald goal provide recognizable gameplay landmarks.
- Five readable, camera-facing region labels replace edge-on vertical names.
- All meshes are original fan-authoring geometry; existing source Kenney CC0 terrain textures stay packed in the Blender file. This is **not a verified playable Saturn stage**.

The pure-Python geometry library and regression tests are in `tools/jade_concept_geometry.py` and `tests/test_jade_concept_geometry.py`, while `tools/jade_concept_dressing.py` holds visual-only setpieces. The Blender workflow in `.github/workflows/jade-gully-concept.yml` checks these modules and renders actual images. **Visual acceptance remains open until we inspect the newly generated screenshots.**

## Mac — one command (pull + rebuild + open)

From the existing checkout, irrespective of its current branch:

```bash
cd ~/dev/sonic-xtreme-saturn && git fetch origin main && git show origin/main:scripts/review-jade-concept-mac.sh | bash
```

The remote-reviewed script performs `git pull --ff-only` on the Mac's current branch, fetches `origin/main`, creates an isolated detached worktree, builds the new Blender scene, and opens its isometric PNG. It does not move the current experimental branch.

When the GitHub Actions [Blender concept workflow](../../.github/workflows/jade-gully-concept.yml) renders successfully against the current `main`, it also publishes the editable scene and previews to [`assets/jade-gully/concept-v2/`](../../assets/jade-gully/concept-v2/). **The existence of this publication step is not proof that the job has completed or that the art passed visual review.**

## Mac — explicit detached worktree


```bash
cd ~/dev/sonic-xtreme-saturn
git fetch origin main
DEST="$HOME/dev/sonic-xtreme-concept-$(date +%s)"
git worktree add --detach "$DEST" origin/main
bash "$DEST/scripts/build-jade-concept-mac.sh"
open "$DEST/build/jade-gully-concept/jade-gully-concept-isometric.png"
```

This uses an isolated detached worktree. It does **not** switch, merge, reset, or alter the developer's current experimental branch. Open `$DEST/build/jade-gully-concept/jade_gully_act1_concept.blend` in Blender. The same command also renders isometric and top-down PNGs. The [GitHub Actions workflow](../../.github/workflows/jade-gully-concept.yml) runs the Blender generator in CI and saves the scene and previews as an artifact when successful. Each large landmass is named `sector_<id>_checker_landmass`; route meshes and line guides have `path_*` / `guide_*` prefixes; landmarks keep their map names. The source PNG is a reference alongside the editable scene, not a texture mapped over the entire ground. Terrain, rock, forest, roof, bamboo, bridge, river and path materials use the already committed **Kenney CC0 PNGs** in `assets/textures/jade-gully/`; source images are packed into the generated `.blend`. The color of rings and visual route guides remains authored.

## Intentional limits

This scene's world-scale mesh deliberately **exceeds the current single-stage 448-face Saturn budget**. It cannot be dropped into the existing runtime. The playable `adventure` layout and original qualification remain unchanged. First qualify sector streaming / segmentation, fixed-point collision, camera/gravity behavior for actual loops, collision for raised bamboo bridges, texel-density tiling, LOD and Ymir frame pacing *before* using it in a game build. Loops, paths, rings, waterfalls and checkpoints in the concept are **art-only**: geometry does not imply gameplay functionality. Screenshots are generated locally by the Mac script; neither a successful Blender render nor a unit-test pass verifies 30 displayed FPS on Saturn.
