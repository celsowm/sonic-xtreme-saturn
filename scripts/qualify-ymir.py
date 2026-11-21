#!/usr/bin/env python3
"""Headless Ymir qualification. Build, replay, decode, zip; no GUI or BIOS in ZIP."""
import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT.parent
MAGIC = 0x58544442
NAMES = ("magic version bytes frames ticks ticks_frame dropped_ms error hud_error "
         "page geometry viewer grounded respawns "
         "pos_x pos_y pos_z vel_x vel_y vel_z normal_x normal_y normal_z "
         "eye_x eye_y eye_z target_x target_y target_z input_x input_z "
         "held pressed analog_valid analog_x analog_y jump_pending ray_valid ray_hit ray_face "
         "ray_origin_x ray_origin_y ray_origin_z ray_point_x ray_point_y ray_point_z "
         "ray_normal_x ray_normal_y ray_normal_z ray_length ray_distance "
         "frame_ms submit_x10 sim_ms camera_ms scene_ms flush_ms hud_ms "
         "submitted flushed culled clipped skipped rejected blocked world_commands command_capacity "
         "hud_reserved hud_used frame_stats_valid late_swaps draw_waits draw_timeouts vram_free "
         "paused steps ray_tick ray_sampled sweep_queries sweep_hits jumps landings snapshot_begin snapshot_end").split()
SIGNED = {"error", "hud_error", "input_x", "input_z", "ray_length", "ray_distance"} | {
    f"{prefix}_{axis}" for prefix in ("pos","vel","normal","eye","target","ray_origin","ray_point","ray_normal")
    for axis in "xyz"
}
SIZE = len(NAMES)*4

SONIC_NAMES = ("magic version enabled ready error vertices faces textures joints "
               "clip ticks draws animation_ms skin_ms draw_ms pos_x pos_y pos_z "
               "registry_capacity init_stage vram_free "
               "clip_mask clip_changes takeoffs landings ground_ticks air_ticks").split()
SONIC_SIZE = len(SONIC_NAMES) * 4

FRAME_CAPACITY=64
FRAME_WORDS=4
FRAME_NAMES=("frame_ms","sim_ms","scene_ms","flush_ms")

