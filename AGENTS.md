# Agent instructions

Read docs/ROADMAP.md, docs/JADE_GULLY.md and docs/ASSETS.md.
Use installed LibSaturn through CMake; no forked renderer, audio driver or hardware code. Inspect current SDK headers and examples before changing anything. General-purpose enhancements go upstream as separate tested changes.
Keep gameplay deterministic, simulation independent of renderer, fixed-point on target, with bounded storage. Test host algorithms before SH-2 build; record Ymir and Mednafen outcomes and actual hardware results separately. No claimed performance without measurements.
Use Blender Toolkit scene contract and headless pipeline; MCP optional for visual authoring. Never add ROMs, BIOS, music, leaked code or unrelated third-party models. The repository owner explicitly requires versioning the Sonic R model under `assets/sonic-r/`; maintain its provenance hashes and visible rights notice, and do not claim or assume Sega or Sketchfab redistribution permission. No further third-party assets without verified licensing. Preserve source/asset license boundaries.
Do not expand beyond the vertical slice until the acceptance gates pass. Record exact dependency revisions and actual test commands. Update roadmap evidence after each milestone.
