"""Host-only telemetry contract tests; no emulator, BIOS or Sonic source needed."""
import importlib.util
import struct
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "qualify-ymir.py"
spec = importlib.util.spec_from_file_location("xtreme_ymir", SCRIPT)
ymir = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ymir)


class YmirTelemetryContractTests(unittest.TestCase):
    def sonic_snapshot(self, *, version=3, clip_mask=0b11111):
        values = {k: 0 for k in ymir.SONIC_NAMES}
        values.update(
            magic=0x53584143, version=version, enabled=1, ready=1,
            vertices=125, faces=159, textures=148, joints=11,
            registry_capacity=164, init_stage=7, clip=0,
            ticks=124, draws=62, clip_mask=clip_mask,
            clip_changes=5, takeoffs=1, landings=2,
            ground_ticks=60, air_ticks=64,
            pos_x=65536, pos_y=2 * 65536, pos_z=(1<<32)-2*65536,
        )
        return b"\0" * 16 + struct.pack(
            ">" + "I" * len(ymir.SONIC_NAMES),
            *(values[k] for k in ymir.SONIC_NAMES)
        ) + b"\0" * 16

    def test_v3_decodes_animation_history_and_signed_position(self):
        raw = self.sonic_snapshot()
        data, address, method = ymir.locate_sonic(raw, [])
        self.assertEqual(method, "header_scan")
        self.assertEqual(address, 0x06000010)
        self.assertEqual(data["clip_mask"], 0b11111)
        self.assertEqual(data["takeoffs"], 1)
        self.assertEqual(data["landings"], 2)
        self.assertEqual(data["position_m"], [1.0, 2.0, -2.0])

    def test_old_v2_record_is_rejected(self):
        raw = self.sonic_snapshot(version=2)
        with self.assertRaises(ValueError):
            ymir.locate_sonic(raw, [])

    def test_character_and_physics_must_have_same_completed_frame(self):
        controller={"ticks":135,"pos_x":262163,"pos_z":-2091936}
        character={"ticks":135,"pos_x":262163,"pos_z":-2091936}
        self.assertEqual(ymir.check_sonic_snapshot_alignment(character,controller),
                         {"actor_sim_sync":True,"actor_position_sync":True})
        # Regression observed on the old live SXAC symbol: Ymir stopped after
        # three actor ticks and read old XTDB from the prior completed frame.
        character.update(ticks=138,pos_z=-2179065)
        self.assertEqual(ymir.check_sonic_snapshot_alignment(character,controller),
                         {"actor_sim_sync":False,"actor_position_sync":False})
        character.update(ticks=135,pos_z=-2091936,pos_x=262164)
        self.assertFalse(ymir.check_sonic_snapshot_alignment(character,controller)["actor_position_sync"])

    def test_recent_frame_history_reports_tail_percentiles(self):
        # A 4-frame synthetic ring after wraparound: only the final four
        # entries count. Slow tail must be visible even at nominal 30 Hz.
        samples=[(0,0,0,0)]*ymir.FRAME_CAPACITY
        samples[62]=(30,1,14,3)
        samples[63]=(33,1,16,3)
        samples[0]=(33,1,16,4)
        samples[1]=(45,2,24,5)
        data=(struct.pack(">4I",0x58465031,1,4,66) +
              b"".join(struct.pack(">4I",*s) for s in samples))
        result=ymir.decode_frame_history(data,0)
        self.assertEqual(result["count"],4)
        self.assertEqual(result["total_frames_recorded"],66)
        self.assertEqual(result["frame_ms_p50"],33)
        self.assertEqual(result["frame_ms_p95"],45)
        self.assertEqual(result["frame_ms_max"],45)
        self.assertEqual(result["scene_ms_p95"],24)

    def render_ring(self, count=64, next_frame=66):
        entries=[(0,)*ymir.RENDER_WORDS for _ in range(ymir.RENDER_CAPACITY)]
        for frame in range(next_frame-count+1,next_frame+1):
            sample={
                "frame":frame,"scene_begin_ms":1,"stage_ms":21+(frame%2),
                "actor_ms":4,"flush_ms":9,"stage_faces_tested":460,
                "stage_visibility_skipped":100,"stage_lod_skipped":40,
                "stage_submitted":300,"marker_submitted":8,
                "actor_submitted":90,"total_submitted":398,
                "total_flushed":380,"painter_culled":42,
                "painter_clipped":3
            }
            entries[(frame-1)%ymir.RENDER_CAPACITY]=tuple(
                sample[k] for k in ymir.RENDER_FIELDS)
        return (struct.pack(">4I",ymir.RENDER_MAGIC,1,count,next_frame)+
                b"".join(struct.pack(">"+str(ymir.RENDER_WORDS)+"I",*entry)
                         for entry in entries))

    def test_render_profile_ring_and_header_scan(self):
        raw=b"\0"*16+self.render_ring()+b"\0"*16
        profile,address,method=ymir.locate_render_history(raw,[])
        self.assertEqual(method,"header_scan")
        self.assertEqual(address,0x06000010)
        self.assertEqual(profile["count"],64)
        self.assertEqual(profile["terminal"]["frame"],66)
        self.assertEqual(profile["stage_submitted_p95"],300)
        self.assertEqual(profile["actor_ms_p95"],4)
        self.assertEqual(profile["stage_ms_p95"],22)
        self.assertEqual(profile["terminal"]["total_submitted"],398)
        self.assertEqual(profile["last_frames"][0]["frame"],3)

    def test_render_profile_rejects_corrupt_or_unattributed(self):
        raw=self.render_ring()
        with self.assertRaises(ValueError):
            ymir.decode_render_history(raw[:-1],0)
        bad=bytearray(raw)
        struct.pack_into(">I",bad,4,2)  # unknown version
        with self.assertRaises(ValueError):
            ymir.decode_render_history(bad,0)
        bad=bytearray(raw)
        last_pos=(66-1)%ymir.RENDER_CAPACITY
        total_field=ymir.RENDER_FIELDS.index("total_submitted")
        struct.pack_into(">I",bad,16+last_pos*ymir.RENDER_WORDS*4+
                         total_field*4,999)
        with self.assertRaises(ValueError):
            ymir.decode_render_history(bad,0)

    def sync_ring(self, count=64, next_frame=66):
        entries=[(0,)*ymir.SYNC_WORDS for _ in range(ymir.SYNC_CAPACITY)]
        for frame in range(next_frame-count+1,next_frame+1):
            sample={
                "frame":frame,"frame_interval_ms":50 if frame in (48,49,50) else 33,
                "begin_ms":17 if frame in (48,49,50) else 5,
                "end_ms":1,"prior_end_gap_ms":0,"active_work_ms":28,
                "field_before_begin":frame*2,
                "field_after_begin":frame*2+1,
                "field_before_end":frame*2+1,
                "field_after_end":frame*2+1,
                "draw_waits_begin_delta":0,"draw_waits_end_delta":0,
                "late_swaps_begin_delta":0,"late_swaps_end_delta":0,
                "draw_timeouts_begin_delta":0,"draw_timeouts_end_delta":0
            }
            entries[(frame-1)%ymir.SYNC_CAPACITY]=tuple(
                sample[k] for k in ymir.SYNC_FIELDS)
        return (struct.pack(">4I",ymir.SYNC_MAGIC,1,count,next_frame)+
                b"".join(struct.pack(">"+str(ymir.SYNC_WORDS)+"I",*sample)
                         for sample in entries))

    def test_sync_ring_wrap_and_magic_scan(self):
        raw=b"\0"*16+self.sync_ring()+b"\0"*16
        sync,addr,method=ymir.locate_sync_history(raw,[])
        self.assertEqual((addr,method),(0x06000010,"header_scan"))
        self.assertEqual(sync["count"],64)
        self.assertEqual(sync["total_frames_recorded"],66)
        self.assertEqual(sync["last_frames"][0]["frame"],3)
        self.assertEqual(sync["terminal"]["frame"],66)
        # Only 3/64 frames are slow: nearest-rank P95 is still 5ms.
        self.assertEqual(sync["begin_ms_p95"],5)
        self.assertEqual(max(x["begin_ms"] for x in sync["last_frames"]),17)
        self.assertEqual(sync["end_ms_p95"],1)
        self.assertEqual(sync["begin_fields_p95"],1)

    def test_sync_ring_rejects_corruption_and_out_of_order(self):
        raw=self.sync_ring()
        for modified in (raw[:-1],):
            with self.assertRaises(ValueError):
                ymir.decode_sync_history(modified,0)
        corrupted=bytearray(raw)
        struct.pack_into(">I",corrupted,4,2)
        with self.assertRaises(ValueError):
            ymir.decode_sync_history(corrupted,0)
        corrupted=bytearray(raw)
        pos=(66-1)%ymir.SYNC_CAPACITY
        struct.pack_into(">I",corrupted,16+pos*ymir.SYNC_WORDS*4,999)
        with self.assertRaises(ValueError):
            ymir.decode_sync_history(corrupted,0)

    def test_slow_frame_correlation_uses_exact_frame_indices(self):
        sync=ymir.decode_sync_history(self.sync_ring(),0)
        samples=[]
        for frame in range(3,67):
            interval=50 if frame in (48,49,50) else 33
            samples.append({"frame_ms":interval,"sim_ms":4,
                            "scene_ms":22,"flush_ms":8})
        pacing={"last_frames":samples,"total_frames_recorded":66,"count":64}
        slow=ymir.correlate_slow_frames(pacing,sync)
        self.assertEqual([s["frame"] for s in slow],[48,49,50])
        self.assertTrue(all(s["begin_call_ms"]==17 for s in slow))
        self.assertTrue(all(s["end_call_ms"]==1 for s in slow))
        self.assertTrue(all(s["begin_fields"]==1 for s in slow))
        pacing["last_frames"][48-3]["frame_ms"]=49
        with self.assertRaises(ValueError):
            ymir.correlate_slow_frames(pacing,sync)

    def test_control_evidence_branch_is_isolated_and_allowlisted(self):
        self.assertIn("ymir-evidence",ymir.EVIDENCE_BRANCHES)
        self.assertIn("ymir-sdk-control-evidence",ymir.EVIDENCE_BRANCHES)
        self.assertNotIn("main",ymir.EVIDENCE_BRANCHES)
        with self.assertRaises(ValueError):
            ymir.publish(Path("/does-not-exist"),Path("/does-not-exist"),{},
                         branch="main")
        with self.assertRaises(ValueError):
            ymir.republish_latest(branch="main")

    def test_control_script_auto_publishes_and_recovers_without_yimir(self):
        script=(SCRIPT.parent/"qualify-jade-sdk-control-mac.sh").read_text()
        self.assertIn('EVIDENCE_BRANCH="ymir-sdk-control-evidence"',script)
        self.assertIn("--evidence-branch \"$EVIDENCE_BRANCH\"",script)
        self.assertIn('if [[ "${1:-}" == "--upload-last" ]]',script)
        self.assertIn("--expected-sdk \"$PIN\"",script)
        self.assertNotIn(" --no-publish",script)

    def test_all_eleven_scenarios_have_replay_and_screenshots(self):
        self.assertEqual(len(ymir.CASES), 11)
        self.assertEqual(len({case[0] for case in ymir.CASES}), 11)
        for name, frames, events, shots in ymir.CASES:
            with self.subTest(name=name):
                self.assertTrue(shots)
                self.assertTrue(all(0 <= n < frames for n in shots))
                self.assertTrue(ymir.pad(events).startswith("0 NONE\n"))
                self.assertGreater(frames, 100)

    def test_adventure_only_offroad_replay(self):
        self.assertEqual(len(ymir.ADVENTURE_CASES),1)
        name,frames,events,shots=ymir.ADVENTURE_CASES[0]
        self.assertEqual(name,"offroad_right")
        self.assertEqual(frames,180)
        self.assertIn((65,"RIGHT",52),events)
        self.assertTrue(all(0<=n<frames for n in shots))

    def test_legacy_proxy_telemetry_remains_independent(self):
        self.assertEqual(ymir.SIZE, 336)
        self.assertEqual(len(ymir.NAMES), 84)
        self.assertEqual(len(ymir.SONIC_NAMES), 27)


if __name__ == "__main__":
    unittest.main()
