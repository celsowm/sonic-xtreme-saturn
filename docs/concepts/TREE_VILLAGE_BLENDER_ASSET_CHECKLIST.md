# Tree Village — Blender production checklist (Saturn hybrid 2D/3D)

Status: **authoring plan only**. This document specifies models to create; no new GLB, blend, sprite, physics, sectors or game render code is claimed complete. Builds on [approved Act 1 concept](JADE_GULLY_ACT1_MAP.md), the Blender toolkit, and the existing authoring generator. The tree village is a **fan-designed expansion** inspired by Sonic X-treme, not a reconstruction of a historically verified Saturn village.

## 0. Non-negotiable constraints from this repository

- Blender authoring: **1 Blender unit = 1 metre**, right-handed **Z-up**. Existing exporter/baker converts to Saturn Y-up; do not pre-rotate source geometry. Apply transforms before export. Use separate `render` and `collision` meshes.
- **Current single-stage exporter:** `tools/bake_greybox.py` limits **448 render faces**, **2,048 vertices**, **64 entities** and local coordinates to **±256m per component**. The present Adventure manifest estimates **442/448 render faces** with **232 imported-prop triangles**, so there is **no room to add this kit to the existing full scene** without replacing content or implementing sectorization. The old budgets proposed for a 300-triangle trunk + 200-triangle houses are **NOT acceptable** as simultaneously resident scene assets.
- Separate sector exports/local coordinate origins **must be implemented before a ~1.45-km Act 1**. `XTREME_STAGE_LAYOUT=adventure` currently exports a **single** scene. Blender collections alone do not enable runtime streaming, and a single OBJ from coordinates >256m fails the current baker.
- Maintain *measured* Saturn goals: ~30 **displayed** FPS target, fixed 60 Hz physics, 320×224 NTSC. The 448-face cap is a build ceiling, **not a performance target**. A new near-camera render budget of **120–180 stage submissions** is an *initial profiling hypothesis*, not an acceptance result; actor/rings add more.
- Reuse existing Kenney CC0 `assets/kenney/nature-kit/tree-palm.glb`, `tree-palmbend.glb`, `bridge-wood.glb`, `plant-bush.glb` and other curated GLBs as authoring inputs. Existing `assets/textures/jade-gully` has **8 Kenney indexed8 64×64 source textures**. It has **no dedicated checkerboard or village atlas**.
- `spring` entities exist in `assets/levels/jade_gully_adventure_v1.json` but currently are **markers only** (no bounce interaction). 16-frame textured rings are in experimental PR #2, not in main. Static cross-plane foliage is feasible in Blender, but **camera-facing billboards are NOT implemented for general scenery**; do not call a static plane a functional billboard.
- Prioritize shapes from the concept image, but clearly distinguish original Sega media from new fan art. New publicly committed materials should be original or redistributable CC0/compatible; keep attribution and source hashes.

## 1. Asset card — dimensions and first-pass budgets

**Polygon unit:** *triangles at full visible LOD (LOD0)*, unless marked `quads`; one quad ordinarily requires two render triangles in the OBJ-to-C baker. Suggested dimensions below are design estimates to validate with Sonic's actual jump and collision tests, not recovered Sega specifications. All sizes in metres.

