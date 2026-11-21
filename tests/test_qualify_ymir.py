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
