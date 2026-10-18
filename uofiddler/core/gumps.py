"""
Gump art loader, decoder, encoder, and saver for UO Gump images.
Supports classic gumpart.mul / gumpidx.mul and modern gumpartLegacyMUL.uop.
"""

import struct
from typing import Optional, Dict
from PIL import Image
from uofiddler.core.file_index import FileIndex
from uofiddler.core.colors import color16_to_rgba, rgba_to_color16


class GumpManager:
    _instance: Optional['GumpManager'] = None

    def __init__(self):
        self._file_index: Optional[FileIndex] = None
        self._cache: Dict[int, Image.Image] = {}
        self._replaced: Dict[int, Image.Image] = {}
        self._removed: set[int] = set()
        self.max_gump_id = 0xFFFF
        self.reload()

    @classmethod
    def get_instance(cls) -> 'GumpManager':
        if cls._instance is None:
            cls._instance = GumpManager()
        return cls._instance

    def reload(self):
        if self._file_index:
            self._file_index.close()
        self._cache.clear()
        self._replaced.clear()
        self._removed.clear()

        self._file_index = FileIndex(
            "Gumpidx.mul",
            "Gumpart.mul",
            "gumpartLegacyMUL.uop",
            max_entries=0x10000,
            file_id=12,
            uop_ext=".tga",
            has_extra=True
        )

    def is_valid(self, index: int) -> bool:
        if index < 0 or index > self.max_gump_id:
            return False
        if index in self._removed:
            return False
        if index in self._replaced or index in self._cache:
            return True
        return self._file_index.is_valid(index) if self._file_index else False

    def get_gump(self, index: int) -> Optional[Image.Image]:
        if index < 0 or index > self.max_gump_id:
            return None
        if index in self._removed:
            return None
        if index in self._replaced:
            return self._replaced[index]
        if index in self._cache:
            return self._cache[index]

        if not self._file_index or not self._file_index.is_valid(index):
            return None

        entry = self._file_index.entries[index]
        data = self._file_index.get_data(index)
        if not data or len(data) <= 8:
            return None

        # Determine width and height
        if self._file_index._is_uop or entry.compression == 1:
            # UOP has 8-byte width/height header: [4 bytes width, 4 bytes height]
            width, height = struct.unpack_from("<II", data, 0)
            payload = data[8:]
        else:
            width = (entry.extra >> 16) & 0xFFFF
            height = entry.extra & 0xFFFF
            payload = data

        if width <= 0 or height <= 0 or width > 4096 or height > 4096:
            return None

        img = self._decode_gump(payload, width, height)
        if img:
            self._cache[index] = img
        return img

    @staticmethod
    def _decode_gump(payload: bytes, width: int, height: int) -> Optional[Image.Image]:
        word_count = len(payload) // 2
        if word_count < height * 2:
            return None

        # Lookup table has 'height' 32-bit integers
        lookups = struct.unpack_from(f"<{height}I", payload, 0)
        words = struct.unpack(f"<{word_count}H", payload[:word_count * 2])

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        pixels = img.load()

        for y in range(height):
            # In UO gumps, each lookup offset is in 32-bit units, so in 16-bit words: offset * 2
            count = lookups[y] * 2
            x = 0
            while x < width and count + 1 < word_count:
                color = words[count]
                run = words[count + 1]
                count += 2

                if color == 0:
                    x += run
                else:
                    rgba = color16_to_rgba(color ^ 0x8000)
                    for r in range(run):
                        if x + r < width:
                            pixels[x + r, y] = rgba
                    x += run

        return img

    @staticmethod
    def encode_gump(img: Image.Image) -> tuple[bytes, int, int]:
        """
        Encodes a PIL Image into UO Gump RLE binary format.
        Returns (data_bytes, width, height).
        """
        img = img.convert("RGBA")
        width, height = img.size
        pixels = img.load()

        row_words = []
        lookups = []
        current_offset = height * 2  # lookup table size in 16-bit words

        for y in range(height):
            # Lookup in 32-bit units
            lookups.append(current_offset // 2)
            x = 0
            while x < width:
                # Transparent run
                if pixels[x, y][3] < 128:
                    trans_start = x
                    while x < width and pixels[x, y][3] < 128:
                        x += 1
                    run = x - trans_start
                    row_words.append(0)  # color 0 = transparent
                    row_words.append(run)
                    current_offset += 2
                else:
                    # Colored run
                    color_c = rgba_to_color16(*pixels[x, y]) ^ 0x8000
                    color_start = x
                    while x < width and pixels[x, y][3] >= 128 and (rgba_to_color16(*pixels[x, y]) ^ 0x8000) == color_c:
                        x += 1
                    run = x - color_start
                    row_words.append(color_c)
                    row_words.append(run)
                    current_offset += 2

        lookups_bin = struct.pack(f"<{len(lookups)}I", *lookups)
        data_bin = struct.pack(f"<{len(row_words)}H", *row_words)
        return lookups_bin + data_bin, width, height

    def replace_gump(self, index: int, img: Image.Image):
        if 0 <= index <= self.max_gump_id:
            self._replaced[index] = img.convert("RGBA")
            self._cache.pop(index, None)
            self._removed.discard(index)

    def remove_gump(self, index: int):
        if 0 <= index <= self.max_gump_id:
            self._removed.add(index)
            self._replaced.pop(index, None)
            self._cache.pop(index, None)
