# Jade Gully — Action Adventure Act 1 (branching map prototype)

**Objective:** build a coherent Sonic Adventure-style action stage for stock Saturn, not an isolated road floating in a sky. A 3–5-minute first act will alternate moments of speed, exploration, traversal, platforming and short combat with clear visual landmarks and risk/reward choices. This is an original level concept; do not copy the geometry of Emerald Coast, Windy Valley or leaked Sonic X-treme assets.

## Plan view — routes and hubs

```text
                 [OVERLOOK / tutorial]
                           |
                 DESCENT — fast run
                           |
                   [FOREST CROSSROADS]---------------+
                   /        |                       |
          CANOPY RIDGE   EMERALD RUN             RIVER BASIN
          (upper risk)  (speed line)         (wide / exploration)
                   \        |                       /
                    \       |         [optional rings / enemy]
                     [WATERFALL MEADOW + wooden bridge]
                           |
                    [TEMPLE CLEARING] ------------+
                           |                      |
                       MAIN RAMP              RUIN STEPS
                       (quick)             (slow / reward)
                           |                      |
                           +------[FINAL RUN]-----+
                                      |
                                    [GOAL]
```

Route coordinates, radius/area constraints, collision-surface metadata, props, entities, and selection limits are **executable data** in [`assets/levels/jade_gully_adventure_v1.json`](../assets/levels/jade_gully_adventure_v1.json). Coordinate system: metres, Blender RH Z-up. The stage has two open explorable courtyards (river basin and temple court) linked to four connected traversable ribbons: `main`, `upper`, `river`, and `ruins`. They share exact junction points and preserve the first stretch of the legacy main route for deterministic movement regression.

## Gameplay rhythm

| Sector | Stage idea | Primary activity | Alternative/reward | Camera requirement |
| --- | --- | --- | --- | --- |
| Overlook | Open grassy starting terrace; can see waterfall far ahead | Learn acceleration, jumping | First rings | Behind Sonic with lookahead |
| Forest | Broad fork with vegetation/rock walls | Momentum through a bend | Canopy ridge with shortcut | Frame two visible exits |
| River basin | Wide lower clearing, streams, boulders | Exploration/collecting rings | Slower safe route to bridge | Wide, minimal occlusion |
| Waterfall | Elevated bridge and pool | Precision jump/spring | Choose safe crossing or fast jump | Reveal landing before jump |
| Temple | Ruined stone columns and raised steps | Platforming and short enemy encounter | Higher ring cache | Rail/soft follow, no pop |
| Goal | Downhill release and completion gate | Final speed burst | Optional side reward | Stable view of exit |

The `ring`, `spring`, `enemy`, `checkpoint`, `camera_anchor`, `goal` entities are **markers only** until P4 gameplay logic exists. The authored meshes are **not** automatically solid walls or obstacles. Never claim a completed playable action game solely because marker instances or bridges render.

## Real 3D model library

The project now tracks **nine low-poly Kenney CC0 GLBs** under [`assets/kenney`](../assets/kenney/ATTRIBUTION.md). These were selected from the Nature Kit and Castle Kit for palm/foliage silhouettes, cliffs, rocks, a wooden bridge, grassy platform and temple pillars/doorway. Attribution and per-file Git blob hashes are documented. Quaternius [Ultimate Nature Pack](https://quaternius.com/packs/ultimatenature.html) and [Ultimate Modular Ruins](https://quaternius.com/packs/ultimatemodularruins.html) are also CC0 research options **but are not yet vendored**. No rip of Sega stage geometry, textures, audio, objects or code.

`tools/create_jade_gully_adventure.py` is a **separate Blender authoring builder**. It imports selected GLBs, flattens glTF transforms, decimates each mesh to its declared triangle cap, and assigns a temporary palette material. Separately, authored ribbon surfaces produce collision surfaces; low-poly cliff skirts and imported scenery are render-only. No general GLB runtime importer is added to LibSaturn. The primary build continues to use `tools/create_jade_gully.py` by default.

The first artifact is deliberately a small, bounded scenic geometry proof with walkable wider areas: four traversable routes, 22 top segments (44 tris), 44 cliff-side quads (88 tris), **two broad collision-enabled clearing pads** (20 tris including skirts), max 80 imported prop triangles plus 2 water triangles — **234 planned render triangles** within the 256-face exporter limit. Runtime adds the Sonic LOD (159 faces) and markers separately. Actual exported counts must be checked by Blender and CI; this number is an authoring budget, **not an observed emulator result**.

## Performance and quality gates

Stock NTSC Saturn, 320×224, **30 displayed FPS target** with independent **60 Hz deterministic physics**. In the post-fix Adventure smoke evidence (game `042c228`, Ymir evidence `668b5a0`), four focused cases passed at 30 scene submissions/s and 34 ms p95, with zero draw timeouts, dropped simulation time or late swaps. The classic 11-case suite also passed earlier but is not the Adventure branch qualification. Display cadence was not independently measured, and the game is still visibly a sparse greybox. The initial adventure candidate must be qualified separately:

1. Validate manifest, connectivity, CC0 files and face budgets with host Python tests.
2. Blender export twice, compare deterministic scene/render/collision outputs and bake stage headers.
3. Build SH-2, check app/texture memory/command budgets and launch fresh Ymir probe with the selected `adventure` layout.
4. Inspect at least the idle overlook, forest fork, upper-route sightline, waterfall and temple screenshots; verify no player occlusion or visible gaps.
5. Measure all phase timings and XFP1 p95, animation state changes, frame drops, 30 scene submissions/s target and deterministic HUD/physics. An isolated pass is only a smoke test; full 11-case routes + new branching traversals follow.
6. Then run Mednafen and physical Saturn; qualify the actual on-screen 30 FPS, not just the VDP1 submission counter.

**Important:** avoid loading every asset at full detail. Later production work needs sector visibility/streaming, texture atlases, distance LOD, environment collision authored separately, actual loops, spring/ring game logic, and physical console testing. No performance or animation claims before those validations.

## Build separately on the Mac

```sh
cd ~/dev/sonic-xtreme-saturn && git pull --ff-only
bash scripts/qualify-jade-adventure-mac.sh
```

This uses `XTREME_STAGE_LAYOUT=adventure`, generates `build/jade-gully-adventure`, compiles using the same tracked Sonic R LOD, runs a focused Ymir smoke subset and publishes the usual evidence ZIP and screenshots to `ymir-evidence`. The default `XTREME_STAGE_LAYOUT=classic` retains the previously qualified stage until this alternative passes.
