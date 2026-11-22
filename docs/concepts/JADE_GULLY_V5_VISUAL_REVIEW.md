# Jade Gully — V5 art-direction review after the 22 Nov 2026 side-by-side

**Status: V4 rejected on visual fidelity.** Reference: the user's 11:34 Mac comparison,
`jade-gully-v4-compare.png`. Left: approved painted fan map. Right: Blender V4
render. This is an **offline art-only** reconstruction, NOT the Saturn game, and
the current V4 branch must not be merged to `main` as visually accepted.

V4 genuinely corrects the 5-region contract (ENTRY HILLS, TREE VILLAGE,
SKY BRIDGES, HEX LOOP, CANYON BASIN), route order, landmarks and camera
fitting. Keep its manifest, validation, editable `.blend` and reproducible
preview workflow. The problem is **silhouette, terrain language and density**,
not missing region names or the number of mesh polygons.

## Image-by-image critique

| Reference painting (left) | V4 preview (right) | V5 target |
|---|---|---|
| Broad, winding entry hills connected to multiple jungle-backed ledges | A few round-edged rectangular checker slabs, highly legible as separate boxes | Contiguous, irregular running hills, distinct slopes and undercuts, 2–3 visible elevation layers |
| Village embedded inside a giant broad-crowned tropical tree, bridges disappearing into foliage | Small pale huts atop disconnected thin trunks; crowns resemble sphere clusters | One dominant branching trunk with *readable* huts at 2–3 heights, decks integrated into foliage, believable supporting beams and ropes |
| Multiple long, stepped sky bridge traversals over deep ravines | Thin route string spanning small islands, regular checker blocks | Vary bridge widths, zigzags, length, suspended supports and island shapes; preserve navigable exits at both ends |
| Huge signature hex loop *integrated* into ridge scenery | Free-standing green hex tube on a small platform; blue interior reads as a detached insert | Blue inner track flowing into the preceding and following running surface; ramp and support landforms must touch the loop; foreground/background overlap with trees/ridge |
| Tall canyon *landscape*, water channels, lush cliffs, foreground waterfalls | Flat upright brown/green walls with isolated rectangular shelves | Staggered canyon ledges and recessed shelves, waterfall sources and lower basins at visibly different heights, vegetation at cliff transitions |
| Deep atmospheric perspective, saturated sky, mountains, foreground jungle | Centre occupied by large opaque white cloud blobs | Blue-shadowed mist *between* cliffs, less foreground cloud occlusion, clear near/mid/far depth hierarchy |
| Dense small-scale details and varied visual rhythm | Repeated checker squares, evenly scattered palms, generic cones/icospheres | Cluster vegetation by biome and scale, break tiling frequency, foreground framing palms, few strong hero props |

**Do not claim fidelity from colour-share L1 alone.** The existing V4 report
explicitly warns that it does not evaluate composition or perceptual similarity.
Nor is 314k offline scene polygons a quality metric or a Saturn budget.

## Implementation order (one visible change at a time)

### Gate A — terrain composition, **before** decorating

- Refactor `build_ground` and `tools/jade_concept_v4_geometry.py`.
  Replace several `rounded_rect` terrace outlines with authored irregular
  polygon boundaries, but retain current stable IDs and bounds. Keep a
  continuous walking narrative: entry ledges -> village -> stepped bridges ->
  loop -> canyon.
- Add overlapping plateau *strata* and taper exposed walls instead of
  vertical box faces of uniform depth. Vary checker size and rock/grass edge
  thickness by region. The *close-up* must not resemble a pile of boxes.
- Explicitly design near/mid/far silhouettes in the **same reference camera**.
  A top-down map does not replace this test.
- Validate no visual joins break route continuity; this is a **visual test**,
  not a claim of Saturn collision.

**Accept only if:** V5 map *without vegetation, clouds, labels, or overlay*
already reads as one large multi-level Sonic world rather than floating slabs.

### Gate B — village as coherent architecture

- Refactor `build_village`, `build_walkways`, and village placements in
  `assets/levels/jade_gully_concept_v4.json`.
