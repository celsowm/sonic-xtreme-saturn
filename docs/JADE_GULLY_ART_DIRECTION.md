# Jade Gully — visual quality bar (not the 32X floating-platform look)

## Visual problem observed in the Ymir evidence

The previous Adventure smoke passed four functional replays at 30 scene submissions/s, yet still looked like a 32X/Sonic Mars-era technical demonstration: narrow green paths floating over a uniform blue void, vertical greybox cliff walls, a tiny Sonic in a high follow camera, colored editor diamonds instead of collectibles, and props reduced to 5–9 triangles. **Functional PASS is not visual acceptance.**

The requested direction is a contiguous, colorful **Sonic Adventure-style** action-platform stage adapted to **stock Saturn** constraints, not an exact remake of any SEGA environment.

## Visual revision v2 — implementation gate

1. **Ground before props.** Replace the 88-triangle vertical suspended-path skirts with one continuous 80-triangle valley mesh that follows the main road, has a left raised canopy ridge and a lower river basin on the right, and extends under the player start. It is both render and collision geometry: Sonic should be able to walk off a road onto open landscape. Keep route ribbons and pads as optional route surfaces.
2. **Branches integrated into terrain.** Add 24 triangles of short terraces beneath upper/riverside/temple routes, without sealing the whole valley behind vertical faces.
3. **Readable hero.** The Adventure camera starts at about 7m behind, 3.5m above and 60° FOV rather than 10m/5m/65°. Sonic should occupy noticeably more of the display. Camera smoothing still uses the library, and the old classic-stage camera remains unchanged.
4. **No editor artifacts in gameplay.** The Adventure default hides the debug overlay; pressing Y still opens the diagnostic pages. Gold rings are initially rendered as 8-sided hollow annuli instead of cyan/yellow/magenta diagnostic diamonds. **They are not yet collectible.** Other markers remain visible only with debug on.
5. **Bounded sector visibility.** Only nearby stage faces and markers are submitted in follow mode (55m lateral, 85m forward, 60m rear, using face AABBs); overview-camera mode retains full geometry. Full collision and deterministic physics are retained regardless of rendering visibility.
6. **Scene budget.** A maximum 250 estimated stage triangles (80 valley, 24 branch banks, 44 ribbon surface, 20 clearing tops and banks, 80 maximum authored CC0 props, 2 waterfall). The baked stage remains constrained to 256 faces and 2048 source vertices; the 159-face Sonic is accounted for in scene face capacity separately. The original CC0 models remain available under assets/kenney for later higher-detail LOD and UV texture-bake work. The landscape is still untextured — a **first compositional fix**, not completed artwork.

## Acceptance: art *and* physics *and* pacing

A visual-quality verdict requires **actual post-v2 Ymir screenshots**, at least from idle, moving curve, elevated branch, river basin and temple; frame samples are never a substitute for reviewing silhouettes. The user must be able to identify a landscape rather than floating strips. Terrain should occupy the foreground, distant terrain should create visual depth, Sonic should be more prominent, and editor overlays should not cover the gameplay image. Resolve overdraw/occlusion if the continuous ground paints above the hero.

Do not accept if the game regresses in collision, running, jumping, respawns, animation selection, frame pacing, VDP1 errors or VRAM headroom. Target **30 displayed FPS** with physics at 60 Hz; the Ymir measured submission rate of 30/s and recent-frame p95 at most 38 ms are diagnostic gates, not independent TV output measurements. Re-run Ymir on the changed scene, including new side-landscape traversal and off-path landings (the original four scripted probes do not yet cover those).

After this revision the highest-value production work is: authentic visual terrain textures via indexed8 VDP1 or VDP2 where technically appropriate; vegetation clusters with distance LOD; artist-directed camera corners; true ring collection and count; springs/checkpoints; more authored cliff/river topology; spatialized entities and sector loading. **Do not solve a perceived quality problem just by scattering more props onto ribbons.**

## Ymir v2 replay — synchronized actor, remaining 49ms outlier

The completed five-case Adventure probe at game commit `475fcadaf54fced1a56750ac152e83cf4b445ed3` confirmed **exact same-frame Sonic/physics tick and X/Z state** across all five cases. Unlike the previous run, there is no stale SXAC-vs-XTDB discrepancy (the curve case was exactly 135/135 ticks). Four cases passed all checks; `curve_route` still returned `review` solely due to a **49ms terminal interval**. All five runs measured 30 scene submissions/s and 34ms p95, with no draw timeouts, dropped simulation time, late swaps, or reported rendering errors. The curve's p99/max are 49ms, so *average cadence alone is insufficient*. These are actual Ymir evidence results, not a new hardware FPS claim.

