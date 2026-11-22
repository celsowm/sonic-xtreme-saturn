# Jade Gully Act 1 — painting-faithful concept v4 (Blender 5.2)

**Status:** offline Blender art reconstruction of the approved painting
[`jade-gully-act1-concept.png`](jade-gully-act1-concept.png). Not Saturn
geometry, collision, gameplay or a performance claim.

## Why v4 exists

The user reviewed the v3 renders and the Saturn build as "much uglier than the
concept art". A side-by-side check found that v1–v3 did not follow the painting
at the contract level:

| | Painting | v1–v3 |
|---|---|---|
| Region labels | 1 ENTRY HILLS, 2 TREE VILLAGE, 3 SKY BRIDGES, 4 HEX LOOP, 5 CANYON BASIN | Sonic's Base, Jade Ridges, Bamboo Heights, Gully Current, Jade Summit. These names do not appear in the image, although the v1–v3 docs said they did |
| Layout | START bottom-left; climb to the tree village; cross floating islands over a cloud sea; one massive hex loop; canyon basin; GOAL top-right | One continuous +Y strip |
| Terrain | Green-checker grass caps on ochre/brown checker columns rising out of jungle and clouds | Dark sloped landmass with scattered squares |
| Hex loop | One huge tube: green checker shell, blue running surface, rings inside | Four small orange C shapes |
| Sky | Deep blue sky, clouds, snowy mountain range | Flat grey-blue |

## What v4 changes

- `assets/levels/jade_gully_concept_v4.json` (schema 4) uses the painting's five
  labels, in order, with the painted notes. The layout is in painting space:
  +X is right of the image and +Y is away from the viewer.
  `tools/validate_jade_concept_v4.py` rejects the old invented names. It also
  rejects a main route that does not visit regions 1→5 in order, alternates
  that do not rejoin the main route, and a loss of the painted signatures
  (at least 8 waterfalls, 5 huts and 8 floating islands, plus a massive hex).
- `tools/jade_concept_v4_geometry.py` provides pure-Python generators for
  checker columns, floating islands with tapered undersides, the hex tube, the
  grass arch, route curves and the mountain range. They are tested in
  `tests/test_jade_concept_v4.py`, which also checks face orientation.
- `tools/create_jade_gully_concept_v4.py` builds the scene. All materials are
  original and procedural: 3D checker, noise-mottled foliage and striped
  falls. No Kenney, Sega or painting pixels are used as textures. The painting
  is loaded only to build the review image.

### Matching the painting's framing

The painting is an illustrated map. It is seen steeply from above, yet still
shows a horizon. The reference camera `JG4_Painting_Reference` (location
`(50,-156,310)`, target `(14,148,14)`, 40 mm) was fitted by least squares to
seven painted landmark positions: START, GOAL, hex centre, main hut, arch,
sky-bridge island and foreground island. Pitch was constrained to ≤44° so
the backdrop can be staged.

Each region was then moved by its back-projected offset onto the painted
positions:

| Region | dx | dy |
|---|---:|---:|
| Entry Hills | +14 | −3 |
| Tree Village | −29 | +3 |
| Sky Bridges | −16 | −2 |
| Hex Loop | −7 | +12 |
| Canyon Basin | +34 | −4 |

The horizon is staged like the painting's: a camera-facing sky panel, a low
snow-capped range and far jungle hills. The hex loop is tilted 60% of the way
toward the reference camera, so it reads face-on as painted while its blue
interior stays visible. Route points inside the loop are tilted with it.

### Measured colour-family distance (review aid, not a quality score)

`concept-v4-contract.json` records the share of green, blue, ochre/brown and
white pixels in the painting and in `jade-gully-v4-map.png`, plus their L1
distance. Lower is closer. It ignores layout, and the painting's title and
legend boxes are counted too.

