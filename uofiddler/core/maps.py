"""
Map manager: Reads terrain blocks (map*.mul) and statics (staidx*.mul / statics*.mul).
Supports Felucca, Trammel, Ilshenar, Malas, Tokuno, Ter Mur with radar-color overview and isometric rendering.
"""

import os
import struct
from typing import List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
from uofiddler.core.files import FileManager
from uofiddler.core.radar_col import RadarColManager
from uofiddler.core.art import ArtManager


@dataclass
class MapInfo:
    map_id: int
    name: str
    width: int
    height: int


MAP_DEFINITIONS = [
    MapInfo(0, "Felucca", 7168, 4096),
    MapInfo(1, "Trammel", 7168, 4096),
    MapInfo(2, "Ilshenar", 2304, 1600),
    MapInfo(3, "Malas", 2560, 2048),
    MapInfo(4, "Tokuno", 1448, 1448),
    MapInfo(5, "Ter Mur", 1280, 4096),
]


@dataclass
class LandTile:
    tile_id: int
    z: int


@dataclass
class StaticTile:
    item_id: int
    x: int
    y: int
    z: int
    hue: int


class MapManager:
    _instance: Optional['MapManager'] = None

    def __init__(self):
        self.maps: List[MapInfo] = list(MAP_DEFINITIONS)
        self._map_streams: dict[int, Optional[object]] = {}
        self._staidx_streams: dict[int, Optional[object]] = {}
        self._statics_streams: dict[int, Optional[object]] = {}
        self.reload()

    @classmethod
    def get_instance(cls) -> 'MapManager':
        if cls._instance is None:
            cls._instance = MapManager()
        return cls._instance

    def reload(self):
        for s in list(self._map_streams.values()) + list(self._staidx_streams.values()) + list(self._statics_streams.values()):
            if s:
                try:
                    s.close()
                except Exception:
                    pass
        self._map_streams.clear()
        self._staidx_streams.clear()
        self._statics_streams.clear()

        fm = FileManager.get_instance()
        for m in self.maps:
            p_map = fm.get_file_path(f"map{m.map_id}.mul")
            p_staidx = fm.get_file_path(f"staidx{m.map_id}.mul")
            p_statics = fm.get_file_path(f"statics{m.map_id}.mul")

            # Check if actual width is 6144 (older UO versions)
            if p_map and os.path.exists(p_map):
                f_size = os.path.getsize(p_map)
                # 196 bytes per block (8x8)
                blocks = f_size // 196
                expected_blocks_7168 = (7168 // 8) * (4096 // 8)
                expected_blocks_6144 = (6144 // 8) * (4096 // 8)
                if m.map_id in (0, 1):
                    if blocks == expected_blocks_6144:
                        m.width = 6144
                    elif blocks == expected_blocks_7168:
                        m.width = 7168

                self._map_streams[m.map_id] = open(p_map, "rb")

            if p_staidx and os.path.exists(p_staidx):
                self._staidx_streams[m.map_id] = open(p_staidx, "rb")

            if p_statics and os.path.exists(p_statics):
                self._statics_streams[m.map_id] = open(p_statics, "rb")

    def read_land_block(self, map_id: int, bx: int, by: int) -> List[LandTile]:
        stream = self._map_streams.get(map_id)
        if not stream or bx < 0 or by < 0:
            return []

        m_info = next((m for m in self.maps if m.map_id == map_id), None)
        if not m_info:
            return []

        block_height = m_info.height // 8
        offset = ((bx * block_height) + by) * 196

        try:
            stream.seek(offset)
            header = stream.read(4)
            tiles_raw = stream.read(192)  # 64 tiles * 3 bytes (uint16 id, int8 z)
            if len(tiles_raw) < 192:
                return []

            tiles = []
            for i in range(64):
                tid, z = struct.unpack_from("<Hb", tiles_raw, i * 3)
                tiles.append(LandTile(tile_id=tid, z=z))
            return tiles
        except Exception:
            return []

    def read_static_block(self, map_id: int, bx: int, by: int) -> List[StaticTile]:
        f_idx = self._staidx_streams.get(map_id)
        f_stat = self._statics_streams.get(map_id)
        if not f_idx or not f_stat:
            return []

        m_info = next((m for m in self.maps if m.map_id == map_id), None)
        if not m_info:
            return []

        block_height = m_info.height // 8
        idx_offset = ((bx * block_height) + by) * 12

        try:
            f_idx.seek(idx_offset)
            raw_idx = f_idx.read(12)
            if len(raw_idx) < 12:
                return []
            lookup, length, extra = struct.unpack("<iii", raw_idx)
            if lookup < 0 or length <= 0:
                return []

            f_stat.seek(lookup)
            raw_stat = f_stat.read(length)
            count = length // 7
            statics = []
            for i in range(count):
                iid, x, y, z, hue = struct.unpack_from("<Hbbbh", raw_stat, i * 7)
                statics.append(StaticTile(item_id=iid, x=x, y=y, z=z, hue=hue))
            return statics
        except Exception:
            return []

    def render_minimap(self, map_id: int, start_bx: int, start_by: int, num_blocks_x: int, num_blocks_y: int, show_statics: bool = True) -> Image.Image:
        """
        Renders a radar/minimap block view where each tile is 1 pixel colored by radarcol.mul.
        Optimized with contiguous column I/O for 60 FPS scrolling and panning.
        """
        radar = RadarColManager.get_instance()
        m_info = next((m for m in self.maps if m.map_id == map_id), None)
        if not m_info:
            return Image.new("RGBA", (num_blocks_x * 8, num_blocks_y * 8), (0, 0, 0, 255))

        block_height = m_info.height // 8
        width = num_blocks_x * 8
        height = num_blocks_y * 8
        img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        pixels = img.load()

        f_map = self._map_streams.get(map_id)
        f_idx = self._staidx_streams.get(map_id)
        f_stat = self._statics_streams.get(map_id)

        for b_x in range(num_blocks_x):
            cur_bx = start_bx + b_x
            if cur_bx < 0 or cur_bx >= (m_info.width // 8):
                continue

            # 1. Read entire column slice of land blocks in one single read
            if f_map:
                map_offset = ((cur_bx * block_height) + start_by) * 196
                f_map.seek(map_offset)
                col_map_data = f_map.read(num_blocks_y * 196)
                for b_y in range(num_blocks_y):
                    b_off = b_y * 196 + 4
                    if b_off + 192 <= len(col_map_data):
                        base_lx = b_x * 8
                        base_ly = b_y * 8
                        for i in range(64):
                            tid, z = struct.unpack_from("<Hb", col_map_data, b_off + i * 3)
                            rgba = radar.get_land_color_rgba(tid)
                            shade = max(-30, min(30, z))
                            r = min(255, max(0, rgba[0] + shade))
                            g = min(255, max(0, rgba[1] + shade))
                            b = min(255, max(0, rgba[2] + shade))
                            pixels[base_lx + (i % 8), base_ly + (i // 8)] = (r, g, b, 255)

            # 2. Read entire column slice of static indices in one read, then read statics
            if show_statics and f_idx and f_stat:
                idx_offset = ((cur_bx * block_height) + start_by) * 12
                f_idx.seek(idx_offset)
                col_idx_data = f_idx.read(num_blocks_y * 12)
                for b_y in range(num_blocks_y):
                    i_off = b_y * 12
                    if i_off + 12 <= len(col_idx_data):
                        lookup, length, _ = struct.unpack_from("<iii", col_idx_data, i_off)
                        if lookup >= 0 and length > 0:
                            f_stat.seek(lookup)
                            raw_stat = f_stat.read(length)
                            count = length // 7
                            base_sx = b_x * 8
                            base_sy = b_y * 8
                            for s_i in range(count):
                                iid, sx, sy, _, _ = struct.unpack_from("<Hbbbh", raw_stat, s_i * 7)
                                rgba = radar.get_item_color_rgba(iid)
                                if rgba[3] > 0:
                                    px = base_sx + (sx & 0x7)
                                    py = base_sy + (sy & 0x7)
                                    if 0 <= px < width and 0 <= py < height:
                                        pixels[px, py] = rgba

        return img

    def render_overview(self, map_id: int) -> Optional[Image.Image]:
        """
        Renders a fast 1/8 scale overview of the entire map (1 pixel per 8x8 block).
        Cached per map_id.
        """
        if not hasattr(self, "_overview_cache"):
            self._overview_cache = {}

        if map_id in self._overview_cache:
            return self._overview_cache[map_id]

        stream = self._map_streams.get(map_id)
        m_info = next((m for m in self.maps if m.map_id == map_id), None)
        if not stream or not m_info:
            return None

        radar = RadarColManager.get_instance()
        bw = m_info.width // 8
        bh = m_info.height // 8
        img = Image.new("RGBA", (bw, bh), (0, 0, 0, 255))
        pixels = img.load()

        for bx in range(bw):
            offset = (bx * bh) * 196
            stream.seek(offset)
            col_data = stream.read(bh * 196)
            for by in range(bh):
                b_off = by * 196 + 4
                if b_off + 2 <= len(col_data):
                    tid = struct.unpack_from("<H", col_data, b_off)[0]
                    pixels[bx, by] = radar.get_land_color_rgba(tid)

        self._overview_cache[map_id] = img
        return img
