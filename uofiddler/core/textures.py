import os
import io
import struct
import zlib
from dataclasses import dataclass
from typing import Optional, Dict, List
from PIL import Image
from uofiddler.core.file_index import FileIndex
from uofiddler.core.files import FileManager
from uofiddler.core.colors import color16_to_rgba, rgba_to_color16


@dataclass
class ECTextureEntry:
    index: int
    offset: int
    compressed_len: int
    decompressed_len: int
    compression: int
    hash: int


class TextureManager:
    _instance: Optional['TextureManager'] = None

    def __init__(self):
        self._file_index: Optional[FileIndex] = None
        self._cache: Dict[int, Image.Image] = {}
        self._replaced: Dict[int, Image.Image] = {}
        self._removed: set[int] = set()
        self.max_textures = 0x4000
        self.client_mode: str = "classic"  # 'classic', 'enhanced_legacy', 'enhanced_3d'
        self._ec_entries: List[ECTextureEntry] = []
        self._ec_stream = None
        self.reload()

    @classmethod
    def get_instance(cls) -> 'TextureManager':
        if cls._instance is None:
            cls._instance = TextureManager()
        return cls._instance

    def set_client_mode(self, mode: str):
        if mode not in ("classic", "enhanced_legacy", "enhanced_3d"):
            raise ValueError(f"Invalid texture client mode: {mode}")
        if self.client_mode != mode:
            self.client_mode = mode
            self.reload()

    def get_count(self) -> int:
        if self.client_mode in ("enhanced_legacy", "enhanced_3d"):
            return len(self._ec_entries)
        return self.max_textures

    def reload(self):
        if self._file_index:
            self._file_index.close()
            self._file_index = None
        if self._ec_stream:
            try:
                self._ec_stream.close()
            except Exception:
                pass
            self._ec_stream = None

        self._cache.clear()
        self._replaced.clear()
        self._removed.clear()
        self._ec_entries.clear()

        fm = FileManager.get_instance()

        if self.client_mode == "enhanced_legacy":
            p_ec = fm.get_ec_file_path("LegacyTexture.uop")
            if p_ec and os.path.exists(p_ec):
                self._load_ec_uop(p_ec)
        elif self.client_mode == "enhanced_3d":
            p_ec = fm.get_ec_file_path("Texture.uop")
            if p_ec and os.path.exists(p_ec):
                self._load_ec_uop(p_ec)
        else:
            self._file_index = FileIndex(
                "Texidx.mul",
                "Texmaps.mul",
                max_entries=self.max_textures,
                file_id=10
            )

    def _load_ec_uop(self, uop_path: str):
        try:
            self._ec_stream = open(uop_path, "rb")
            hdr = self._ec_stream.read(28)
            if len(hdr) < 28:
                return
            magic, ver, sig, next_block, cap, count = struct.unpack("<IIIQII", hdr)
            if magic != 0x50594D:
                return

            idx = 0
            while next_block != 0:
                self._ec_stream.seek(next_block)
                block_hdr = self._ec_stream.read(12)
                if len(block_hdr) < 12:
                    break
                f_count, next_block = struct.unpack("<IQ", block_hdr)

                for _ in range(f_count):
                    entry_raw = self._ec_stream.read(34)
                    if len(entry_raw) < 34:
                        break
                    offset, h_len, c_len, d_len, h, crc, comp = struct.unpack("<QIIIQIH", entry_raw)
                    if offset != 0:
                        self._ec_entries.append(ECTextureEntry(
                            index=idx,
                            offset=offset + h_len,
                            compressed_len=c_len,
                            decompressed_len=d_len,
                            compression=comp,
                            hash=h
                        ))
                        idx += 1
        except Exception as e:
            print(f"[TextureManager] Failed to load EC UOP {uop_path}: {e}")

    def is_valid(self, index: int) -> bool:
        if self.client_mode in ("enhanced_legacy", "enhanced_3d"):
            return 0 <= index < len(self._ec_entries)
        idx = index & 0x3FFF
        if idx in self._removed:
            return False
        if idx in self._replaced or idx in self._cache:
            return True
        return self._file_index.is_valid(idx) if self._file_index else False

    def get_texture(self, index: int) -> Optional[Image.Image]:
        if self.client_mode in ("enhanced_legacy", "enhanced_3d"):
            if index in self._replaced:
                return self._replaced[index]
            if index in self._cache:
                return self._cache[index]
            if not self._ec_stream or index < 0 or index >= len(self._ec_entries):
                return None
            e = self._ec_entries[index]
            try:
                self._ec_stream.seek(e.offset)
                raw = self._ec_stream.read(e.compressed_len)
                data = zlib.decompress(raw) if e.compression == 1 else raw
                img = Image.open(io.BytesIO(data)).convert("RGBA")
                self._cache[index] = img
                return img
            except Exception:
                return None

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
