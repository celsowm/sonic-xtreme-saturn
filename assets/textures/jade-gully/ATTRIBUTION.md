# Jade Gully — real terrain textures (Kenney CC0)

These **8 PNG material images are actual third-party artwork**, committed as untouched source images (not invented/procedural noise). The previous synthetic placeholders were replaced on 2026-11-20.

- **Artist:** Kenney — [Retro Textures Fantasy](https://kenney.nl/assets/retro-textures-fantasy), **Creative Commons Zero (CC0 1.0)**.
- **Mirror of original PNG source files:** [shorepine/kenney — 2d/Retro Textures Fantasy](https://github.com/shorepine/kenney/tree/main/2d/Retro%20Textures%20Fantasy). The mirror's [README](https://github.com/shorepine/kenney/blob/main/README.md) confirms all Kenney art is CC0. The mirror is a format/collection copy, not a claim of a Kenney-operated account.
- **Usage:** source PNG is checked in as-is under `assets/textures/jade-gully/`, and `tools/bake_stage_textures.py` generates indexed8 arrays deterministically at build time. Pixel data is sampled from actual original Kenney images; per-material color grading and reduction to 31 colors provide a shared 256-color RGB555 palette in bank 7, preserving the Saturn's fixed VRAM limits.
- **VRAM:** eight 64×64 indexed8 textures = **32 KiB**, one shared 256-entry CRAM palette. 64×128 wall textures are downsampled vertically to 64×64 at build time; no runtime image decompression/PNG loader.
- **Style:** these are preexisting CC0 retro/fantasy material textures, **not recovered Sonic X-treme assets**, nor an exact final art match.

| Repo PNG | Exact original Kenney source file |
| --- | --- |
| `grass-path.png` | `floor_ground_grass.png` |
| `sand-path.png` | `floor_ground_dirt.png` |
| `rock-grey.png` | `wall_rock.png` |
| `forest-leaves.png` | `floor_ground_grass_overlay.png` |
| `sandstone.png` | `floor_stone_sand_random.png` |
| `waterfall.png` | `floor_ground_water.png` |
| `meadow-grass.png` | `floor_ground_grass.png` (different gameplay material/color grade) |
| `moss-bank.png` | `wall_rock_structure.png` |

### Sonic X-treme historic textures

Several original/prototype-era images and texture sheets have been preserved by the community, e.g. [The Textures Resource — Sonic X-treme prototype](https://textures.spriters-resource.com/saturn/sonicxtreme/) and Sonic Retro's 2009 file discoveries. **Age of the cancelled project, attribution to Sega and the label “fangame” do not establish a public-domain license.** This public source repo uses the Kenney CC0 pack as a redistributable baseline. A separate local-use, user-supplied texture source can be converted through the same indexed8 pipeline if rights/permissions are established; it must not silently replace tracked CC0 sources with third-party copyrighted files.

### Technical limitations

The engine currently maps one stage material to one image across each face; it does **not** preserve source GLB UVs, support material blending or tile repeating over huge polygons yet. Good texture resolution and lighting alone will not turn broad valley quads into a finished Sonic Adventure stage. Next: sector UV tiling and selected face subdivision, material-specific decals and foliage silhouettes, while preserving the 30 FPS visual target.
