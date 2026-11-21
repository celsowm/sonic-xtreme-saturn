import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.bake_xtreme_rings import (
    FRAME_COUNT,HEIGHT,WIDTH,PALETTE_BANK,COMPRESSED_SHA256,
    SOURCE,META,load,emit,rgb555,
)


class RingSpriteTests(unittest.TestCase):
    def test_source_art_is_versioned_and_checksum_anchored(self):
        meta=json.loads(META.read_text())
        self.assertEqual(meta["author"],"Mr. Malfunction")
        self.assertEqual(meta["frame_increment_sim_ticks"],2)
        self.assertEqual(len(meta["frame_names"]),16)
        self.assertEqual([f"ring{i}.png" for i in range(1,17)],
                         meta["frame_names"])
        self.assertEqual(meta["archive_sha256"],
                         "16e64620bd0b378b9a8523092fd88f222c0dcbe9da65f66c63decfcd3d6895f0")
        self.assertEqual(PALETTE_BANK,6)

    def test_sprites_preserve_source_rotation_and_transparency(self):
        palette,frames=load()
        self.assertEqual(len(frames),FRAME_COUNT)
        self.assertEqual({len(f) for f in frames},{WIDTH*HEIGHT})
        self.assertEqual(len(palette),256)
        self.assertEqual(palette[0],0)  # transparent VDP1 texel code
        self.assertTrue(all(max(f)<=14 and 0 in f and any(f) for f in frames))
        self.assertNotEqual(bytes(frames[0]),bytes(frames[7]))
        self.assertNotEqual(bytes(frames[7]),bytes(frames[8]))
        self.assertEqual(palette[14],rgb555((255,255,57)))

    def test_output_deterministic_without_pillow_or_archive_extractor(self):
        palette,frames=load()
        first=emit(palette,frames).encode("ascii")
        second=emit(*load()).encode("ascii")
        self.assertEqual(first,second)
        self.assertIn(b"xtreme_ring_pixels[16][1024]",first)
        self.assertIn(b"xtreme_ring_palette[256]",first)
        self.assertIn(b"transparent code 0",first)
        self.assertGreater(len(first),16*1024*4)

    def test_invalid_or_modified_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            wrong=Path(temp)/"ring.b64"
            wrong.write_text("eJwDAAAAAAE=")
            with self.assertRaises(ValueError):
                load(wrong,META)

if __name__=="__main__":unittest.main()
