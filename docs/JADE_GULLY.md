# Jade Gully — Act 1 (working concept)

An original tropical action stage with a 1997–98 Saturn aesthetic. Initial layout uses only author-created placeholder geometry.

Route: spawn overlook -> acceleration descent -> forest forks -> waterfall crossing -> banked loop -> ruined temple platforms -> final downhill and goal. Upper route rewards speed and precise jumps; lower route is safer and rejoins the main path. Avoid blind pits. Camera must show landing areas before jumps and not clip through walls.

Greybox acceptance: start to finish, alternate route, fall/restart, checkpoint, loop at high speed and disengage at low speed, repeated deterministic replay. Target 3–5 minutes in the full slice; first greybox is much shorter. Place rings and springs only after controller interactions are proven.

Art: layered distant mountains/sky with VDP2 where feasible; modular checkerboard rock, tropical vegetation, temple stones and waterfalls with constrained palettes/UVs, original low-poly assets. Keep collision independent of decorative geometry. Budget per visible sector; prioritize player and interactables.

## Visual pass 0.1 — measured 30 FPS target

The first décor pass adds original low-poly palms near the overlook, bend and temple, four off-track rocks, and a flat blue-cyan waterfall beyond the traversable ribbon. These are silhouette and composition proxies, not final textures, water simulation, or wall collision. The route and its collision mesh are not modified.

The success criteria are: Sonic visible without depth-order artifacts, ground contact and route progress unchanged, all 11 replay scenarios passing with SXAC v3 animation history, zero dropped simulation time, and a stable 30 scene submissions/s with acceptable p95 frame time. Ymir evidence must distinguish **submission cadence** from independently verified displayed FPS; physical-Saturn measurement remains pending.

## Alternative connected Adventure layout (P3 candidate)

Separate from the qualified original 11-case course, [Jade Gully Action Adventure](JADE_GULLY_ADVENTURE.md) now defines four routes, two wider collision-enabled clearings, six region/camera concepts, thirteen semantic entities and ten instances of selected Kenney CC0 source models checked into `assets/kenney/`. The original `tools/create_jade_gully.py` and baseline Ymir course remain unchanged. The new Blender generator `tools/create_jade_gully_adventure.py` budgets 234 render triangles including cliffs/water and decimates imported models before export. **This is an authoring candidate, not a fully playable 3–5 minute stage and not qualified on the Saturn yet.**
