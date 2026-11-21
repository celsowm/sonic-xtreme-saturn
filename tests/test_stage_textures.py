"""Regression tests for REAL third-party CC0 texture conversion to Saturn data."""
import unittest
from pathlib import Path
from tools.bake_stage_textures import (
    NAMES,read_png,build,emit,rgb555
)

ROOT=Path(__file__).resolve().parents[1]/"assets/textures/jade-gully"

class RealStageTextureTests(unittest.TestCase):
    def test_all_eight_source_pngs_are_real_decodable_art(self):
        self.assertEqual(len(NAMES),8)
        for name in NAMES:
            with self.subTest(name=name):
                f=ROOT/(name+".png")
                self.assertTrue(f.is_file())
                # Sources must remain PNGs, not generated C byte arrays.
                data=read_png(f.read_bytes())
                self.assertEqual(len(data),64*64)
                self.assertGreater(len(set(data)),8)

    def test_palette_and_pixel_budget(self):
        palette,pixels,fallback,metrics=build(ROOT)
        self.assertEqual(len(palette),256)
        self.assertEqual(len(pixels),8)
        self.assertEqual(len(fallback),8)
        for i,material in enumerate(pixels):
            self.assertEqual(len(material),4096)
            self.assertGreaterEqual(min(material),i*32+1)
            self.assertLessEqual(max(material),i*32+31)
            self.assertGreaterEqual(len(set(material)),4)
            self.assertTrue(all(color&0x8000 for color in palette))
        self.assertEqual(8*64*64,32768)

    def test_generated_native_header_is_bit_identical(self):
        first=build(ROOT)
        self.assertEqual(emit(*first[:3]),emit(*build(ROOT)[:3]))
        output=emit(*first[:3])
        self.assertIn("stage_pixels[8][4096]",output)
        self.assertIn("stage_palette[256]",output)
        self.assertIn("grass-path",output)
        self.assertNotIn("random",output.lower())

    def test_brightness_grade_is_not_flat_rgb(self):
        _,pixels,_,_=build(ROOT)
        # At least six source images should carry 8+ distinct palette indices
        # after quantization: identical solid colors cannot pass this gate.
        self.assertGreaterEqual(sum(len(set(row))>=8 for row in pixels),6)
        self.assertEqual(rgb555((255,0,0)),0x801f)

if __name__=="__main__":
    unittest.main()
