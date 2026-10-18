"""
Texture manager: reads, decodes, replaces, and saves terrain textures (texmaps.mul and texidx.mul).
Supports 64x64 (8192 bytes) and 128x128 (32768 bytes) 16-bit RGB555 textures.
"""

import struct
from typing import Optional, Dict
from PIL import Image
from uofiddler.core.file_index import FileIndex
from uofiddler.core.colors import color16_to_rgba, rgba_to_color16


class TextureManager:
    _instance: Optional['TextureManager'] = None

    def __init__(self):
        self._file_index: Optional[FileIndex] = None
        self._cache: Dict[int, Image.Image] = {}
        self._replaced: Dict[int, Image.Image] = {}
        self._removed: set[int] = set()
        self.max_textures = 0x4000
        self.reload()

    @classmethod
    def get_instance(cls) -> 'TextureManager':
        if cls._instance is None:
            cls._instance = TextureManager()
        return cls._instance

    def reload(self):
        if self._file_index:
            self._file_index.close()
        self._cache.clear()
        self._replaced.clear()
        self._removed.clear()

        self._file_index = FileIndex(
            "Texidx.mul",
            "Texmaps.mul",
            max_entries=self.max_textures,
            file_id=10
        )

    def is_valid(self, index: int) -> bool:
        idx = index & 0x3FFF
        if idx in self._removed:
            return False
        if idx in self._replaced or idx in self._cache:
            return True
        return self._file_index.is_valid(idx) if self._file_index else False

    def get_texture(self, index: int) -> Optional[Image.Image]:
        idx = index & 0x3FFF
        if idx in self._removed:
            return None
        if idx in self._replaced:
            return self._replaced[idx]
        if idx in self._cache:
            return self._cache[idx]

        if not self._file_index or not self._file_index.is_valid(idx):
            return None

        entry = self._file_index.entries[idx]
        data = self._file_index.get_data(idx)
        if not data:
            return None

        size = 128 if entry.extra != 0 or len(data) >= 32768 else 64
        expected_len = size * size * 2
        if len(data) < expected_len:
            return None

        words = struct.unpack(f"<{size * size}H", data[:expected_len])
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        pixels = img.load()

        i = 0
        for y in range(size):
            for x in range(size):
                pixels[x, y] = color16_to_rgba(words[i] | 0x8000)
                i += 1

        self._cache[idx] = img
        return img

    def replace(self, index: int, img: Image.Image):
        idx = index & 0x3FFF
        # Must be 64x64 or 128x128
        w, h = img.size
        size = 128 if w >= 96 or h >= 96 else 64
        self._replaced[idx] = img.resize((size, size)).convert("RGBA")
        self._cache.pop(idx, None)
        self._removed.discard(idx)

    def remove(self, index: int):
        idx = index & 0x3FFF
        self._removed.add(idx)
        self._replaced.pop(idx, None)
        self._cache.pop(idx, None)

    @staticmethod
    def encode_texture(img: Image.Image) -> tuple[bytes, int]:
        """
        Encodes a texture into raw 16-bit RGB555 words.
        Returns (data_bytes, extra) where extra=0 for 64x64, extra=1 for 128x128.
        """
        w, h = img.size
        size = 128 if w >= 96 or h >= 96 else 64
        img = img.resize((size, size)).convert("RGBA")
        pixels = img.load()

        words = []
        for y in range(size):
            for x in range(size):
                r, g, b, a = pixels[x, y]
                words.append(rgba_to_color16(r, g, b, a) & 0x7FFF)

        data = struct.pack(f"<{len(words)}H", *words)
        extra = 1 if size == 128 else 0
        return data, extra
