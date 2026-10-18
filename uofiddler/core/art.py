"""
Art loader, decoder, encoder, and saver for Land tiles and Static items.
Handles 16-bit ARGB1555 pixel conversions, RLE encoding/decoding, and UOP/MUL files.
"""

import struct
from typing import Optional, Dict
from PIL import Image
from uofiddler.core.file_index import FileIndex
from uofiddler.core.colors import color16_to_rgba, rgba_to_color16


class ArtManager:
    _instance: Optional['ArtManager'] = None

    def __init__(self):
        self._file_index: Optional[FileIndex] = None
        self._land_cache: Dict[int, Image.Image] = {}
        self._static_cache: Dict[int, Image.Image] = {}
        self._replaced_land: Dict[int, Image.Image] = {}
        self._replaced_static: Dict[int, Image.Image] = {}
        self._removed_land: set[int] = set()
        self._removed_static: set[int] = set()
        self.max_item_id = 0xFFFF
        self.reload()

    @classmethod
    def get_instance(cls) -> 'ArtManager':
        if cls._instance is None:
            cls._instance = ArtManager()
        return cls._instance

    def reload(self):
        if self._file_index:
            self._file_index.close()
        self._land_cache.clear()
        self._static_cache.clear()
        self._replaced_land.clear()
        self._replaced_static.clear()
        self._removed_land.clear()
        self._removed_static.clear()

        self._file_index = FileIndex(
            "Artidx.mul",
            "Art.mul",
            "artLegacyMUL.uop",
            max_entries=0x14000,
            file_id=4,
            uop_ext=".tga",
            has_extra=False
        )

    def is_valid_land(self, index: int) -> bool:
        idx = index & 0x3FFF
        if idx in self._removed_land:
            return False
        if idx in self._replaced_land or idx in self._land_cache:
            return True
        return self._file_index.is_valid(idx) if self._file_index else False

    def is_valid_static(self, index: int) -> bool:
        if index < 0 or index > self.max_item_id:
            return False
        if index in self._removed_static:
            return False
        if index in self._replaced_static or index in self._static_cache:
            return True
        raw_idx = index + 0x4000
        return self._file_index.is_valid(raw_idx) if self._file_index else False

    def get_land(self, index: int) -> Optional[Image.Image]:
        idx = index & 0x3FFF
        if idx in self._removed_land:
            return None
        if idx in self._replaced_land:
            return self._replaced_land[idx]
        if idx in self._land_cache:
            return self._land_cache[idx]

        if not self._file_index:
            return None

        data = self._file_index.get_data(idx)
        if not data or len(data) < 2048:
            return None

        img = self._decode_land(data)
        if img:
            self._land_cache[idx] = img
        return img

    def get_static(self, index: int) -> Optional[Image.Image]:
        if index < 0 or index > self.max_item_id:
            return None
        if index in self._removed_static:
            return None
        if index in self._replaced_static:
            return self._replaced_static[index]
        if index in self._static_cache:
            return self._static_cache[index]

        if not self._file_index:
            return None

        raw_idx = index + 0x4000
        data = self._file_index.get_data(raw_idx)
        if not data or len(data) < 8:
            return None

        img = self._decode_static(data)
        if img:
            self._static_cache[index] = img
        return img

    def replace_land(self, index: int, img: Image.Image):
        idx = index & 0x3FFF
        self._replaced_land[idx] = img.convert("RGBA")
        self._land_cache.pop(idx, None)
        self._removed_land.discard(idx)

    def replace_static(self, index: int, img: Image.Image):
        if 0 <= index <= self.max_item_id:
            self._replaced_static[index] = img.convert("RGBA")
            self._static_cache.pop(index, None)
            self._removed_static.discard(index)

    def remove_land(self, index: int):
        idx = index & 0x3FFF
        self._removed_land.add(idx)
        self._replaced_land.pop(idx, None)
        self._land_cache.pop(idx, None)

    def remove_static(self, index: int):
        if 0 <= index <= self.max_item_id:
            self._removed_static.add(index)
            self._replaced_static.pop(index, None)
            self._static_cache.pop(index, None)

    @staticmethod
    def _decode_land(data: bytes) -> Optional[Image.Image]:
        """
        Decodes a 44x44 diamond land tile from 2048 bytes of 16-bit RGB555 words.
        """
        words = struct.unpack(f"<{len(data) // 2}H", data[:2048])
        img = Image.new("RGBA", (44, 44), (0, 0, 0, 0))
        pixels = img.load()

        word_idx = 0
        x_offset = 21
        x_run = 2

        # Top half
        for y in range(22):
            for x in range(x_offset, x_offset + x_run):
                c = words[word_idx] | 0x8000
                word_idx += 1
                pixels[x, y] = color16_to_rgba(c)
            x_offset -= 1
            x_run += 2

        x_offset = 0
        x_run = 44
        # Bottom half
        for y in range(22, 44):
            for x in range(x_offset, x_offset + x_run):
                c = words[word_idx] | 0x8000
                word_idx += 1
                pixels[x, y] = color16_to_rgba(c)
            x_offset += 1
            x_run -= 2

        return img

    @staticmethod
    def _decode_static(data: bytes) -> Optional[Image.Image]:
        """
        Decodes an RLE-encoded static item into a PIL Image.
        """
        dummy, width, height = struct.unpack_from("<IHH", data, 0)
        if width <= 0 or height <= 0 or width > 1024 or height > 1024:
            return None

        word_count = len(data) // 2
        words = struct.unpack(f"<{word_count}H", data[:word_count * 2])

        if len(words) < 4 + height:
            return None

        lookups = [height + 4 + words[4 + i] for i in range(height)]
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        pixels = img.load()

        for y in range(height):
            count = lookups[y]
            x = 0
            while count + 1 < word_count:
                x_offset = words[count]
                x_run = words[count + 1]
                count += 2
                if x_offset + x_run == 0:
                    break
                x += x_offset
                if x + x_run > width:
                    break
                for r in range(x_run):
                    if count >= word_count:
                        break
                    c = words[count] ^ 0x8000
                    count += 1
                    pixels[x + r, y] = color16_to_rgba(c)
                x += x_run

        return img

    @staticmethod
    def encode_land(img: Image.Image) -> bytes:
        """
        Encodes a 44x44 image into 2048 bytes of land tile MUL data.
        """
        img = img.resize((44, 44)).convert("RGBA")
        pixels = img.load()
        out_words = []

        x_offset = 21
        x_run = 2
        for y in range(22):
            for x in range(x_offset, x_offset + x_run):
                r, g, b, a = pixels[x, y]
                out_words.append(rgba_to_color16(r, g, b, a) & 0x7FFF)
            x_offset -= 1
            x_run += 2

        x_offset = 0
        x_run = 44
        for y in range(22, 44):
            for x in range(x_offset, x_offset + x_run):
                r, g, b, a = pixels[x, y]
                out_words.append(rgba_to_color16(r, g, b, a) & 0x7FFF)
            x_offset += 1
            x_run -= 2

        # Pad to 1024 words (2048 bytes)
        while len(out_words) < 1024:
            out_words.append(0)

        return struct.pack(f"<{len(out_words)}H", *out_words)

    @staticmethod
    def encode_static(img: Image.Image) -> bytes:
        """
        Encodes a PIL Image into UO Static RLE MUL binary format.
        """
        img = img.convert("RGBA")
        width, height = img.size
        pixels = img.load()

        row_data = []
        lookups = []
        current_offset = 0

        for y in range(height):
            lookups.append(current_offset)
            x = 0
            while x < width:
                # Skip transparent pixels
                run_start = x
                while x < width and pixels[x, y][3] < 128:
                    x += 1
                x_offset = x - run_start

                if x >= width:
                    break

                # Count opaque pixels
                opaque_start = x
                opaque_pixels = []
                while x < width and pixels[x, y][3] >= 128:
                    r, g, b, a = pixels[x, y]
                    opaque_pixels.append(rgba_to_color16(r, g, b, a) ^ 0x8000)
                    x += 1

                x_run = len(opaque_pixels)
                row_data.append(x_offset)
                row_data.append(x_run)
                row_data.extend(opaque_pixels)
                current_offset += 2 + x_run

            # End of line marker
            row_data.append(0)
            row_data.append(0)
            current_offset += 2

        # Header: dummy (uint32 = 0), width (uint16), height (uint16)
        header = struct.pack("<IHH", 0, width, height)
        lookups_bin = struct.pack(f"<{len(lookups)}H", *lookups)
        data_bin = struct.pack(f"<{len(row_data)}H", *row_data)

        return header + lookups_bin + data_bin