def percentile_nearest_rank(values, percent):
    ordered=sorted(values)
    if not ordered:return None
    return ordered[max(0,((len(ordered)*percent+99)//100)-1)]

def decode_frame_history(raw, offset):
    need=16+FRAME_CAPACITY*FRAME_WORDS*4
    if offset<0 or offset+need>len(raw):
        raise ValueError("truncated frame timing ring")
    magic,version,count,nxt=struct.unpack_from(">4I",raw,offset)
    if magic!=0x58465031 or version!=1 or count>FRAME_CAPACITY or nxt<count:
        raise ValueError("invalid XFP1 timing record")
    samples=[]
    start=(nxt-count)%FRAME_CAPACITY
    for i in range(count):
        pos=(start+i)%FRAME_CAPACITY
        frame=struct.unpack_from(">4I",raw,offset+16+pos*FRAME_WORDS*4)
        samples.append(dict(zip(FRAME_NAMES,frame)))
    return {
        "version":version,"count":count,"total_frames_recorded":nxt,
        "last_frames":samples,
        "frame_ms_p50":percentile_nearest_rank([s["frame_ms"] for s in samples],50),
        "frame_ms_p95":percentile_nearest_rank([s["frame_ms"] for s in samples],95),
        "frame_ms_p99":percentile_nearest_rank([s["frame_ms"] for s in samples],99),
        "frame_ms_max":max((s["frame_ms"] for s in samples),default=None),
        "scene_ms_p95":percentile_nearest_rank([s["scene_ms"] for s in samples],95),
        "sim_ms_p95":percentile_nearest_rank([s["sim_ms"] for s in samples],95),
        "flush_ms_p95":percentile_nearest_rank([s["flush_ms"] for s in samples],95),
    }

def locate_frame_history(raw,maps):
    for p in maps:
        m=re.search(r"0x([0-9a-fA-F]+)\s+_?xtreme_frame_history\b",
                    p.read_text(errors="replace"))
        if m:
            address=int(m[1],16)
            return decode_frame_history(raw,address-0x06000000),address,"map"
    found=[]
    sig=struct.pack(">II",0x58465031,1)
    for m in re.finditer(re.escape(sig),raw):
        if m.start()%4:continue
        try:found.append((m.start(),decode_frame_history(raw,m.start())))
        except (ValueError,struct.error):continue
    if len(found)!=1:raise ValueError(f"expected unique XFP1 timing record, got {len(found)}")
    off,values=found[0]
    return values,0x06000000+off,"header_scan"

BOOT_NAMES=("magic version stage error main_entries frames").split()
BOOT_SIZE=4*len(BOOT_NAMES)

def decode_boot(raw, offset):
    if offset<0 or offset+BOOT_SIZE>len(raw):
        raise ValueError("boot record outside WRAM-H")
    t=dict(zip(BOOT_NAMES,struct.unpack_from(">6I",raw,offset)))
    if t["magic"]!=0x58425431 or t["version"]!=1:
        raise ValueError("boot record header mismatch")
    return t

def locate_boot(raw,maps):
    for p in maps:
        m=re.search(r"0x([0-9a-fA-F]+)\s+_?xtreme_boot_debug\b",p.read_text(errors="replace"))
        if m:
            address=int(m[1],16)
            return decode_boot(raw,address-0x06000000),address,"map"
    found=[]
    header=struct.pack(">II",0x58425431,1)
    for m in re.finditer(re.escape(header),raw):
        if m.start()%4:continue
        try:found.append((m.start(),decode_boot(raw,m.start())))
        except(ValueError,struct.error):continue
    if len(found)!=1:
        raise ValueError(f"expected unique XBT1 record, got {len(found)}")
    off,values=found[0]
    return values,0x06000000+off,"header_scan"

def decode_sonic(raw, offset):
    if offset < 0 or offset + SONIC_SIZE > len(raw):
        raise ValueError("Sonic telemetry outside WRAM-H")
    values = dict(zip(SONIC_NAMES, struct.unpack_from(">"+str(len(SONIC_NAMES))+"I",raw,offset)))
    if values["magic"] != 0x53584143 or values["version"] != 3 or not values["enabled"]:
        raise ValueError("invalid SXAC v3 character telemetry")
    for k in ("pos_x","pos_y","pos_z"):
        if values[k] >= 2**31: values[k] -= 2**32
    values["position_m"] = [values["pos_"+a]/65536 for a in "xyz"]
    return values

def locate_sonic(raw, maps):
    for p in maps:
        m = re.search(r"0x([0-9a-fA-F]+)\s+_?xtreme_sonic_debug\b", p.read_text(errors="replace"))
        if m:
            addr = int(m[1],16)
            return decode_sonic(raw,addr-0x06000000),addr,"map"
    header = struct.pack(">II",0x53584143,3)
    found = []
    for m in re.finditer(re.escape(header),raw):
        if m.start()%4:continue
        try: found.append((m.start(),decode_sonic(raw,m.start())))
        except (ValueError,struct.error):continue
    if len(found)!=1:raise ValueError(f"expected unique Sonic telemetry header, got {len(found)}")
    off,values=found[0]
    return values,0x06000000+off,"header_scan"


def decode(raw, offset=0):
    if len(raw) < offset+SIZE or offset < 0:
        raise ValueError("truncated telemetry")
    values = dict(zip(NAMES, struct.unpack_from(">"+str(len(NAMES))+"I", raw, offset)))
    if (values["magic"], values["version"], values["bytes"]) != (MAGIC, 3, SIZE):
        raise ValueError("telemetry header mismatch (expected XTDB v3)")
    if not values["frames"] or values["snapshot_begin"]!=values["snapshot_end"] or values["snapshot_begin"]!=values["frames"]:
        raise ValueError("uncommitted telemetry snapshot")
    for k in SIGNED:
        if values[k] >= 2**31:
            values[k] -= 2**32
    values["position_m"] = [values["pos_"+a]/65536 for a in "xyz"]
    values["velocity_m_s"] = [values["vel_"+a]*60/65536 for a in "xyz"]
    values["submission_rate_hz"] = values["submit_x10"]/10
    return values

def locate(raw, map_paths):
    for p in map_paths:
        m = re.search(r"0x([0-9a-fA-F]+)\s+_?xtreme_debug\b", p.read_text(errors="replace"))
        if m:
            addr = int(m[1],16)
            off = addr-0x06000000
            return decode(raw,off),addr,"map"
    # Unique fully validated header, never guess if multiple matches.
    header = struct.pack(">III", MAGIC,3,SIZE)
    found = []
    for m in re.finditer(re.escape(header),raw):
        if m.start()%4:continue
        try:found.append((m.start(),decode(raw,m.start())))
        except (ValueError,struct.error):continue
    if len(found)!=1:
        raise ValueError(f"expected unique committed telemetry snapshot, got {len(found)}")
    off, values=found[0]
    return values,0x06000000+off,"header_scan"

def hash_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def git(path, *args):
    p=subprocess.run(["git","-C",str(path),*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    return p.stdout.strip()

def run(cmd, log, env=None, timeout=600):
    with log.open("w") as f:
        f.write("COMMAND: "+repr([str(x) for x in cmd])+"\n");f.flush()
        try:
            p=subprocess.run([str(x) for x in cmd],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=timeout)
            return p.returncode
        except subprocess.TimeoutExpired:
            f.write("\nTIMEOUT\n");return 124
        except OSError as exc:
            f.write("\n"+str(exc)+"\n");return 127

def pad(events):
    rows={0:"NONE"}
    for at,buttons,length in events:
        if at in rows or at+length in rows:
            raise ValueError("overlapping event boundary")
        rows[at]=buttons;rows[at+length]="NONE"
    return "".join(f"{k} {rows[k]}\n" for k in sorted(rows))

# Program fields, not guest ticks. Each run starts fresh with the same boot.
# Leave wide gaps for SMPC sampling; no START (it exits the game).
BASE=[(60,"Y",6),(80,"Z",6),(100,"UP",28),(140,"L",6)]
STEP=BASE+[(190,"R",6)]
JUMP=STEP+[(220,"A",6),(240,"R",6),(270,"L",6),(290,"UP",45)]
CASES=[
    ("idle",130,[],[40,90,129]),
    ("idle_long",280,[],[130,279]),
    ("jump_in_place",200,[(65,"A",6)],[64,72,84,105,150,199]),
    ("curve_route",145,[(65,"UP",28),(95,"UP+RIGHT",12),(109,"UP",28)],[64,95,108,125,144]),
    ("paused",180,BASE,[90,118,165,179]),
    ("one_step",215,STEP,[189,205,214]),
    ("jump_resume",365,JUMP,[239,255,275,305,340,364]),
    ("hud_pages",260,[(60,"Y",6),(90,"Y",6),(120,"Y",6),(150,"Y",6),(180,"Y",6),(210,"X",6)],[45,75,105,135,165,195,245,259]),
    ("fall_reset",400,[(60,"Y",6),(85,"RIGHT",180),(310,"B",6)],[80,150,240,300,345,399]),
    ("hud_on_route",190,[(100,"UP",48),(155,"A",6)],[99,140,189]),
    ("hud_off_route",190,[(20,"Y",5),(35,"Y",5),(50,"Y",5),(65,"Y",5),(80,"Y",5),(100,"UP",48),(155,"A",6)],[99,140,189]),
]

ADVENTURE_CASES=[
    # Move sideways off the 4m ribbon and cross the continuous valley floor.
    # Stronger than "boot PASS": tests collision support outside the old path.
    ("offroad_right",180,[(65,"RIGHT",52)],[64,90,115,145,179]),
]

def check_sonic_snapshot_alignment(sonic, controller):
    """Both SXAC and XTDB must represent the same COMPLETED game frame.
    The rendered Sonic world translation shares exact X/Z fixed-point
    coordinates with the controller; only Y differs by the bind-foot offset.
    """
    return {
        "actor_sim_sync":sonic["ticks"]==controller["ticks"],
        "actor_position_sync":(
            sonic["pos_x"]==controller["pos_x"] and
            sonic["pos_z"]==controller["pos_z"]),
    }

def checks(name,t):
    out={"guest_running":t["frames"]>0 and t["ticks"]>0,
         "world_error_zero":t["error"]==0,"hud_error_zero":t["hud_error"]==0,
         "overlay_within_reservation":t["hud_used"]<=t["hud_reserved"],
         "expected_pause":t["paused"]==1 if name in ("paused","one_step") else t["paused"]==0}
    if name=="jump_in_place":
        out.update(jump_observed=t["jumps"]>=1,landed=t["landings"]>=2 and t["grounded"]==1,no_respawn=t["respawns"]==0)
    if name=="fall_reset":out.update(respawn_observed=t["respawns"]>=2)
    if name=="curve_route":out.update(progress=t["pos_z"]<-24*65536,steered=t["pos_x"]>2*65536,no_respawn=t["respawns"]==0,grounded=t["grounded"]==1)
    if name=="offroad_right":
        out.update(left_original_road=t["pos_x"]>12*65536,
                   still_grounded=t["grounded"]==1,
                   no_respawn=t["respawns"]==0)
    return out


def sanitize_text(work, bios, probe):
    # Evidence is destined for a public repository. Strip known local paths.
    replacements = [(str(bios), "<BIOS>"), (str(probe), "<YMIR_PROBE>"),
                    (str(ROOT), "<GAME>"), (str(DEV), "<DEV>"), (str(Path.home()), "<HOME>")]
    replacements.sort(key=lambda item: len(item[0]), reverse=True)
    for f in work.rglob("*"):
        if not f.is_file() or f.suffix not in (".json", ".log", ".map", ".h", ".pad", ".txt"):
            continue
        original=f.read_text(encoding="utf-8",errors="replace")
        cleaned=original
        for source,replacement in replacements:
            if source and source!="/":cleaned=cleaned.replace(source,replacement)
        if cleaned!=original:f.write_text(cleaned,encoding="utf-8")

def publish(archive, work, summary):
    """Push a standalone evidence tree. Never check out or modify main."""
    branch="ymir-evidence"
    ref="refs/heads/"+branch
    url=subprocess.check_output(["git","-C",str(ROOT),"remote","get-url","origin"],text=True).strip()
    allowed=("https://github.com/celsowm/sonic-xtreme-saturn.git",
             "https://github.com/celsowm/sonic-xtreme-saturn",
             "git@github.com:celsowm/sonic-xtreme-saturn.git",
             "git@github.com:celsowm/sonic-xtreme-saturn",
             "ssh://git@github.com/celsowm/sonic-xtreme-saturn.git",
             "ssh://git@github.com/celsowm/sonic-xtreme-saturn")
    if url.rstrip("/") not in allowed:
        raise RuntimeError("origin is not celsowm/sonic-xtreme-saturn; refusing public upload")
    if archive.stat().st_size >= 95*1024*1024:
        raise RuntimeError("ZIP exceeds safe GitHub Git size threshold; retained locally")
    def cmd(*args,env=None,data=None):
        return subprocess.check_output(["git","-C",str(ROOT),*args],input=data,env=env,stderr=None).decode().strip()
    # Use an isolated temporary index and git plumbing, not the developer's
    # working tree/index. Existing evidence branch history is retained.
    remote=cmd("ls-remote","--heads","origin",ref)
    parent=None
    if remote:
        cmd("fetch","--no-tags","origin",ref)
        parent=cmd("rev-parse","FETCH_HEAD")
    with tempfile.TemporaryDirectory(prefix="xtreme-evidence-index-") as tmp:
        env=dict(os.environ,GIT_INDEX_FILE=str(Path(tmp)/"index"))
        cmd("read-tree","--empty",env=env)
        def add(name,src):
            blob=cmd("hash-object","-w","--",str(src),env=env)
            cmd("update-index","--add","--cacheinfo","100644",blob,name,env=env)
        add("latest/return.zip",archive)
        add("latest/summary.json",work/"summary.json")
        # Small readable files alongside the ZIP let a chat agent retrieve
        # results directly with the GitHub connector instead of parsing ZIP.
        for f in sorted(work.rglob("*")):
            if f.is_file() and f.suffix in (".png",".json",".log",".pad") and f.name!="summary.json":
                add("latest/"+f.relative_to(work).as_posix(),f)
        tree=cmd("write-tree",env=env)
        args=["commit-tree",tree]
        if parent:args += ["-p",parent]
        commit=cmd(*args,"-m","Ymir evidence "+summary["game_commit"][:12]+" "+summary["status"],env=env)
        # A normal non-force push rejects concurrent, divergent publications.
        subprocess.run(["git","-C",str(ROOT),"push","origin",commit+":"+ref],check=True)
    print("[xtreme] GitHub ZIP: https://github.com/celsowm/sonic-xtreme-saturn/blob/"+commit+"/latest/return.zip",flush=True)
    print("[xtreme] Results: https://github.com/celsowm/sonic-xtreme-saturn/tree/ymir-evidence/latest",flush=True)
    print("[xtreme] Evidence commit: "+commit,flush=True)

def republish_latest():
    """Retry publication of an existing complete return ZIP without booting Ymir."""
    candidates=sorted((ROOT/"build").glob("ymir-evidence-*-return.zip"),
                      key=lambda p:p.stat().st_mtime,reverse=True)
    if not candidates:
        print("[xtreme] No previous return ZIP found; run the full qualification.",file=sys.stderr)
        return 2
    archive=candidates[0]
    try:
        # Rebuild a temporary evidence directory from the final sanitized ZIP.
        # Do not trust archive paths, and do not publish a mutable work directory.
        with tempfile.TemporaryDirectory(prefix="xtreme-republish-") as tmp:
            work=Path(tmp)
            with zipfile.ZipFile(archive) as z:
                if z.testzip() is not None:raise ValueError("corrupt return ZIP")
                for item in z.infolist():
                    p=Path(item.filename)
                    if p.is_absolute() or ".." in p.parts:raise ValueError("unsafe ZIP member")
                    if item.is_dir():continue
                    dst=work/p
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(item) as src,dst.open("wb") as out:shutil.copyfileobj(src,out)
            summary=json.loads((work/"summary.json").read_text())
            print("[xtreme] Republishing",archive.name,"game",summary["game_commit"],"status",summary["status"],flush=True)
            publish(archive,work,summary)
        return 0
    except (OSError,ValueError,RuntimeError,KeyError,zipfile.BadZipFile,subprocess.CalledProcessError) as exc:
        print(f"[xtreme] Retry failed: {type(exc).__name__}: {exc}",file=sys.stderr)
        return 2

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--probe",type=Path);p.add_argument("--bios",type=Path)
    is_adventure=os.environ.get("XTREME_STAGE_LAYOUT")=="adventure"
    active_cases=CASES + (ADVENTURE_CASES if is_adventure else [])
    p.add_argument("--case",action="append",choices=[c[0] for c in active_cases])
    p.add_argument("--timeout",type=int,default=600)
    p.add_argument("--require-sonic",action="store_true",help="fail if private Sonic R C/H/SKA are missing")
    p.add_argument("--no-publish",action="store_true",help="keep ZIP local instead of publishing to the public GitHub evidence branch")
    p.add_argument("--publish-latest",action="store_true",help="retry GitHub push of the newest local return ZIP without rebuilding")
    a=p.parse_args()
    if a.publish_latest:return republish_latest()
    sdk=Path(os.environ.get("LIBSATURN_SOURCE",str(DEV/"lib-saturn"))).expanduser()
    if not (sdk/"CMakeLists.txt").exists(): sdk=DEV/"libsaturn"
    probe=a.probe or Path(os.environ.get("YMIR_PROBE",str(sdk/"harness/build-macos/probe")))
    bios_candidates=[DEV/"tekken3-saturn/assets/imported/ymir/profile/roms/ipl/saturn_101a_us.bin",sdk/"bios/firmware/mpr-17933.bin"]
    bios=a.bios or (Path(os.environ["LIBSATURN_BIOS"]) if os.environ.get("LIBSATURN_BIOS") else next((x for x in bios_candidates if x.is_file()),bios_candidates[0]))
    probe=probe.expanduser().resolve();bios=bios.expanduser().resolve()
    output=ROOT/"build";output.mkdir(exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix="ymir-evidence-",dir=output))
    archive=output/(work.name+"-return.zip")
    summary={"status":"incomplete","game_commit":git(ROOT,"rev-parse","HEAD"),"sdk_commit":git(sdk,"rev-parse","HEAD"),
             "game_dirty":git(ROOT,"status","--porcelain","--untracked-files=no"),"sdk_dirty":git(sdk,"status","--porcelain","--untracked-files=no"),
             "boot":"Ymir injection via CUE + app.bin, not optical boot","cases":{},"comparisons":{}}
    sonic_assets=Path(os.environ.get("XTREME_SONIC_DIR",str(ROOT/"assets/sonic-r/lod-160"))).expanduser().resolve()
    sonic_present=all((sonic_assets/f).is_file() for f in ("sonic.c","sonic.h","sonic.ska"))
    summary["sonic_asset_present"]=sonic_present
    summary["sonic_asset_dir"]=str(sonic_assets.relative_to(ROOT)) if sonic_assets.is_relative_to(ROOT) else "<external>"
    if sonic_present:
        summary["sonic_asset_sha256"]=hash_file(sonic_assets/"sonic.ska")
        summary["sonic_asset_source_sha256"]=hash_file(sonic_assets/"sonic.c")
    summary["performance_policy"]={
        "display_target_fps":30,"physics_target_hz":60,
        "min_measured_submission_rate_hz":29.0,"max_terminal_frame_ms":40,
        "max_recent_frame_ms_p95":38,"frame_history_window":64,
        "display_cadence_independently_verified":False,
        "note":"A 1s submission-rate sample and terminal frame time are diagnostic gates, not display FPS or p95."}
    failures=[]
    publish_failed=False
    try:
        if a.require_sonic and not sonic_present:
            raise ValueError(f"Sonic R generated C/H/SKA not found under {sonic_assets}; run scripts/vendor-sonic-r-mac.sh")
        if not probe.is_file() or not os.access(probe,os.X_OK):raise ValueError(f"Ymir probe missing: {probe}; set YMIR_PROBE")
        if not bios.is_file() or bios.stat().st_size!=524288:raise ValueError(f"512 KiB BIOS missing: {bios}; set LIBSATURN_BIOS")
        summary.update(probe_sha256=hash_file(probe),bios_sha256=hash_file(bios))
        print("[xtreme] Building with existing local SDK...",flush=True)
        env=dict(os.environ,LIBSATURN_SOURCE=str(sdk))
        rc=run(["bash","scripts/run-mac.sh","--build-only"],work/"build.log",env,timeout=max(1800,a.timeout))
        summary["build_exit"]=rc
        if rc:raise RuntimeError("build failed; see build.log")
        game=ROOT/"build/game";cue=game/"disc/xtreme.cue"
        apps=sorted(game.rglob("xtreme.app.bin"))
        if not cue.is_file() or len(apps)!=1:raise ValueError(f"disc/app.bin missing or ambiguous: {apps}")
        app=apps[0]
        maps=sorted(game.rglob("*.map"))
        summary.update(app_sha256=hash_file(app),cue_sha256=hash_file(cue))
        for image in (cue.with_suffix(".bin"),cue.with_suffix(".iso")):
            if image.is_file():summary[image.suffix[1:]+"_sha256"]=hash_file(image)
        build_dir=work/"build";build_dir.mkdir()
        for i,m in enumerate(maps):shutil.copy2(m,build_dir/f"{i}-{m.name}")
        for file in ("greybox.h","collision.h"):
            src=game/"generated"/file
            if src.is_file():shutil.copy2(src,build_dir/file)
        for name,frames,events,shots in active_cases:
            if a.case and name not in a.case:continue
            d=work/name;d.mkdir()
            script=d/"input.pad";script.write_text(pad(events))
            wram=d/"wram-high.bin"
            cmd=[probe,"--iso",cue,"--bin",app,"--bios",bios,"--frames",frames,"--out",d/"probe.json",
                 "--pad-script",script,"--dump-wram-high",wram]
            for field in shots:cmd += ["--screenshot",f"{field}:{d / ('frame-%04d.png'%field)}"]
            print(f"[xtreme] Ymir {name}: {frames} fields",flush=True)
            rc=run(cmd,d/"probe.log",timeout=a.timeout)
            result={"exit":rc,"frames_requested":frames,"screenshots_expected":shots,
                    "screenshots_missing":[f for f in shots if not (d/("frame-%04d.png"%f)).is_file()]}
            summary["cases"][name]=result
            if rc or result["screenshots_missing"]:failures.append(name+": probe/screenshots")
            try:
                raw=wram.read_bytes()
                try:
                    boot,boot_addr,boot_method=locate_boot(raw,maps)
                    result["boot"]=boot
                    result["boot_address"]=hex(boot_addr)
                    result["boot_method"]=boot_method
                    (d/"boot-telemetry.json").write_text(json.dumps(boot,indent=2)+"\n")
                except (OSError,ValueError,struct.error) as exc:
                    result["boot_decode_error"]=str(exc)
                if sonic_present:
                    try:
                        sonic,character_addr,character_method=locate_sonic(raw,maps)
                        result["sonic"]=sonic
                        result["sonic_address"]=hex(character_addr)
                        result["sonic_method"]=character_method
                        (d/"sonic-telemetry.json").write_text(json.dumps(sonic,indent=2)+"\n")
                    except (ValueError,OSError,struct.error) as exc:
                        result["sonic_decode_error"]=str(exc)
                try:
                    probe_info=json.loads((d/"probe.json").read_text())
                    pc=probe_info.get("boot",{}).get("pc_after_run")
                    if isinstance(pc,int):result["pc_after_run"]=hex(pc)
                except (OSError,ValueError):
                    pass
                t,addr,method=locate(raw,maps)
                result.update(telemetry=t,telemetry_address=hex(addr),address_method=method,checks=checks(name,t))
                try:
                    hist,hist_addr,hist_method=locate_frame_history(raw,maps)
                    result["frame_pacing"]=hist
                    result["frame_pacing_address"]=hex(hist_addr)
                    result["frame_pacing_method"]=hist_method
                    (d/"frame-pacing.json").write_text(json.dumps(hist,indent=2)+"\n")
                except (ValueError,OSError,struct.error) as exc:
                    result["frame_pacing_decode_error"]=str(exc)
                if sonic_present:
                    hist=result.get("frame_pacing")
                    result["checks"]["frame_history_available"]=(hist is not None and hist["count"]>=30)
                    if hist is not None:
                        result["checks"]["frame_p95_30_target"]=(hist["frame_ms_p95"] is not None and hist["frame_ms_p95"]<=38)
                        result["performance_frame_pacing"]={
                            "recent_samples":hist["count"],
                            "frame_ms_p50":hist["frame_ms_p50"],
                            "frame_ms_p95":hist["frame_ms_p95"],
                            "frame_ms_p99":hist["frame_ms_p99"],
                            "frame_ms_max":hist["frame_ms_max"],
                            "scene_ms_p95":hist["scene_ms_p95"],
                            "independent_display_fps":None}
                if sonic_present:
                    sonic=result.get("sonic")
                    result["checks"]["sonic_rendered"]=(sonic is not None and
                        sonic["ready"]==1 and sonic["error"]==0 and
                        sonic["faces"]>0 and sonic["vertices"]>0 and
                        sonic["ticks"]>0 and sonic["draws"]>0 and
                        sonic["registry_capacity"]>=sonic["textures"] and sonic["init_stage"]==7)
                    if sonic is not None:
                        mask=sonic["clip_mask"]
                        result["checks"].update(check_sonic_snapshot_alignment(sonic,t))
                        result["actor_snapshot_alignment"]={
                            "sonic_ticks":sonic["ticks"],
                            "controller_ticks":t["ticks"],
                            "delta_ticks":sonic["ticks"]-t["ticks"],
                            "x_delta_fixed":sonic["pos_x"]-t["pos_x"],
                            "z_delta_fixed":sonic["pos_z"]-t["pos_z"],
                        }
                        if name in ("idle","idle_long"):
                            result["checks"]["idle_clip_visited"]=bool(mask & (1<<0))
                        if name=="curve_route":
                            result["checks"]["run_clip_visited"]=bool(mask & (1<<1))
                            result["checks"]["animation_transitions"]=sonic["clip_changes"]>=2
                        if name=="jump_in_place":
                            result["checks"]["jump_clip_visited"]=bool(mask & (1<<2))
                            result["checks"]["falling_clip_visited"]=bool(mask & (1<<3))
                            result["checks"]["landing_clip_visited"]=bool(mask & (1<<4))
                            result["checks"]["takeoff_observed"]=sonic["takeoffs"]>=1
                            result["checks"]["landing_observed"]=sonic["landings"]>=2
                        if name=="fall_reset":
                            result["checks"]["falling_clip_visited"]=bool(mask & (1<<3))
                        result["performance"]={
                            "target_display_fps":30,
                            "measured_submission_rate_hz":t["submission_rate_hz"],
                            "terminal_frame_ms":t["frame_ms"],
                            "simulated_physics_hz":60,
                            "display_cadence_independently_verified":False}
                        result["checks"]["submission_rate_30_target"]=t["submission_rate_hz"]>=29.0
                        result["checks"]["terminal_frame_budget"]=t["frame_ms"]<=40
                        result["checks"]["no_draw_timeout"]=t["draw_timeouts"]==0
                        result["checks"]["no_late_swap"]=t["late_swaps"]==0
                        result["checks"]["no_dropped_physics_time"]=t["dropped_ms"]==0
                        result["checks"]["command_headroom"]=t["world_commands"]+t["hud_reserved"]<=t["command_capacity"]

                (d/"telemetry.json").write_text(json.dumps(t,indent=2)+"\n")
                off=addr-0x06000000
                (d/"telemetry.bin").write_bytes(raw[off:off+SIZE])
                # WRAM can contain injected application code; keep only requested telemetry in return ZIP.
                wram.unlink()
                if not all(result["checks"].values()):failures.append(name+": telemetry checks")
            except (OSError,ValueError,struct.error) as exc:
                result["decode_error"]=str(exc);failures.append(name+": decode")
                if wram.exists():
                    result["wram_sha256"]=hash_file(wram);wram.unlink()
        cases=summary["cases"]
        def compare(label,names,fn):
            if all("telemetry" in cases.get(n,{}) for n in names):
                outcome=fn(*(cases[n]["telemetry"] for n in names))
                summary["comparisons"][label]=outcome
                if not outcome:failures.append(label)
        compare("idle_no_drift",["idle","idle_long"],lambda x,y:all(x[k]==y[k] for k in ("pos_x","pos_y","pos_z","vel_x","vel_y","vel_z","grounded")))
        compare("paused_to_one_step",["paused","one_step"],lambda x,y:y["ticks"]-x["ticks"]==1 and y["steps"]-x["steps"]==1)
        compare("hud_on_off_terminal_state",["hud_on_route","hud_off_route"],lambda x,y:y["page"]==0 and x["page"]!=0 and all(x[k]==y[k] for k in ("ticks","pos_x","pos_y","pos_z","vel_x","vel_y","vel_z","grounded")))
        if sonic_present and all("sonic" in cases.get(k,{}) for k in ("paused","one_step")):
            p_actor=cases["paused"]["sonic"];s_actor=cases["one_step"]["sonic"]
            outcome=s_actor["ticks"]-p_actor["ticks"]==1
            summary["comparisons"]["sonic_paused_to_one_step"]=outcome
            if not outcome:failures.append("sonic_paused_to_one_step")
        if sonic_present and all("sonic" in cases.get(k,{}) for k in ("hud_on_route","hud_off_route")):
            a_actor=cases["hud_on_route"]["sonic"];b_actor=cases["hud_off_route"]["sonic"]
            fields=("ticks","clip","clip_mask","clip_changes","takeoffs","landings","pos_x","pos_z")
            outcome=all(a_actor[k]==b_actor[k] for k in fields)
            summary["comparisons"]["sonic_hud_on_off_deterministic"]=outcome
            if not outcome:failures.append("sonic_hud_on_off_deterministic")

        # Different observed field cadence can invalidate HUD equivalence; report, don't hide it.
        summary["status"]="pass" if not failures else "review"
    except (OSError,ValueError,RuntimeError) as exc:
        failures.append(str(exc));summary["status"]="failed"
    finally:
        summary["failures"]=failures
        (work/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
        sanitize_text(work,bios,probe)
        with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for f in sorted(work.rglob("*")):
                if f.is_file() and f.name!="wram-high.bin":z.write(f,f.relative_to(work))
        print(f"\n[xtreme] {summary['status']}: {archive}",flush=True)
        if not a.no_publish:
            try:
                publish(archive,work,summary)
            except (OSError,RuntimeError,subprocess.CalledProcessError) as exc:
                print(f"[xtreme] GitHub publish failed: {type(exc).__name__}. ZIP retained: {archive}",file=sys.stderr,flush=True)
                publish_failed=True
    if publish_failed:return 2
    return 0 if summary["status"]=="pass" else 1

if __name__=="__main__":
    sys.exit(main())
