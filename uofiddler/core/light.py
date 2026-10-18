"""
Light manager: reads, decodes, and previews light masks from light.mul and lightidx.mul.
"""

from typing import Optional, Dict
from PIL import Image
from uofiddler.core.file_index import FileIndex


class LightManager:
    _instance: Optional['LightManager'] = None

    def __init__(self):
        self._file_index: Optional[FileIndex] = None
        self._cache: Dict[int, Image.Image] = {}
        self.max_lights = 100
        self.reload()

    @classmethod
    def get_instance(cls) -> 'LightManager':
        if cls._instance is None:
            cls._instance = LightManager()
        return cls._instance

    def reload(self):
        if self._file_index:
            self._file_index.close()
        self._cache.clear()
        self._file_index = FileIndex("lightidx.mul", "light.mul", max_entries=self.max_lights)

    def is_valid(self, index: int) -> bool:
        if 0 <= index < self.max_lights:
            if self._file_index and self._file_index.is_valid(index):
                extra = self._file_index.entries[index].extra
                w = extra & 0xFFFF
                h = (extra >> 16) & 0xFFFF
                return w > 0 and h > 0
        return False

    def get_light(self, index: int) -> Optional[Image.Image]:
        if index < 0 or index >= self.max_lights:
            return None
        if index in self._cache:
            return self._cache[index]

        if not self._file_index or not self._file_index.is_valid(index):
            return None

        entry = self._file_index.entries[index]
        width = entry.extra & 0xFFFF
        height = (entry.extra >> 16) & 0xFFFF
        if width <= 0 or height <= 0:
            return None

        data = self._file_index.get_data(index)
        if not data or len(data) < width * height:
            return None

        # Each byte is intensity 0..31. We convert to 0..255 for viewing
        img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        pixels = img.load()

        i = 0
        for y in range(height):
            for x in range(width):
                val = data[i]
                # Light glow: yellow-white tint based on intensity
                intensity = min(255, val * 8)
                pixels[x, y] = (intensity, intensity, intensity // 2, 255)
                i += 1

        self._cache[index] = img
        return img
