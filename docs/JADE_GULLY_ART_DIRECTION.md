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
