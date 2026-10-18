"""
Animdata manager: reads, edits, and saves animdata.mul.
Defines frame offsets, intervals, and start delays for animated static items.
"""

import os
import struct
from typing import Dict, List, Optional
from dataclasses import dataclass
from uofiddler.core.files import FileManager


@dataclass
class AnimDataEntry:
    item_id: int
    frames: List[int]  # 64 signed byte offsets
    unk: int
    frame_count: int
    frame_interval: int
    frame_start: int


class AnimDataManager:
    _instance: Optional['AnimDataManager'] = None

    def __init__(self):
        self.entries: Dict[int, AnimDataEntry] = {}
        self._headers: List[int] = []
        self._unknown_tail: bytes = b""
        self.reload()

    @classmethod
    def get_instance(cls) -> 'AnimDataManager':
        if cls._instance is None:
            cls._instance = AnimDataManager()
        return cls._instance

    def reload(self):
        fm = FileManager.get_instance()
        path = fm.get_file_path("animdata.mul")
        self.entries.clear()
        self._headers.clear()

        if not path or not os.path.exists(path):
            return

        with open(path, "rb") as f:
            data = f.read()

        chunk_size = 4 + 8 * 68  # 548 bytes per chunk
        num_chunks = len(data) // chunk_size
        offset = 0
        tile_id = 0

        for _ in range(num_chunks):
            header = struct.unpack_from("<i", data, offset)[0]
            self._headers.append(header)
            offset += 4

            for _ in range(8):
                frames = list(struct.unpack_from("<64b", data, offset))
                offset += 64
                unk, count, interval, start = struct.unpack_from("<BBBB", data, offset)
                offset += 4

                if count > 0:
                    self.entries[tile_id] = AnimDataEntry(
                        item_id=tile_id,
                        frames=frames,
                        unk=unk,
                        frame_count=count,
                        frame_interval=interval,
                        frame_start=start
                    )
                tile_id += 1

        if offset < len(data):
            self._unknown_tail = data[offset:]

    def get_anim_data(self, item_id: int) -> Optional[AnimDataEntry]:
        return self.entries.get(item_id)

    def set_anim_data(self, entry: AnimDataEntry):
        self.entries[entry.item_id] = entry

    def save(self, filepath: str):
        total_tiles = 0x8000
        total_chunks = total_tiles // 8

        with open(filepath, "wb") as f:
            tile_id = 0
            for chunk_idx in range(total_chunks):
                h = self._headers[chunk_idx] if chunk_idx < len(self._headers) else 0
                f.write(struct.pack("<i", h))

                for _ in range(8):
                    entry = self.entries.get(tile_id)
                    if entry:
                        frames = (entry.frames + [0] * 64)[:64]
                        f.write(struct.pack("<64b", *frames))
                        f.write(struct.pack("<BBBB", entry.unk, entry.frame_count, entry.frame_interval, entry.frame_start))
                    else:
                        f.write(b"\x00" * 68)
                    tile_id += 1

            if self._unknown_tail:
                f.write(self._unknown_tail)