| ID (Blender object) | Purpose / suggested dimensions (W×D×H) | LOD0 triangles | LOD1 | LOD2 | Collision | First use |
|---|---|---:|---|---|---|---|
| `jg_tree_trunk_A` | central structural trunk, ~6×6×19; 6–8 sided, tapered; painted bark | **24–40** | 12–20 | distant silhouette, 2 crossed quads | separate 6–8 sided blocking hull if reachable | Tree Village landmark |
| `jg_branch_walk_A` | traversable main limb, ~3×9×1, low-poly tapered prism | 8–14 | 4–8 | omit | flat/sloped 2–4 triangle top collision | primary upper route |
| `jg_platform_round_S` | stop/jump pad, Ø4.5×0.5 | 6–10 | 4–6 | omit | 4–6 triangle top collision | entry terrace |
| `jg_platform_round_M` | branch stop, Ø7×0.6 | 8–12 | 4–8 | omit | 6–8 triangle top collision | bridge junction |
| `jg_platform_round_L` | village square, Ø11×0.8 | 12–18 | 6–10 | omit | 6–10 triangle top collision | alternate hub |
| `jg_bridge_short_A` | playable bridge, 3.5×10×0.3; rope/handrails as sprites | 8–12 | 4–8 | far silhouette | one sloped rectangular top (2 triangles) | required junction |
| `jg_bridge_long_A` | playable bridge, 3.5×18×0.3 | 10–16 | 6–10 | far silhouette | segmented 2–4 triangle top | shortcut |
| `jg_ramp_wood_A` | wide walkable ascent, 4×9×2 rise | 6–10 | 4–6 | omit | 2 triangles + landing | route ascent |
| `jg_house_playable_A` | **exterior only**, 5×5×4.5, cuboid + simple roof | **14–24** | 8–12 | textured façade, 1 quad | porch / doorway / blocker only; no interior | landmark at village hub |
| `jg_house_facade_A` | decorative house face, ~4×0.15×3.5 | 2–4 | 2 | omit | none | distant houses on trunks |
| `jg_house_half3d_A` | shallow decorative house, ~4×1.5×3.5 | 8–12 | one quad | omit | none | middle-distance branches |
| `jg_palm_close_A` | reuse + decimate Kenney source, ~3×3×6.5 | 12–24 | 2 crossed quads | one quad or omit | normally none | opening & village clearing |
| `jg_palm_xplane_A` | 2 crossed textured planes, 3×3×6.5 | **2 quads = 4 tris** | one quad | omit | none | near/mid decoration |
| `jg_foliage_x_A` | bush/fern/canopy cluster, ~2.5×2.5×2 | 2 quads = 4 tris | one quad | omit | none | hides seams/repetition |
| `jg_spring_red_A` | visible spring, ~1.8×1.8×0.6, simple box + red top | 6–10 | 2–4 | omit | separate contact **trigger**, impulse logic not yet implemented | mandatory progression |
| `jg_checkpoint_A` | checkpoint silhouette, ~1.3×0.5×2.7 | 4–8 | 2 | omit | trigger only | village exit |
| `jg_rope_banner_A` | ambient hanging detail, 1–3m long textured strip | 1 quad = 2 tris | omit | omit | none | bridge edge |

**Geometry budget rules:** avoid modeled nails, planks, branches, window frames, rope twists, leaves, hut interiors, thickness of far decorative faces. Paint those on the texture. Thin crossed planes must be tested for both sides/backface culling; if needed, use controlled two-sided geometry and account for its extra triangles.

## 2. UV / texture production card

- [ ] **`checker-ground-64.png`**: original 64×64 checkerboard (dark moss green + tan/earth), tile repeat in Blender; runtime tiling needs actual support, otherwise use subdivided patches. Do not rip Sega texture and claim CC0.
- [ ] **`village-wood-64.png`**: 64×64 boards + bark/tan accents; atlas packing must align with the *real* VDP1 UV/export behavior.
- [ ] **`village-hut-64.png`**: shingled roof, door and window painted, no geometric windows.
- [ ] **`foliage-palms-64.png`**: original/CC0 image with transparent background; verify **index-0** transparent palette behavior in real Ymir screenshots. For static cross-planes, orient and test both back and side views.
- [ ] **`spring-red-64.png`**: red top with clear arrow/impact zone; collision and bounce behavior remain separate gameplay tasks.
- [ ] Record each source URL/license, SHA-256 and conversion dimensions; verify **actual** VRAM and CRAM occupancy against existing stage textures (8×64×64 indexed8 = 32KiB), ring frames from PR #2 (16×32×32 = 16KiB) and actor textures. Do not allocate new CRAM banks by assumption.

## 3. Tree Village blockout — player navigation (proposed)

A practical *single sector* test scene may be about **50×70m** in Blender-local space. This is a test cell, **not** the total stage length. Place Sonic, platforms and the camera before decorative details.

1. **Arrival / lower clearing:** one 10m-diameter walkable open patch, one trunk (center), and a readable wide approach, with safe landing after a sprint.
2. **Primary route A:** lower platform (diameter 7m) at **Z=4–5m** `→` bridge 3.5m wide, 10m long `→` second platform at **Z=5–6m** `→` exit ramp.
3. **Alternative elevated route B:** 4.5m platform at **Z≈8m**, spring at reachable takeoff, 18m bridge to a high hut balcony; route rejoins path A. **Verify spring jump velocity and reachable gap in actual gameplay**; these are placeholder heights.
4. **Scenic dressing:** one low-poly playable hut by a junction, **four to six non-collidable façade huts** on other branches, **four or more cross-plane palms** with varied rotation and silhouette.
5. **Safety:** every route has an intentional safe landing, no invisible blocking house walls, stable camera near trunk, no collision assigned to visual-only banners, palms, façades or distant huts. Confirm collisions while approaching from both directions.

