# Jade Gully — Sonic X-treme collectible rings and Saturn-native distance fade

Status: **design/asset-selection gate; NOT yet activated in the game**.
The original Jade Gully PR #2 still runs 8-quad procedural ring annuli. These
cost `8 * rings_in_view` scene submissions (the last XRH1 run recorded 32
marker submissions). They do not collect, animate or change the HUD.

## 1. Ring visual sources and build identity

The Spriters Resource has a sheet titled **Ring (v40)** at
https://www.spriters-resource.com/pc_computer/sonicxtreme/asset/28332/
(386x58, PNG, submitted by Shadowth117). This is currently classified as
**PC / Computer, Sonic X-treme**: despite old URLs under
`/saturn/sonicxtreme/asset/28332/`, it is *not proof of the Saturn 718 ring
source*. The actual Saturn prototype category has
https://www.spriters-resource.com/saturn/sonicxtreme/asset/195366/
(**HUD (July 18th 1996 Build)**), which should not be confused with a full
world-space ring animation.

**Do not silently replace the world ring with a guessed sheet**. Confirm
actual source build, frame boundaries, palette, transparency, copyright and
rotation sequence from the accepted asset. The Spriters Resource terms
https://www.spriters-resource.com/page/tou/ restrict commercial reuse and
call for credit; Sega's original rights remain separate. To keep PR #2
reproducible, track the selected source file, author/source attribution and
SHA-256 (or a documented independent permission) before enabling the
runtime. Do not add unlicensed source art or build-time network downloads.

### Proposed stock-Saturn renderer (once artwork is selected)

- Replace the procedural `draw_gold_ring` eight-quadrilateral annulus with
  **one billboard quad per ring**, selecting a frame from a small resident
  indexed8 VDP1 texture sequence. Use transparent palette index 0; convert
  source sheet offline into frame-aligned, width-multiple-of-8 texture pixels
  and a single RGB555 palette with an explicit VRAM/CRAM accounting test.
- Keep rings facing the chase camera using a yaw billboard basis (or camera
  right/up basis if the source art requires it). A fixed 16.16 scale and
  anchor/origin must preserve existing 3D positions and sorting in the
  `sat_scene_t` painter; no 2D HUD shortcut.
- Animate by 60 Hz simulation ticks, not render frame count; stay deterministic
  at 20/23/30 scene submissions/s. Keep ring collection/counters separate
  from this graphics pass.
- Preserve a documented **procedural fallback only while an approved
  source sheet is missing**, and clearly log that it is still provisional.
- Verify front/back shading, thin-angle readability, occlusion by Sonic,
  palette code 0, and no overdraw on genuine Ymir captures. Estimate four
  visible rings as 4 quads instead of 32, but measure actual stage_ms and
  painter cost rather than claiming 28 saved GPU commands in advance.

## 2. LibSaturn ALREADY has world LOD and Sonic-R-class distance fade

Use existing official LibSaturn APIs instead of a custom fake fog:

- `sat_world_lod3d_plan()` — frustum/projection-size-aware LOD selection,
  resident-resource fallback, budgets and stateful hysteresis
  (`include/saturn/world_lod3d.h`).
- `sat_fade3d_slot()` — quantized view-depth fade and per-object slot
  hysteresis (`include/saturn/fade3d.h`).
- `sat_world_lod3d_fade_apply()` — compatibility-aware adapter for the
  selected draw and its material (`include/saturn/world_lod_fade3d.h`).
- `sat_world_lod3d_governor_step()` — adaptive budget policy.
- Working examples: `examples/distance_fade_3d`,
  `examples/world_lod3d_demo`, `examples/city_walk`.

**Do not confuse two different mechanisms:** a smaller LOD mesh cannot
generically crossfade through a nearer opaque VDP1 mesh. The Saturn fade
uses 8 **VDP2 sprite colour-calculation ratio slots**, for supported
indexed VDP1 sprites over *lower-priority VDP2 backgrounds*. That is the
Sonic R-style far-horizon transition, not arbitrary alpha blending between
VDP1 surfaces. The LibSaturn adapter explicitly falls back for unsupported
RGB, LUT4/RGB-coded combinations, or missing VDP2 composition. Mixing
RGB-coded Sonic and indexed faded stage art needs emulator compositing
checks. Do not add alpha slots until a legitimate NBG0/RBG0 background
layer and sprite/backdrop priority policy are configured.

### Practical migration in Jade Gully

1. Retain the single `sat_scene_t` painter. Instead of separate
   geometry-only 24/30-metre tree thresholds and XZ rectangle guesses,
   group **real scene objects** (terrain sectors, tree/bush groups,
   rings as optional small objects) and create bounded view+LOD inputs.
   Do not call planner per triangle or process the entire map recursively.
2. First prove the world planner **without fade**, matching the current
   same-camera screenshots and preserving untouched collision meshes.
   Use XRH1 before/after per-class timings.
3. Create a **real VDP2 sky/background** and verify indexed sprite colour
   calculation using the distance-fade example on the **same SDK pin**.
4. Enable fade only for author-approved *far scenery/foliage*; keep Sonic,
   nearby terrain, rings and UI opaque. Prefer start/end near the far draw
   distance (authoring values after camera measurements, not hardcoded
   guesses). Fade out before culling, with hysteresis.
5. Keep trees' trunks and foliage in the **same logical object** and
   switch both at once. Configure opacity and phase from the group rather
   than per face. Transparent far meshes must not hide opaque near
   terrain; verify overlaps and the painter's depth ordering.
6. Qualify idle/curve/offroad in Ymir against pinned `08e39e9` and
   the current local SDK independently. Targets: >=29 scene
   submissions/s, P95 <=38ms (normal play), 0 dropped time/late swaps/
   draw timeouts, collision unchanged, no popping, no holes, no flicker,
   and **human-reviewed screenshots**. Independently measured display
   FPS remains a separate gate.

Historical footnote: Sonic R used distance-dependent transparency by
the VDP2's blend ratios. An analysis is available in the published
hardware case study and `examples/distance_fade_3d/README.md`.
Neither that technique nor this document certifies the visual quality
of Jade Gully until it is actually integrated.
