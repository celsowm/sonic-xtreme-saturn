# Jade Gully — Act 1: concept map (visual target)

**Status:** fan-made **concept artwork**, not the recovered original level mesh, a build of the leaked game, or a playable stage. This document captures the approved artistic direction. Keep the original Saturn/718 references clearly separate from proposed expansions.

## Proposed layout

The new concept uses a longer, continuous **3D action-adventure** route, with optional side routes rather than a 20-second racetrack. The image carries five numbered areas:

1. **Entry Hills** — rolling terrain, water pools, rings, springs, an open starting clearing.
2. **Tree Village** — tall tree platforms, huts and elevated bridges; alternate vertical paths and hidden rings. *Interpretive/new design*, not verified as part of the Saturn Jade Gully level.
3. **Sky Bridges** — narrow suspended platforms and routes through clouds. *Concept expansion*, not a claim about documented original geometry.
4. **Hex Loop** — large hexagonal corkscrew/loop with ring paths and changing camera orientation. *Inspired by documented Sonic X-treme footage*; the pictured scale and position are new design.
5. **Canyon Basin / Goal** — multi-level checkerboard canyon, streams, cascades, walkways and final climb, followed by a distinct goal space.

The intended gameplay is **exploration + speed + platforming**, with a readable main route, optional risk/reward shortcuts, increasing elevation, and room for the fisheye camera's gravity transitions. No fixed duration, world dimensions or measured speed are inferred from this painting. Segment lengths, collision geometry, LOD and target completion time must be specified and tested as game data.

## Historical grounding (not a claim of 1:1 replication)

- [Secrets of Sonic Team — Jade Gully Zone](https://sost.emulationzone.org/sonic_xtreme/jade_gully/index.htm): images from the TGS footage show checkerboard ledges, a hexagonal loop, narrow passages, changes of gravity and a fisheye view.
- [Secrets of Sonic Team — 718 tech demo](https://sost.emulationzone.org/sonic_xtreme_718/techdemo/index.htm): a **different early build**, with green hills, water, scattered rings and visible geometry pop-in.
- [The Models Resource — Jade Gully extracted model](https://models.spriters-resource.com/saturn/sonicxtreme/asset/467305/): 3D mesh and nine PNG textures; use as a technical reference only after actual inspection, not evidence that the concept map follows its shape.
- [Project SXU 2020 Jade Gully Act 1](https://www.moddb.com/games/sonic-x-treme-unity/downloads/project-sxu-2020-jade-gully-demo): a **separate unofficial Unity remake**, not proof of the Saturn layout.

## Asset and implementation status

The full-resolution generated concept PNG belongs at **`docs/concepts/jade-gully-act1-concept.png`**. The PNG is *not source geometry*, is not an asset derived automatically from Sega's extracted mesh, and must not be used for collision or for texture generation. Use the included `scripts/publish-jade-gully-map-mac.sh` to publish the image from the Mac's Downloads folder to `main` without modifying the developer's working branch.

Do **not** merge the experimental [Jade Gully PR #2](https://github.com/celsowm/sonic-xtreme-saturn/pull/2) as part of concept-art publication: performance and visual acceptance gates remain open. The `main` baseline and build reproducibility should be preserved.