Proposed first-cell **render-mesh** target, before visibility culling (triangles): ~120 terrain + 32 trunk + 18 (3×6 platforms) + 16 (2×8 bridges) + 14 hut + 10 (5×2 façades) + 8 (4×2 far single-plane palms) + 6 (3×2 leaf screens) + 6 spring = **230**. This is below the 448 export limit **only if sectorization replaces the existing 442-face stage**; it is *not* 230 faces added to it. A camera can still see too much of the 230, so Ymir needs scene-pacing measurements.

## 4. Production workflow — checkboxes

### Sprint 0: compatibility prerequisites
- [ ] Inventory accepted scene references: approved map, Saturn 718 shots, TGS Jade Gully footage, Project SXU independently. Keep actual assets/licensing separate.
- [ ] Decide and implement **sector-local export** before extending the world past ±256m, with sector origins, adjacency, instancing, scene/collision switching, and persistent entity IDs. Do not presume the current single-stage exporter handles 1.45km.
- [ ] Prove a one-object minimal `render` mesh and a separate `collision` mesh survive the existing Blender toolkit export and `tools/bake_greybox.py`.

### Sprint 1: minimum hybrid kit (first Blender deliverable)
- [ ] `jg_tree_trunk_A`, solid 6–8-sided low-poly, no high-resolution bark geometry.
- [ ] `jg_platform_round_M` and `jg_bridge_short_A` with separately baked simple collision.
- [ ] `jg_house_playable_A` exterior **and** `jg_house_facade_A` background variant.
- [ ] `jg_palm_xplane_A`, `jg_foliage_x_A` with transparency and back-face tests.
- [ ] `jg_spring_red_A` visual + separate trigger placeholder. Do not mark spring gameplay complete.
- [ ] First original checkerboard, hut and foliage textures, with source/license metadata.
- [ ] Save **source .blend** under a versioned project asset path, alongside a JSON manifest of object positions/dimensions/LOD policy.

### Sprint 2: route/blockout
- [ ] Assemble the 50×70m test cell with route A, route B and camera-aware sightlines.
- [ ] Put all walkable platforms, bridge tops and takeoff/landing pads in the explicit collision group. Decorative copies are **render-only**.
- [ ] Verify Sonic's real scale, acceleration, ground contacts, ramps, gaps and springs; adjust dimensions **from measurements**, not solely the concept image.
- [ ] Count triangles, Q16 export degeneracy, 64-entity budget and scene local coordinate bounds.

### Sprint 3: render integration and performance
- [ ] Bake with **pinned** Blender toolkit version, inspect OBJ/JSON and collision C tables.
- [ ] Add *static* X-planes first. Implement actual yaw-facing billboards only if the renderer provides view-updated quads and safe indexed8 transparency, then measure the CPU cost; no claim of generic billboard support today.
- [ ] Budget VDP1 texture/CRAM, stage/sprite material indices and clipping; avoid scenery disappearing near the camera or crossing a seam.
- [ ] Run Ymir `idle`, `curve_route`, `offroad_right` **plus a new Tree Village traversal**; publish PNG/ZIP automatically and inspect near/far/oblique angles.
- [ ] Preserve threshold **≥29 scene submissions/s** and **frame P95 ≤38ms** from the experimental qualification, as *diagnostics*, and independently validate real displayed 30 FPS; never relax these to make scenery pass.
- [ ] Only after passing: integrate the kit into the longer map, with loaded/visible sector and LOD telemetry; separately test physical Saturn/Saroo if available.

## 5. Expected file organization (proposed, not present yet)

```text
assets/jade-gully/tree-village/
    tree_village_source.blend            # one editable Blender source
    kit-manifest.json                   # IDs, dimensions, LOD, collision flags
    source/
        village-wood-64.png
        village-hut-64.png
        foliage-palms-64.png
        checker-ground-64.png
        spring-red-64.png
    generated/                          # exported per-sector bundle, only after integration
        sector_tree_village.render.obj
        sector_tree_village.collision.obj
        sector_tree_village.json
```

## 6. Immediate local baseline to inspect

```bash
cd ~/dev/sonic-xtreme-saturn
git pull --ff-only
XTREME_STAGE_LAYOUT=adventure bash scripts/run-mac.sh --build-only
open -a Blender build/jade-gully-adventure/jade_gully.blend
```

