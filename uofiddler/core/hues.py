"""
Hues manager: Reads, modifies, applies, and saves hues.mul.
Supports 3000 hues, each with 32 16-bit colors, start/end table markers, and names.
Provides fast hueing for PIL Images (both normal and partial gray-pixel hueing).
"""

import os
import struct
from typing import List, Optional
from dataclasses import dataclass
from PIL import Image
from uofiddler.core.files import FileManager
from uofiddler.core.colors import color16_to_rgba, rgba_to_color16, COLOR_5_TO_8, COLOR_8_TO_5


@dataclass
class Hue:
    index: int
    colors: List[int]  # 32 16-bit RGB555 colors
    table_start: int = 0
    table_end: int = 0
    name: str = ""

    def get_rgba_colors(self) -> List[tuple[int, int, int, int]]:
        return [color16_to_rgba(c | 0x8000) for c in self.colors]

    def apply_to(self, img: Image.Image, only_gray: bool = False) -> Image.Image:
        """
        Applies this hue to a PIL RGBA image.
        If only_gray is True, only pixels where R == G == B (partial hue) are tinted.
        Uses native C accelerator when available, falling back to pure Python.
        """
        if not self.colors or len(self.colors) < 32:
            return img

        try:
            from uofiddler.native import HAS_NATIVE_CORE, native_apply_hue
            if HAS_NATIVE_CORE:
                return native_apply_hue(img, self.colors, only_gray=only_gray)
        except Exception:
            pass

        out = img.copy().convert("RGBA")
        pixels = out.load()
        width, height = out.size

        # Precompute RGB tuples for the 32 palette colors
        palette = self.get_rgba_colors()

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a == 0 or (r == 0 and g == 0 and b == 0):
                    continue

                if only_gray:
                    # Partial hue: only tint if pixel is grayscale (r == g == b)
                    if r == g == b:
                        # Map 5-bit brightness to palette index 0..31
                        idx = COLOR_8_TO_5[r]
                        pr, pg, pb, _ = palette[idx]
                        pixels[x, y] = (pr, pg, pb, a)
                else:
                    # Normal hue: map red (or brightness) to palette index
                    idx = COLOR_8_TO_5[r]
                    pr, pg, pb, _ = palette[idx]
                    pixels[x, y] = (pr, pg, pb, a)

        return out


class HuesManager:
    _instance: Optional['HuesManager'] = None

    def __init__(self):
        self.hues: List[Hue] = [Hue(index=i, colors=[0] * 32) for i in range(3000)]
        self._headers: List[int] = []
        self.reload()

    @classmethod
    def get_instance(cls) -> 'HuesManager':
        if cls._instance is None:
            cls._instance = HuesManager()
        return cls._instance

    def reload(self):
        fm = FileManager.get_instance()
        path = fm.get_file_path("hues.mul")
        self.hues = [Hue(index=i, colors=[0] * 32) for i in range(3000)]
        self._headers = []

        if not path or not os.path.exists(path):
            return

        with open(path, "rb") as f:
            data = f.read()

        block_count = len(data) // 708
        if block_count > 375:
            block_count = 375

        offset = 0
        hue_idx = 0

        for block in range(block_count):
            header = struct.unpack_from("<i", data, offset)[0]
            self._headers.append(header)
            offset += 4

            for _ in range(8):
                if offset + 88 > len(data):
                    break
                colors = list(struct.unpack_from("<32H", data, offset))
                offset += 64
                t_start, t_end = struct.unpack_from("<HH", data, offset)
                offset += 4
                raw_name = data[offset: offset + 20]
                offset += 20

                name = raw_name.split(b"\x00")[0].decode("ascii", errors="replace")
                if hue_idx < len(self.hues):
                    self.hues[hue_idx] = Hue(
                        index=hue_idx,
                        colors=colors,
                        table_start=t_start,
                        table_end=t_end,
                        name=name
                    )
                hue_idx += 1

    def get_hue(self, index: int) -> Optional[Hue]:
        idx = index & 0x3FFF
        if 0 <= idx < len(self.hues):
            return self.hues[idx]
        return self.hues[0] if self.hues else None

    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            hue_idx = 0
            for b in range(375):
                header = self._headers[b] if b < len(self._headers) else 0
                f.write(struct.pack("<i", header))

                for _ in range(8):
                    hue = self.hues[hue_idx] if hue_idx < len(self.hues) else Hue(hue_idx, [0] * 32)
                    colors = hue.colors if len(hue.colors) == 32 else (hue.colors + [0] * 32)[:32]
                    f.write(struct.pack("<32H", *colors))
                    f.write(struct.pack("<HH", hue.table_start, hue.table_end))
                    name_bytes = hue.name.encode("ascii", errors="replace")[:20]
                    f.write(name_bytes.ljust(20, b"\x00"))
                    hue_idx += 1
