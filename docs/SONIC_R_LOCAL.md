# Sonic R — local character build (private-source gate)

This is a purely local integration experiment. The user-supplied character model and derivative generated assets are **not part of the repository**. Sonic and other Sega assets may have restrictive redistribution terms; the script never uploads source GLB, PNG, SKA1, generated C/H, ELF, ISO, BIN or BIOS to GitHub. The existing public Ymir evidence branch **does contain screenshots** and should only be used if publishing those images is authorized.

The [LibSaturn skeletal importer](https://github.com/celsowm/libsaturn) generates `sonic.c`, `sonic.h`, `sonic.ska` and `report.json` in `assets/private/sonic-r/saturn/`. The CMake build detects local `sonic.c` and `sonic.h`, compiles them together with `src/sonic_actor.c`, and sets `XTREME_HAS_SONIC`. No assets present means the original blue collision proxy is compiled, keeping public CI independent. To use another private path configure `-DXTREME_SONIC_DIR=<dir>`.

The prototype maps generated `sonic_clip_idle`, `sonic_clip_highspeed`, `sonic_clip_jump`, `sonic_clip_falling`, `sonic_clip_landing`, `sonic_clip_brake` and turning clips to the fixed-tick controller. It uses `sat_skeleton3d` playback, `sat_skin_update_mesh` and `sat_scene_submit_instance` in the existing world painter. Character meshes and materials are allocated before rendering, submitted after the stage, and sorted together with scenery. Root motion is intentionally ignored so physics remains authoritative. Standing height is based on generated `sonic_bind_min.y`; heading, speed warping, camera occlusion and transitions are still pending. This first pass compiles all animation and texture tables into the ELF. If the Saturn boot-image RAM budget is exceeded, move the SKA1 archive to the disc and use the existing asset/CDFS loader in a follow-up. Do not disable linker checks.

Mac automated qualification (run exactly once after code pull):

```sh
cd ~/dev/sonic-xtreme-saturn && git pull --ff-only && python3 scripts/qualify-ymir.py --require-sonic
```

The runner recompiles the game, runs 11 independent Ymir replay cases, checks XTDB physics telemetry and now also reads the `xtreme_sonic_debug` symbol from WRAM-H (`SXAC` v1). It requires `ready=1`, `error=0`, nonzero geometry, animation ticks and actual scene draw submissions in every case. The output includes `sonic-telemetry.json` for each case and only hashes for private generated sources; raw asset bytes are never packaged. As with other runs, the log and ZIP are automatically pushed to the `ymir-evidence` branch. The game itself must compile and run on the user's Mac before this can be claimed to work.

Error gates: malformed generated asset, unsupported texture, lack of palette or VDP1 memory, SH-2 linker overrun, animation mismatch and scene capacity are real failures. Do not silently fall back to the blue proxy when the private files are present. Inspect `latest/summary.json` and `latest/build.log` on GitHub to diagnose. The HUD displays generic movement state; character telemetry is machine-readable separately.

The initial character size is set by the local importer `--scale 0.03265`. Actual height and on-screen appearance must be verified visually in the Ymir screenshots. No stock-Saturn performance claim is established yet.
