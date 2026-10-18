"""
Font manager: Reads and renders ASCII (fonts.mul) and Unicode (unifont*.mul) fonts.
"""

import os
import struct
from typing import List, Optional
from PIL import Image
from uofiddler.core.files import FileManager
from uofiddler.core.colors import color16_to_rgba


class AsciiFont:
    def __init__(self, header: int):
        self.header = header
        self.height = 0
        self.characters: List[Optional[Image.Image]] = [None] * 224
        self.unk: List[int] = [0] * 224

    def get_character(self, ch: str) -> Optional[Image.Image]:
        code = ord(ch) - 0x20
        if 0 <= code < 224:
            return self.characters[code]
        return None

    def render_text(self, text: str) -> Optional[Image.Image]:
        glyphs = [self.get_character(c) for c in text]
        valid_glyphs = [g for g in glyphs if g is not None]
        if not valid_glyphs:
            return None

        total_width = sum(g.width for g in valid_glyphs)
        max_height = max(g.height for g in valid_glyphs)

        out = Image.new("RGBA", (total_width, max_height), (0, 0, 0, 0))
        cur_x = 0
        for g in valid_glyphs:
            out.paste(g, (cur_x, max_height - g.height))
            cur_x += g.width

        return out


class FontsManager:
    _instance: Optional['FontsManager'] = None

    def __init__(self):
        self.ascii_fonts: List[Optional[AsciiFont]] = [None] * 10
        self.reload()

    @classmethod
    def get_instance(cls) -> 'FontsManager':
        if cls._instance is None:
            cls._instance = FontsManager()
        return cls._instance

    def reload(self):
        fm = FileManager.get_instance()
        path = fm.get_file_path("fonts.mul")
        self.ascii_fonts = [None] * 10

        if not path or not os.path.exists(path):
            return

        with open(path, "rb") as f:
            data = f.read()

        offset = 0
        for i in range(10):
            if offset >= len(data):
                break
            header = data[offset]
            offset += 1
            font = AsciiFont(header)

            for k in range(224):
                if offset + 3 > len(data):
                    break
                w = data[offset]
                h = data[offset + 1]
                unk = data[offset + 2]
                offset += 3

                if w <= 0 or h <= 0:
                    continue

                if h > font.height and k < 96:
                    font.height = h

                pixel_bytes = w * h * 2
                if offset + pixel_bytes > len(data):
                    break

                words = struct.unpack_from(f"<{w * h}H", data, offset)
                offset += pixel_bytes

                img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                pixels = img.load()

                pidx = 0
                for y in range(h):
                    for x in range(w):
                        c = words[pidx]
                        pidx += 1
                        if c != 0:
                            pixels[x, y] = color16_to_rgba(c ^ 0x8000)

                font.characters[k] = img
                font.unk[k] = unk

            self.ascii_fonts[i] = font
