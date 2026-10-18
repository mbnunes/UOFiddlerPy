"""
Radar color manager: reads, edits, calculates average colors, and saves radarcol.mul.
Used for minimaps and radar views in Ultima Online.
"""

import os
import struct
from typing import List, Optional
from PIL import Image
from uofiddler.core.files import FileManager
from uofiddler.core.colors import color16_to_rgba, rgba_to_color16


class RadarColManager:
    _instance: Optional['RadarColManager'] = None

    def __init__(self):
        self.colors: List[int] = [0] * 0x14000
        self.reload()

    @classmethod
    def get_instance(cls) -> 'RadarColManager':
        if cls._instance is None:
            cls._instance = RadarColManager()
        return cls._instance

    def reload(self):
        fm = FileManager.get_instance()
        path = fm.get_file_path("radarcol.mul")
        self.colors = [0] * 0x14000

        if not path or not os.path.exists(path):
            return

        with open(path, "rb") as f:
            data = f.read()

        count = len(data) // 2
        words = struct.unpack(f"<{count}H", data[:count * 2])
        self.colors = list(words)
        if len(self.colors) < 0x14000:
            self.colors.extend([0] * (0x14000 - len(self.colors)))

    def get_land_color(self, index: int) -> int:
        idx = index & 0x3FFF
        return self.colors[idx] if idx < len(self.colors) else 0

    def get_item_color(self, index: int) -> int:
        idx = index + 0x4000
        return self.colors[idx] if idx < len(self.colors) else 0

    def get_land_color_rgba(self, index: int) -> tuple[int, int, int, int]:
        c = self.get_land_color(index)
        return color16_to_rgba(c | 0x8000)

    def get_item_color_rgba(self, index: int) -> tuple[int, int, int, int]:
        c = self.get_item_color(index)
        return color16_to_rgba(c | 0x8000)

    def set_land_color(self, index: int, color16: int):
        idx = index & 0x3FFF
        if idx < len(self.colors):
            self.colors[idx] = color16 & 0x7FFF

    def set_item_color(self, index: int, color16: int):
        idx = index + 0x4000
        if idx < len(self.colors):
            self.colors[idx] = color16 & 0x7FFF

    @staticmethod
    def calculate_average_color(img: Image.Image) -> int:
        """
        Calculates the average 16-bit color of a tile image, ignoring transparent pixels.
        """
        img = img.convert("RGBA")
        pixels = img.load()
        w, h = img.size

        tot_r = 0
        tot_g = 0
        tot_b = 0
        count = 0

        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if a >= 128 and not (r == 0 and g == 0 and b == 0):
                    tot_r += r
                    tot_g += g
                    tot_b += b
                    count += 1

        if count == 0:
            return 0

        avg_r = tot_r // count
        avg_g = tot_g // count
        avg_b = tot_b // count

        return rgba_to_color16(avg_r, avg_g, avg_b) & 0x7FFF

    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            f.write(struct.pack(f"<{len(self.colors)}H", *self.colors))
