# Automated Ymir qualification (preferred)

From the Mac checkout under ~/dev:

```sh
cd ~/dev/sonic-xtreme-saturn && git pull --ff-only && python3 scripts/qualify-ymir.py
```

No GUI or manual input. Reuses lib-saturn/harness/build-macos/probe and local BIOS candidates (Tekken 3 profile or LibSaturn Mednafen firmware); override with YMIR_PROBE / LIBSATURN_BIOS or --probe / --bios. Builds with run-mac.sh --build-only, never resets the SDK. Runs eight independent injection-boot scenarios with programmed pad events: idle, pause, one step, jump/resume, HUD pages and viewer, fall/reset, matched HUD on/off routes. Captures PNGs, probe JSON/log and pad timeline, decodes XTDB v2 from high WRAM via map or unique validated magic, extracts the exact telemetry block and produces summary JSON with checks and comparisons. Full WRAM is temporary and not packaged; only game telemetry is returned. Maps, generated headers, build log and hashes of the actual game, SDK revision, probe and BIOS identify the run. No BIOS, disc images or executable are in the ZIP. A build/probe failure still generates a return ZIP with available evidence. Fields in scripts are program fields, not guest ticks; field-driven input can yield different terminal states if HUD changes submission timing. A mismatch is REVIEW, not automatically a physics bug. PASS means automated checks passed, not physical hardware or complete visual qualification.

By default, the runner publishes the ZIP and individually readable JSON, logs, pad scripts and screenshots to the public GitHub branch `ymir-evidence`, under `latest/`. It uses the existing origin credentials, an isolated Git index and a non-force push; main and the local checkout are not modified. The branch history retains earlier runs. Known local paths are redacted before packaging, but logs are still diagnostic data and may contain unexpected local details; use `--no-publish` for private local-only runs. A failed build or failed probe also publishes available evidence. If authentication, size limit or concurrent push prevents upload, the local ZIP remains and the runner exits 2. Use --case to repeat a single scenario. Mednafen remains an independent optional check.

No manual chat attachment is needed: the agent can retrieve latest/summary.json and individual case evidence from the branch, with the ZIP preserved at latest/return.zip.

---

# Debug capture and single step

On Mac, use `bash scripts/capture-mac.sh` instead of run-mac.sh. It builds and runs the same Mednafen launcher, logs console output and source revisions/dirty tracked files, collects new xtreme*.png F9 screenshots from the configured Mednafen snap directory, and writes an xtreme-return timestamped ZIP when the emulator closes. On failed builds the ZIP contains logs but not stale maps. No disc, BIOS or ROM included. Logs may contain local paths; inspect before sharing. If your emulator uses a different screenshot filename or directory, copy screenshots manually. `--build-only` works too.

Game controls (normal play): L toggles pause, R advances exactly one 60 Hz simulation tick when paused, D-pad/analog sets direction, A/C buffers jump for next tick, B resets. L/R still control altitude in X viewer mode. Y changes HUD page and Z vectors regardless of pause. Pause discards wall-clock backlog; no physics elapsed during pause or viewer. Holding R does not repeat; press again for another tick. A/C before R or simultaneously queues jump. Toggling pause clears buffered jump. HUD still refreshes.

Telemetry v2 appends paused, steps, ray_tick, ray_sampled to v1 block. Last ray remains visible across frozen frames, sample tick and NEW flag indicate staleness; reset invalidates it. No raw memory export by Mednafen yet. The clock helper is tested on host with cadence, pause, single-step, suspend, catch-up cap. Target acceptance pending.

Capture compact idle, physics paused on ramp (L), press R three times and capture each tick, jump with A then R and advance through landing, renderer HUD on/off, fork and fall/respawn. Close emulator to assemble ZIP. Compare tick index and positions; note any failures. Separate Ymir WRAM dump and real-hardware tests remain open.
