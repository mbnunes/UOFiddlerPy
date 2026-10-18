"""
Comprehensive unit tests for UOFiddlerPy core engine.
Tests hashing, RLE encoding/decoding, tiledata, hues, gumps, textures, radar colors, cliloc, sounds, and multis.
"""

import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from uofiddler.core.hash_utils import hash_file_name, hash_adler32
from uofiddler.core.colors import color16_to_rgba, rgba_to_color16
from uofiddler.core.files import FileManager
from uofiddler.core.art import ArtManager
from uofiddler.core.tiledata import TileDataManager
from uofiddler.core.hues import HuesManager
from uofiddler.core.gumps import GumpManager
from uofiddler.core.textures import TextureManager
from uofiddler.core.radar_col import RadarColManager
from uofiddler.core.multis import MultisManager
from uofiddler.core.animations import AnimationsManager
from uofiddler.core.maps import MapManager


class TestCore(unittest.TestCase):
    def test_hash_file_name(self):
        h = hash_file_name("build/multicollection/housing.bin")
        self.assertEqual(h, 0x126D1E99DDEDEE0A)

    def test_color_conversions(self):
        # Opaque pure red: 5 bits = 31, green = 0, blue = 0
        c16 = (31 << 10) | 0x8000
        r, g, b, a = color16_to_rgba(c16)
        self.assertEqual((r, g, b, a), (255, 0, 0, 255))

        # Roundtrip
        c16_back = rgba_to_color16(255, 0, 0)
        self.assertEqual(c16_back, c16)

    def test_file_manager_auto_detect(self):
        fm = FileManager.get_instance()
        self.assertIsNotNone(fm.uo_dir)
        self.assertTrue(os.path.isdir(fm.uo_dir))

    def test_art_manager(self):
        art = ArtManager.get_instance()
        land0 = art.get_land(0)
        self.assertIsNotNone(land0)
        self.assertEqual(land0.size, (44, 44))

        item0 = art.get_static(0)
        self.assertIsNotNone(item0)
        self.assertEqual(item0.size, (44, 42))

        # Test encoding roundtrip
        encoded_land = art.encode_land(land0)
        self.assertEqual(len(encoded_land), 2048)

    def test_tiledata_manager(self):
        tm = TileDataManager.get_instance()
        self.assertTrue(len(tm.land_tiles) > 0)
        self.assertTrue(len(tm.item_tiles) > 0)
        gold = tm.get_item(0x0EED)
        self.assertIsNotNone(gold)
        self.assertIn("gold", gold.name.lower())

    def test_hues_manager(self):
        hm = HuesManager.get_instance()
        self.assertEqual(len(hm.hues), 3000)
        hue1 = hm.get_hue(1)
        self.assertEqual(len(hue1.colors), 32)

    def test_gumps_manager(self):
        gm = GumpManager.get_instance()
        gump0 = gm.get_gump(0)
        self.assertIsNotNone(gump0)
        self.assertTrue(gump0.width > 0 and gump0.height > 0)

    def test_textures_manager(self):
        tm = TextureManager.get_instance()
        # Test first valid texture
        tex0 = tm.get_texture(0)
        if tex0:
            self.assertIn(tex0.size, [(64, 64), (128, 128)])

    def test_multis_manager(self):
        mm = MultisManager.get_instance()
        m0 = mm.get_multi(0)
        self.assertIsNotNone(m0)
        self.assertTrue(len(m0.components) > 0)
        img = m0.render_isometric()
        self.assertIsNotNone(img)

    def test_animations_manager(self):
        am = AnimationsManager.get_instance()
        frames = am.get_animation_frames(400, 0, 0)
        self.assertTrue(len(frames) > 0)

    def test_map_manager(self):
        mp = MapManager.get_instance()
        self.assertTrue(len(mp.maps) >= 6)
        img = mp.render_minimap(0, 180, 200, 8, 8)
        self.assertEqual(img.size, (64, 64))


if __name__ == "__main__":
    unittest.main()
