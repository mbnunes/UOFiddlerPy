"""
FileIndex: Generic binary index reader supporting both classic (.idx + .mul) and Mythic Package (.uop) files.
"""

import os
import struct
import zlib
from typing import Optional, List, Dict
from dataclasses import dataclass
from uofiddler.core.files import FileManager
from uofiddler.core.hash_utils import hash_file_name


@dataclass
class IndexEntry:
    lookup: int = -1
    length: int = -1
    extra: int = 0
    decompressed_length: int = 0
    compression: int = 0  # 0 = None, 1 = Zlib

    @property
    def is_valid(self) -> bool:
        return self.lookup >= 0 and self.length > 0


class FileIndex:
    def __init__(
        self,
        idx_file: Optional[str] = None,
        mul_file: Optional[str] = None,
        uop_file: Optional[str] = None,
        max_entries: int = 0x14000,
        file_id: int = -1,
        uop_ext: str = ".dat",
        has_extra: bool = False,
        direct_path: Optional[str] = None
    ):
        self.idx_file = idx_file
        self.mul_file = mul_file
        self.uop_file = uop_file
        self.max_entries = max_entries
        self.file_id = file_id
        self.uop_ext = uop_ext
        self.has_extra = has_extra
        self.direct_path = direct_path

        self.entries: List[IndexEntry] = [IndexEntry() for _ in range(max_entries)]
        self.mul_path: Optional[str] = None
        self._mul_stream = None
        self._is_uop = False

        self.reload()

    def reload(self):
        if self._mul_stream:
            try:
                self._mul_stream.close()
            except Exception:
                pass
            self._mul_stream = None

        fm = FileManager.get_instance()
        self.entries = [IndexEntry() for _ in range(self.max_entries)]

        # 1. Direct path if supplied
        if self.direct_path and os.path.exists(self.direct_path):
            if self.direct_path.lower().endswith(".uop"):
                try:
                    self._load_uop(self.direct_path)
                    self.mul_path = self.direct_path
                    self._mul_stream = open(self.direct_path, "rb")
                    self._is_uop = True
                    return
                except Exception as e:
                    print(f"[FileIndex] Failed to parse direct UOP {self.direct_path}: {e}")

        # 2. Check UOP file (Classic dir first, then EC dir)
        uop_path = None
        if self.uop_file:
            if os.path.exists(self.uop_file):
                uop_path = self.uop_file
            else:
                uop_path = fm.get_file_path(self.uop_file) or fm.get_ec_file_path(self.uop_file)

        if uop_path and os.path.exists(uop_path):
            try:
                self._load_uop(uop_path)
                self.mul_path = uop_path
                self._mul_stream = open(uop_path, "rb")
                self._is_uop = True
                return
            except Exception as e:
                print(f"[FileIndex] Failed to parse UOP {uop_path}: {e}")

        # 3. Fallback to MUL + IDX
        idx_path = fm.get_file_path(self.idx_file) if self.idx_file else None
        mul_path = fm.get_file_path(self.mul_file) if self.mul_file else None

        if idx_path and mul_path and os.path.exists(idx_path) and os.path.exists(mul_path):
            try:
                self._load_mul(idx_path, mul_path)
                self.mul_path = mul_path
                self._mul_stream = open(mul_path, "rb")
                self._is_uop = False
                return
            except Exception as e:
                print(f"[FileIndex] Failed to parse MUL/IDX: {e}")

    def _load_mul(self, idx_path: str, mul_path: str):
        size = os.path.getsize(idx_path)
        count = size // 12
        with open(idx_path, "rb") as f:
            for i in range(min(count, self.max_entries)):
                raw = f.read(12)
                if len(raw) < 12:
                    break
                lookup, length, extra = struct.unpack("<iii", raw)
                self.entries[i] = IndexEntry(
                    lookup=lookup,
                    length=length,
                    extra=extra,
                    decompressed_length=length,
                    compression=0
                )

    def _load_uop(self, uop_path: str):
        basename = os.path.splitext(os.path.basename(uop_path))[0].lower()
        with open(uop_path, "rb") as f:
            magic, ver, sig, next_block, block_size, count = struct.unpack("<IIIQII", f.read(28))
            if magic != 0x50594D:
                raise ValueError(f"Invalid UOP magic: 0x{magic:X}")

            # Precompute hashes for pattern: build/{basename}/{i:08d}{uop_ext}
            hashes: Dict[int, int] = {}
            for i in range(self.max_entries):
                entry_name = f"build/{basename}/{i:08d}{self.uop_ext}"
                h = hash_file_name(entry_name)
                hashes[h] = i

            f.seek(next_block)
            while next_block != 0:
                block_data = f.read(12)
                if len(block_data) < 12:
                    break
                files_count, next_block = struct.unpack("<IQ", block_data)

                for _ in range(files_count):
                    entry_raw = f.read(34)
                    if len(entry_raw) < 34:
                        break
                    offset, h_len, c_len, d_len, h, d_hash, flag = struct.unpack("<QIIIQIH", entry_raw)
                    if offset == 0:
                        continue
                    if h in hashes:
                        idx = hashes[h]
                        self.entries[idx] = IndexEntry(
                            lookup=offset + h_len,
                            length=c_len,
                            extra=0,
                            decompressed_length=d_len,
                            compression=flag
                        )

                if next_block != 0:
                    f.seek(next_block)

    def is_valid(self, index: int) -> bool:
        if 0 <= index < len(self.entries):
            return self.entries[index].is_valid
        return False

    def get_data(self, index: int) -> Optional[bytes]:
        """
        Reads and returns the decompressed payload bytes for index.
        """
        if not self.is_valid(index) or not self._mul_stream:
            return None

        entry = self.entries[index]
        self._mul_stream.seek(entry.lookup)
        raw = self._mul_stream.read(entry.length)
        if len(raw) < entry.length:
            return None

        if entry.compression in (1, 3):
            try:
                decomp = zlib.decompress(raw)
            except Exception as e:
                print(f"[FileIndex] Zlib decompress failed for index {index}: {e}")
                return None

            if entry.compression == 3:
                try:
                    from uofiddler.core.mythic import MythicDecompress
                    return MythicDecompress.decompress(decomp)
                except Exception as e:
                    print(f"[FileIndex] Mythic decompress failed for index {index}: {e}")
                    return None
            return decomp

        return raw

    def close(self):
        if self._mul_stream:
            try:
                self._mul_stream.close()
            except Exception:
                pass
            self._mul_stream = None
