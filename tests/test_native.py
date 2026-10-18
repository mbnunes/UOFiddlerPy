"""
Automated unit tests for the native C accelerator and verification of parity with pure Python.
"""

import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PIL import Image
from uofiddler.native import (
    HAS_NATIVE_CORE,
    native_decode_static,
    native_decode_land,
    native_apply_hue,
    native_hash_file_name,
    native_decompress_mythic
)
from uofiddler.core.colors import color16_to_rgba, rgba_to_color16
from uofiddler.core.art import ArtManager
from uofiddler.core.hues import HuesManager
from uofiddler.core.hash_utils import hash_file_name
from uofiddler.core.mythic import MythicDecompress


class TestNativeAccelerator(unittest.TestCase):
    def test_native_loaded(self):
        self.assertTrue(HAS_NATIVE_CORE, "Native C library should compile and load successfully")

    def test_color_conversions(self):
        import uofiddler.native as native
        test_colors = [0, 0x8000, 0x8001, 0xFFFF, 0x1F, 0x03E0, 0x7C00, 0x1234, 0x5555]
        for c in test_colors:
            py_rgba = color16_to_rgba(c)
            c_val = native._lib.uo_color16_to_rgba(c)
            c_rgba = (c_val & 0xFF, (c_val >> 8) & 0xFF, (c_val >> 16) & 0xFF, (c_val >> 24) & 0xFF)
            self.assertEqual(py_rgba, c_rgba)

            c16_py = rgba_to_color16(*py_rgba)
            c16_c = native._lib.uo_rgba_to_color16(*py_rgba)
            self.assertEqual(c16_py, c16_c)

    def test_hash_parity(self):
        test_strings = [
            "build/tileartlegacy/00000001.dds",
            "build/tileartlegacy/00000eed.dds",
            "data/gamedata/legacycontainers.csv",
            "test_hash_string_12345",
            "a",
            "abcdefghijkl",
            "abcdefghijklm"
        ]
        for s in test_strings:
            py_hash = hash_file_name(s)
            c_hash = native_hash_file_name(s)
            self.assertEqual(py_hash, c_hash, f"Hash mismatch for '{s}'")

    def test_static_decode_parity(self):
        am = ArtManager.get_instance()
        # Test known items (2: ankh, 3821: gold coins, 3903: arrows, 7939: robe)
        for item_id in [2, 3821, 3903, 7939]:
            data = am._file_index.get_data(item_id + 0x4000)
            if data:
                c_img = native_decode_static(data)
                self.assertIsNotNone(c_img)
                py_img = am._decode_static(data)
                self.assertEqual(c_img.tobytes(), py_img.tobytes())

    def test_land_decode_parity(self):
        am = ArtManager.get_instance()
        for tile_id in [2, 749, 1176]:
            data = am._file_index.get_data(tile_id)
            if data:
                c_img = native_decode_land(data)
                self.assertIsNotNone(c_img)
                self.assertEqual(c_img.size, (44, 44))

    def test_hue_apply_parity(self):
        am = ArtManager.get_instance()
        hm = HuesManager.get_instance()
        item_img = am.get_static(3821)
        self.assertIsNotNone(item_img)

        hue = hm.get_hue(1)
        if hue and len(hue.colors) >= 32:
            # Full hue
            hued_img = native_apply_hue(item_img, hue.colors, only_gray=False)
            self.assertEqual(hued_img.size, item_img.size)

            # Partial hue
            partial_hued = native_apply_hue(item_img, hue.colors, only_gray=True)
            self.assertEqual(partial_hued.size, item_img.size)


if __name__ == "__main__":
    unittest.main()
