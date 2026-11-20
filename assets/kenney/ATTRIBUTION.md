# Kenney CC0 environment kit — Jade Gully

The following **9 model binaries are checked into this repository** at `assets/kenney/` for the Sonic X-treme action-adventure stage prototype.

## Rights and provenance

- Original artist: **Kenney** — [Kenney Nature Kit](https://kenney.nl/assets/nature-kit), [Kenney Castle Kit](https://kenney.nl/assets/castle-kit).
- License: **Creative Commons Zero 1.0 Universal (CC0-1.0)** on Kenney's asset pages. [Kenney licensing FAQ](https://kenney.nl/support), [CC0 text](https://creativecommons.org/publicdomain/zero/1.0/).
- Binary GLBs imported here from Kenney's [CC0 converted model library](https://github.com/Hidencod/tge-assets), `packs/nature-kit/` and `packs/castle-kit/`. Its `LICENSE` confirms that these derived GLBs, including embedded textures, are CC0. This is a format-converted mirror, **not** a claim that Kenney published these exact GLB bytes.
- Acquired/verified: 2026-11-20. GLBs are retained with their **original Git blob hashes**. The Git tree is the immutable provenance record; do not replace without updating this document.
- Attribution is not required by CC0 but is included for traceability. The rights to **Sonic R character data** are entirely separate; see `assets/sonic-r/ATTRIBUTION.md`.

## Selected models

| Repo model | Git blob SHA-1 | Intended scene use |
| --- | --- | --- |
| `nature-kit/tree-palm.glb` | `f9bcf4d90cfde7ef2863258442545e983740b2e4` | Palm silhouette |
| `nature-kit/tree-palmbend.glb` | `c8c16dc1c2e3ba02b7cd3d4e93318eec3105253d` | Varied foliage silhouette |
| `nature-kit/rock-largea.glb` | `40e1365a43b706bd78c2658b48b189c9a35f8923` | Gully boulders |
| `nature-kit/cliff-waterfall-rock.glb` | `96d680e199facf3b31f83a77e4b39576c3bc7e9e` | Waterfall cliff structure |
| `nature-kit/plant-bush.glb` | `185be95ecccc59f8edc874587508c44b6a39431b` | Ground vegetation |
| `nature-kit/bridge-wood.glb` | `99cd820a62a664e203842ade58cafd33352de478` | Crossing |
| `nature-kit/platform-grass.glb` | `f382aa18e456c4ba2db5586de4185225d60ac641` | Platforms |
| `castle-kit/wall-pillar.glb` | `d55c45873bc9159c5dd44f50afa8ac9be054ec4d` | Temple columns |
| `castle-kit/wall-doorway.glb` | `06ac4e9e45dd632cc3fdcdda44f6bc107bbdee82` | Temple gateway |

## Saturn conversion

This is a **source/authoring asset library**, not 9 automatically resident Saturn meshes. The Blender stage authoring script selects models on demand and budgets **the resulting triangles and drawn VDP1 commands** per sector. The C/SH-2 runtime is not a generic glTF loader. Selected models must be transformed, decimated or atlased, made render-only unless explicit collision is authored separately, baked through the Blender toolkit, and qualified in Ymir/Mednafen before acceptance. Do not render entire packs or claim target performance based on source file sizes.