| Iteration (Blender 5.2.2, same camera/samples) | L1 distance |
|---|---:|
| First v4 render (wide camera) | 0.591 |
| Fitted camera + regional offsets | 0.486 |
| Darker painted palette, jungle foreground, tilted hex, pillars | 0.378 |
| Leafy foliage, striped falls, bevelled lips | 0.348 |
| Sparser cloud sea over a deep-blue void | 0.323 |
| Painted details pass: hills, spiral, canyon, items, title/labels/legend | 0.253 |
| Soft billowing clouds (whiter than painted; see below) | 0.269 |

The last row is slightly worse on this metric but closer by eye. The
billowing clouds count as more white (0.112 vs the painting's 0.035), and
the painting is bluer overall (0.454 vs 0.320). Its cloud banks are painted
with blue shadows, which the render does not reproduce.

### Painted details pass (closing the first review's gaps)

| Gap in the first v4 render | What now matches the painting |
|---|---|
| Entry Hills terraces were flat boxes | Seven rolling grass hills (`hills`, cosine profile) and two grass ramps joining the terrace levels (`slopes`) |
| Village had few walkways, no structure around the trunk | A spiral stair wrapped 1.25 turns around the trunk to a ring deck with rope rails (`spiral`), plus two more bridges/stairs between huts |
| Canyon had few channels and platforms | Three more checker columns, four wooden stilt decks with crates (`platforms`) and four raised water channels feeding the falls (`channels`) |
| Cloud banks were opaque blobs | Clouds fade out at their silhouettes (Layer Weight → Transparent mix), have a billowy bump and carry cumulus puffs on top of each bank |
| No item monitors, stars, title or legend | Seven item monitors and five bonus stars (original designs). The title, numbered region labels with the painted notes, START/GOAL tags and the map legend sit at the label positions measured on the painting (`label_uv`, `overlay`). They are rendered only in the `map` shot; the `clean` shot omits them |
| Hex close-up camera too close; rings cut the running surface | Camera placed along the tilted hex's face normal at 3.4× its radius; the ring trail now follows the hexagon's apothem, not its corner radius |

The validator checks every new section: region membership, level channels,
a spiral outside the trunk, and 0..1 overlay coordinates. `tests/test_jade_concept_v4.py` covers
the new generators (`grass_mound`, `slope`, `spiral_steps`, `star_prism`),
including face orientation.

## Build

```
bash scripts/build-jade-concept-v4-mac.sh            # tests + 10 images + .blend
JADE_V4_QUICK=1 bash scripts/build-jade-concept-v4-mac.sh   # map + compare only
```

Outputs go to `build/jade-gully-concept-v4/`:

- `jade-gully-v4-compare.png`: painting and render side by side.
- `jade-gully-v4-map.png` and `jade-gully-v4-clean.png`: the painting framing. `map` has the routes, title, labels and legend; `clean` has none of them.
- `jade-gully-v4-top.png`: overhead view.
- Five region close-ups.
- `jade_gully_act1_concept_v4.blend`.
- `concept-v4-contract.json`.

The full set took 4 min 42 s on the project Mac (Blender 5.2.2, CPU Cycles, 48 samples; measured 2026-11-22 after the details pass). The quick mode took 1 min 39 s. The scene has 449 mesh objects and 314,427 polygons (offline art, not a Saturn budget).

## Still different from the painting

These are deliberate omissions or limits of the procedural style. None is a
missing feature from the first review:

- No characters. They are not drawn: the painting's characters are not
  project-original art.
- No game logo. The title is plain text in the project's own wording.
- The painting's brushwork, atmospheric haze and blue cloud shading are not
  reproduced. The render is clean low-poly with procedural checker.

## Next steps

1. **F2 — Saturn textures.** Bake the v4 palette into original 64×64
   indexed8 textures (grass checker, cliff checker, water tile, thatch, plank,
   cloud), replacing the Kenney stand-ins. Size them against the VDP1 VRAM
   headroom recorded in the roadmap.
2. **F3 — Entry Hills on Saturn only.** This is the vertical slice; the other
   regions stay Blender-only until acceptance gates pass. Add a VDP2 sky and
   mountain backdrop, checker terraces, pools, the arch and palms with LOD,
   and accept it on Ymir screenshots plus the existing p95/late-swap gates.