This opens the *existing* small adventure test scene **without** producing Tree Village. Once Sprint 1 assets and the sector-aware builder are implemented, the new Tree Village Blender scene can be generated on the Mac. Neither this plan nor the concept image is proof that new 3D source models already exist.

## Implemented source generator (2026-11-21)

The **first authored 50×70 m Blender test cell** is now defined as code, not merely specified in this checklist:

- [`kit-manifest.json`](../../assets/jade-gully/tree-village/kit-manifest.json): **28 authored pieces**, five static X-plane palms, five decorative 2D house facades, main and spring-required upper paths, and seven editor/entity markers.
- [`tools/create_tree_village_kit.py`](../../tools/create_tree_village_kit.py): creates geometry with independent collision meshes, UVs, seven **original procedural pixel-art source textures** (checker, timber, bark, hut, roof, palm silhouette, spring) packed into a source .blend, camera, lighting and optional overview PNG. **No Blender add-on, network asset, third-party ripped textures or Sega material is used in the generator.**
- [`tools/validate_tree_village_kit.py`](../../tools/validate_tree_village_kit.py) plus host unit tests: verify the manuscript's typed objects, coordinates, IDs, route joins and runtime honesty.
- [`scripts/build-tree-village-mac.sh`](../../scripts/build-tree-village-mac.sh): after `git pull --ff-only`, runs validation and Blender in a clean **origin/main worktree**, checks the actual generated face/vertex totals and **commits the .blend, seven PNGs, report and optional preview to main**. It preserves the currently checked-out experimental branch.

**Current code-only estimate:** 308 render triangles across 28 authored definitions, plus separate collision geometry (verified against build limits by the Mac generator before publishing). This is **a standalone test cell**, not 308 faces inserted into the existing 442/448-face adventure build. **Neither the new .blend nor its preview has been run on the user's Blender until the Mac generator finishes.** No in-game Tree Village, camera-following billboards, collision qualification, spring impulses or sector streaming is implied.

Single Mac command after pulling the current branch:

```bash
cd ~/dev/sonic-xtreme-saturn && git pull --ff-only && bash scripts/build-tree-village-mac.sh
```

The **first-time output on success** will be `assets/jade-gully/tree-village/tree_village_source.blend` in `main`; this local generation is intentionally needed because the authoring runner currently has no Blender binary. Do not describe an unbuilt .blend as already committed.

## Visual audit: first Mac Blender preview (2026-11-21)

The Mac build produced an actual **`tree_village_source.blend`** and a 1280×720 preview and pushed them to `main`. The real [kit report](../../assets/jade-gully/tree-village/kit-report.json) for **v1** showed **308 render triangles, 271 vertices, 96 collision faces, 29 render meshes, 13 collision meshes, 7 entity markers and 7 textures**. Eight host tests passed, and the Blender 5.2.2 authoring run completed successfully.

**Art rejection:** the first [preview](../../assets/jade-gully/tree-village/tree_village_preview.png) looked like a suspended wood track in empty sky. Palm cutouts were thin; facade houses looked like five free-floating wood squares; central tree ended as a bark spike. Passing build limits is not visual approval.

**Generator v2 changes, not yet run in Blender:**

- Expanded original palm frond width and textured **alpha-cutout house facades** with pitched roofs, doors and windows.
- A new original leafy canopy cutout on three cross-planes at the tree crown, replacing the visually bare trunk top.
- Connected **32-triangle terrain valley** under the elevated bridges with its own 32-triangle collision mesh, and five **two-triangle timber supports** holding the facade huts near the main tree (render-only).
- Added original checker-compatible meadow, facade and canopy textures, increasing the v2 palette source set to **10 PNGs**; no Saturn VDP1 migration has been claimed.
- Changed the overview camera framing to show more of the grounds and vegetation.
- Expected v2 render budget: **308 + 6 canopy + 32 terrain + 10 supports = 356 / 448 faces**. Actual faces, collision counts, preview quality, transparency and Blender syntax must be verified by the next Mac build before accepting it.

Rebuild from current working branch (the publisher fetches the latest `main` in an isolated worktree):

```bash
cd ~/dev/sonic-xtreme-saturn && git pull --ff-only && bash scripts/build-tree-village-mac.sh
```

The new preview will replace the file at the same path in `main`. Only after **human inspection of v2** should it progress to renderer integration or the sectorized 1.45-km Act 1 map.

