# Sonic R — local character build (private-source gate)

This is a purely local integration experiment. The user-supplied character model and derivative generated assets are **not part of the repository**. Sonic and other Sega assets may have restrictive redistribution terms; the script never uploads source GLB, PNG, SKA1, generated C/H, ELF, ISO, BIN or BIOS to GitHub. The existing public Ymir evidence branch **does contain screenshots** and should only be used if publishing those images is authorized.

The [LibSaturn skeletal importer](https://github.com/celsowm/libsaturn) generates `sonic.c`, `sonic.h`, `sonic.ska` and `report.json` in `assets/private/sonic-r/saturn/`. The CMake build detects local `sonic.c` and `sonic.h`, compiles them together with `src/sonic_actor.c`, and sets `XTREME_HAS_SONIC`. No assets present means the original blue collision proxy is compiled, keeping public CI independent. To use another private path configure `-DXTREME_SONIC_DIR=<dir>`.

The prototype maps generated `sonic_clip_idle`, `sonic_clip_highspeed`, `sonic_clip_jump`, `sonic_clip_falling`, `sonic_clip_landing`, `sonic_clip_brake` and turning clips to the fixed-tick controller. It uses `sat_skeleton3d` playback, `sat_skin_update_mesh` and `sat_scene_submit_instance` in the existing world painter. Character meshes and materials are allocated before rendering, submitted after the stage, and sorted together with scenery. Root motion is intentionally ignored so physics remains authoritative. Standing height is based on generated `sonic_bind_min.y`; heading, speed warping, camera occlusion and transitions are still pending. This first pass compiles all animation and texture tables into the ELF. If the Saturn boot-image RAM budget is exceeded, move the SKA1 archive to the disc and use the existing asset/CDFS loader in a follow-up. Do not disable linker checks.

Mac automated qualification (run exactly once after code pull):

```sh
cd ~/dev/sonic-xtreme-saturn && git pull --ff-only && python3 scripts/qualify-ymir.py --require-sonic
```

The runner recompiles the game, runs 11 independent Ymir replay cases, checks XTDB physics telemetry and now also reads the `xtreme_sonic_debug` symbol from WRAM-H (`SXAC` v2). It requires `ready=1`, `error=0`, nonzero geometry, animation ticks and actual scene draw submissions in every case. The output includes `sonic-telemetry.json` for each case and only hashes for private generated sources; raw asset bytes are never packaged. As with other runs, the log and ZIP are automatically pushed to the `ymir-evidence` branch. The game itself must compile and run on the user's Mac before this can be claimed to work.

Error gates: malformed generated asset, unsupported texture, lack of palette or VDP1 memory, SH-2 linker overrun, animation mismatch and scene capacity are real failures. Do not silently fall back to the blue proxy when the private files are present. Inspect `latest/summary.json` and `latest/build.log` on GitHub to diagnose. The HUD displays generic movement state; character telemetry is machine-readable separately.

The first local importer output produced 281 baked face textures for 286 faces, exceeding LibSaturn's default managed texture registry (64) and causing `SAT_ERR_CAPACITY (-3)` during actor initialization. The optional character module now supplies 297 texture handles via `SAT_TEXTURE_MEMORY`, with slots, regions and hash buckets placed in WRAM-L. This does not alter the SDK default or change any other project's registry. The SXAC v2 block reports the configured capacity, actor initialization stage (1=start, 2=model validated, 3=skeleton validated, 4=mesh setup, 5=upload started, 6=upload complete, 7=ready) and remaining VDP1 VRAM. It has not yet been re-qualified in the emulator.

The initial character size is set by the local importer `--scale 0.03265`. Actual height and on-screen appearance must be verified visually in the Ymir screenshots. No stock-Saturn performance claim is established yet.

## Early boot diagnostics

If the Ymir screen is black, the game can return from `main` and loop in LibSaturn CRT0. That is **not** an XTDB parser bug by itself. The headless harness now extracts a separate initialized `xtreme_boot_debug` (`XBT1`) word record with `stage`, `error`, `main_entries`, and `frames` **before** attempting to decode normal frame telemetry. The game's `fail` path also commits XTDB even if no frame was rendered. The harness reads the independent `SXAC` character error state from the same WRAM dump, including on normal XTDB decode failure.

Stages: 0 = entry into `main` not recorded, 1 = calling `sat_app_init_default`, 2 = Saturn runtime initialized, 3 = debug HUD initialized, 4 = scene allocated, 5 = Sonic initialized (or absent), 6 = frame loop entered, 7 = loop executing. A failure stores its `sat_result_t` numeric code in the record, with the raw emulator PC in the case summary.

Diagnose a black frame with a **single** lightweight replay first:

```sh
cd ~/dev/sonic-xtreme-saturn && git pull --ff-only && python3 scripts/qualify-ymir.py --require-sonic --case idle
```

The result in `latest/idle/boot-telemetry.json`, `latest/idle/sonic-telemetry.json` and `latest/summary.json` distinguishes a startup, asset, texture, or renderer failure without exposing any private source data. Fix that concrete failure before rerunning all eleven replays.

## First working Sonic probe and frame-time baseline

The first private-asset idle Ymir qualification at game commit `44bc3bf`, SDK `08ad63b`, returned PASS with `SAT_OK`, 189 skinned vertices, 286 source faces, 281 material textures, 11 joints, 61 scene submissions and 122 animation ticks, at 320x224. It observed ~30.0 scene submissions/s (33 ms/frame), scene preparation 18 ms, instance submission 7 ms, skinning 1 ms, animation 1 ms, painter flush 4 ms, and 249,504 free VDP1 VRAM bytes. The remaining ten Ymir cases were **not** run with the skinned character yet. Screenshots prove a visible Sonic and Jade Gully but not 60 FPS, gameplay animation transitions, or full-course compatibility.

A small, no-asset-rebake runtime optimization now prevalidates the immutable Sonic face/material binding once at initialization with `sat_scene3d_instance_binding_init`. It is still pending a new measured Ymir replay; never claim an improvement until telemetry confirms it. The Mac harness also accepts `XTREME_SONIC_DIR=/absolute/local/asset/dir` to compare alternative private generated LODs without overwriting the original GLB or C files. The compiler propagates that path into the fresh CMake configuration. Candidate tests must use `--require-sonic` and verify the private source hashes in their summary.