To create render headroom while preserving the geometry, character and 30 FPS goal, the **next candidate** precomputes every static Adventure face's bounding box and four world-space vertices at boot. This removes per-frame repeated indexed vertex gathers and AABB scans. It is **not yet Ymir-qualified**: do not claim the 49ms peak is gone or a new frame rate until a subsequent five-case probe succeeds. The optimized scene has no changes to collision geometry and the classic build remains unchanged. See `src/main.c` (`stage_prepare_bounds`, `stage_cached_quads`).

The screenshots are still a highly simplified, flat-colored valley. Real art direction needs ground textures, coherent elevation silhouettes, grouped vegetation and identifiable landmarks. Future scene work should be accepted visually on actual emulator screenshots, not from function-level smoke PASS alone.

## Real CC0 texture pass — first Saturn build candidate

The fake hand-generated noise patterns have been replaced with **eight unchanged source PNGs** from Kenney's CC0 [Retro Textures Fantasy](https://kenney.nl/assets/retro-textures-fantasy) pack, retained in `assets/textures/jade-gully/`. See the material-by-material [attribution](../assets/textures/jade-gully/ATTRIBUTION.md). The `tools/bake_stage_textures.py` host converter reads indexed PNGs with Python stdlib, grades them for the tropical palette and reduces each to 31 colors in one 256-color RGB555 CRAM bank. It emits eight 64×64 indexed8 patterns (32 KiB of VDP1 VRAM) at build time. All 238 baked stage faces use these real texture materials instead of RGB-only debug colors in the **Adventure** layout. The classic layout is unchanged.

**CI source-art + conversion gate passed** in [run 44847714151](https://github.com/celsowm/sonic-xtreme-saturn/actions/runs/44847714151), including 26 Python tests, byte-identical generator runs and host C syntax checks. But that only validates authoring and code interfaces. The last published 5-case Ymir PASS refers to the *pre-texture* map. The new build must still prove material upload, appearance and its 30 submissions/s/p95 budget in Ymir.

**Not yet solved:** stage quadrilateral texturing maps one 64×64 image across each polygon rather than repeating it by real-world UV coordinates, so broad valley faces can look stretched; near-clipped textured polygons fall back to RGB rather than tessellated UV clipping. Real improvement after the first rendered screenshot requires UV-authored tiling/face subdivision at close distance, higher-quality mixed foreground materials, denser vegetation and authored landmarks. Do not confuse "real licensed textures" with "final art quality".

## Art v3 candidate — readable foreground and authentic CC0 surfaces

The next revision addresses *why* the v2 Ymir frames looked poor instead of accepting their functional PASS. The original continuous landmass was a single green surface composed of broad triangles. The Adventure builder now preserves the main-road intermediate station, introduces four near-field longitudinal splits and emits four adjacent valley bands with distinct, **already licensed Kenney source textures**: foliage on the rising left canopy, moss along the inner bank, grass across the playable floor and rocky terrain at the outer bank. Each band has a corresponding collision copy. The resulting terrain budget is 120 triangles, rather than 80. Static textures remain VDP1 indexed8 and unchanged.

The manifest now contains 18 sourced scenery instances (up from 10): near-spawn palms and bushes, visible rock accents, and more recognizable 17–20-triangle palms rather than every palm being decimated to 8 triangles. The exporter estimates 442 scene triangles under a strict 448-face limit, excludes the 159-face Sonic from that static scene budget, and continues to use deterministic near-field visibility. Classic mode is untouched. **No new third-party art or proprietary X-treme rip was introduced.**

**Remaining shortcomings:** every large polygon still maps the full texture; full meter-based UV tiling, dedicated scenic silhouettes, a real VDP2 sky, occlusion/LOD improvements and dynamic entity gameplay are still open. The increased triangle count *might* regress performance. Before acceptance, require a clean host Blender/SH-2 build, five-case Ymir screenshots, `frame_ms_p95 <=38`, no late swaps/timeouts/dropped simulation, collision evidence at the off-road point, and a separate human visual review. No hardware FPS or artistic success is claimed by this source-only commit.
