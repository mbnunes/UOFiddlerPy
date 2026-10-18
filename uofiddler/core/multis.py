"""
Multis manager: Reads multi structures (houses, ships, structures) from multi.mul / multi.idx or MultiCollection.uop.
Provides isometric 2D/3D multi rendering onto a PIL Image canvas and text script import/export.
"""

import struct
from typing import List, Optional, Dict
from dataclasses import dataclass
from PIL import Image
from uofiddler.core.file_index import FileIndex
from uofiddler.core.art import ArtManager


@dataclass
class MultiComponent:
    item_id: int
    offset_x: int
    offset_y: int
    offset_z: int
    flags: int
    unk1: int = 0


class MultiStructure:
    def __init__(self, multi_id: int, components: List[MultiComponent]):
        self.multi_id = multi_id
        self.components = components

        # Calculate bounding box
        if components:
            self.min_x = min(c.offset_x for c in components)
            self.max_x = max(c.offset_x for c in components)
            self.min_y = min(c.offset_y for c in components)
            self.max_y = max(c.offset_y for c in components)
            self.min_z = min(c.offset_z for c in components)
            self.max_z = max(c.offset_z for c in components)
        else:
            self.min_x = self.max_x = self.min_y = self.max_y = self.min_z = self.max_z = 0

    def render_isometric(self, max_z: int = 300) -> Optional[Image.Image]:
        if not self.components:
            return None

        art = ArtManager.get_instance()

        # Sort components for isometric drawing:
        # standard depth sort: Z first, then X + Y
        sorted_comps = sorted(self.components, key=lambda c: (c.offset_z, c.offset_x + c.offset_y, c.offset_x))

        # First pass: compute screen coordinates and canvas bounds
        draw_items = []
        screen_min_x = 999999
        screen_max_x = -999999
        screen_min_y = 999999
        screen_max_y = -999999

        for c in sorted_comps:
            if c.offset_z > max_z:
                continue
            bmp = art.get_static(c.item_id)
            if not bmp:
                continue

            px = (c.offset_x - c.offset_y) * 22 - (bmp.width // 2)
            py = (c.offset_x + c.offset_y) * 22 - (c.offset_z * 4) - bmp.height

            draw_items.append((bmp, px, py))

            screen_min_x = min(screen_min_x, px)
            screen_max_x = max(screen_max_x, px + bmp.width)
            screen_min_y = min(screen_min_y, py)
            screen_max_y = max(screen_max_y, py + bmp.height)

        if not draw_items:
            return None

        padding = 10
        width = (screen_max_x - screen_min_x) + (padding * 2)
        height = (screen_max_y - screen_min_y) + (padding * 2)

        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        offset_x = -screen_min_x + padding
        offset_y = -screen_min_y + padding

        for bmp, px, py in draw_items:
            canvas.alpha_composite(bmp, (px + offset_x, py + offset_y))

        return canvas


class MultisManager:
    _instance: Optional['MultisManager'] = None

    def __init__(self):
        self._file_index: Optional[FileIndex] = None
        self._cache: Dict[int, MultiStructure] = {}
        self.max_multis = 0x2000
        self.reload()

    @classmethod
    def get_instance(cls) -> 'MultisManager':
        if cls._instance is None:
            cls._instance = MultisManager()
        return cls._instance

    def reload(self):
        if self._file_index:
            self._file_index.close()
        self._cache.clear()

        self._file_index = FileIndex(
            "multi.idx",
            "multi.mul",
            uop_file=None,
            max_entries=self.max_multis,
            file_id=14
        )

    def is_valid(self, multi_id: int) -> bool:
        if 0 <= multi_id < self.max_multis:
            if multi_id in self._cache:
                return True
            return self._file_index.is_valid(multi_id) if self._file_index else False
        return False

    def get_multi(self, multi_id: int) -> Optional[MultiStructure]:
        if multi_id < 0 or multi_id >= self.max_multis:
            return None
        if multi_id in self._cache:
            return self._cache[multi_id]

        if not self._file_index or not self._file_index.is_valid(multi_id):
            return None

        data = self._file_index.get_data(multi_id)
        if not data:
            return None

        # Check entry record size:
        # Classic entry: 2 (item) + 2 (x) + 2 (y) + 2 (z) + 4 (flags) = 12 bytes
        # High Seas entry: 12 + 4 (unk1) = 16 bytes
        record_size = 16 if len(data) % 16 == 0 and len(data) % 12 != 0 else 12
        count = len(data) // record_size

        comps = []
        for i in range(count):
            off = i * record_size
            if record_size == 16:
                item_id, ox, oy, oz, flags, unk1 = struct.unpack_from("<HhhhII", data, off)
            else:
                item_id, ox, oy, oz, flags = struct.unpack_from("<HhhhI", data, off)
                unk1 = 0
            comps.append(MultiComponent(item_id, ox, oy, oz, flags, unk1))

        structure = MultiStructure(multi_id, comps)
        self._cache[multi_id] = structure
        return structure