- Model a tapered *branching* trunk with buttress roots, smaller tree limbs
  supporting decks, huts with readable door/window openings, roofs scaled to
  their platforms, and 2–3 distinct deck levels.
- Use broad layered foliage clumps **behind and around** structures; avoid
  covering the 3 main huts or turning the frame into floating straw umbrellas.
- Build a cross-section view demonstrating an uninterrupted path from the
  lower deck to the upper deck via stairs, spiral or supported bridges.

**Accept only if:** viewers identify a village built *in* a giant tree,
without needing the `TREE VILLAGE` overlay.

### Gate C — loop and bridges, clear route topology

- Refactor `build_hex`, `build_walkways`, `build_pillars`.
  The giant six-sided loop must connect visually to an entrance ramp and
  an exit landform. Do not change the authored route's origin or end without
  updating `validate_jade_concept_v4.py` and its tests.
- Provide a clean hero close-up of the blue running face, surrounding green
  checker ridge and entry/exit. The loop should not look like a floating sign.
- Sky islands need distinct silhouettes and layers, not clones of the same
  beveled prism. Route segments remain distinct enough to evaluate traversal.

**Accept only if:** the primary route can be followed by eye
START -> tree -> bridges -> loop -> canyon -> GOAL.

### Gate D — canyon, water, atmosphere, props

- Refactor `build_canyon_details`, `build_ground`, `build_vegetation`,
  `cloud_material`, `build_backdrop`. Add ledges *inside* the canyon wall,
  traceable sources for waterfalls and several visible elevation tiers.
- Clouds should have a blue/lilac shadow side and semi-transparent boundaries;
  keep openings showing the deep blue void and terrain, not a white foam field.
- Distribute palms, bushes, hanging vines and distant jungle in **clusters**,
  with variation in size, asymmetry and depth. A palm can be 2D/billboard in
  eventual Saturn LOD; don't burn polygons unnecessarily on far scenery.
- Blend checker cliff faces with grass caps, green edge growth and rocks. Use
  restrained waterfalls rather than long featureless cyan rectangles.
- Use *licensed/provenance-tracked* art only. Historic Sega screenshots,
  1996 Jade Gully footage and extracted models/textures are visual reference,
  not permission to commit copyrighted rips.

**Accept only if:** the canyon reads as a deep navigable place with basins and
bridges and the clouds no longer dominate the composition.

## Deliverables and evidence (mandatory)

1. Render the current approved painting and the new panorama at the **same
   dimensions and locked V4 reference camera**. Store `compare.png`.
2. Export `clean.png` with `MAP_OVERLAY` and `MAP_HUD` hidden. **No region
   label cards in the art acceptance shot.** The viewer must recognize all
   five zones from geometry alone.
3. Render **five close-ups** (entry, tree village, sky bridges, hex loop,
   canyon basin), plus top view. Do not present a map-only beauty shot as proof.
4. Include a short *artist review table*, with each of the five gates marked
   pass/revise and a specific visual observation. Pixel colour distribution
   and object counts are diagnostic only.
5. Commit the source `*.py`, manifest edits and tests; commit `.blend` and
   PNGs only via the existing artifact/publishing workflow when checks pass.
   Do not claim any render or Blender validation unless it actually ran.
6. Keep V4 review isolated from the Saturn runtime. **Stock Saturn:** continue
   to target 30 displayed FPS, use independent collision/LOD/streaming and
   qualify incremental **Entry Hills first** in Ymir and Mednafen. Never
   attempt to export the full offline 314k-polygon scene as one stage.

## What NOT to do

- Don't fix this by adding more floating palm trees, clouds, labels,
  golden route arrows, debug badges or higher polygon counts.
- Don't silently swap the approved five-region layout back to the older
  `SONIC'S BASE / JADE RIDGES / BAMBOO HEIGHTS` concept.
- Don't merge a visual branch to `main` based on passing Python tests,
  a lower colour-family L1 number or a successful Blender render alone.
- Don't delete the current V4 generator and evidence: keep before/after
  comparison reproducible.
