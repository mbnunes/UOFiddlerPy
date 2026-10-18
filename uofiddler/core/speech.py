"""
Speech manager: Reads, modifies, and saves speech.mul entries.
Uses big-endian IDs and UTF-8 keywords.
"""

import os
import struct
from typing import List, Optional
from dataclasses import dataclass
from uofiddler.core.files import FileManager


@dataclass
class SpeechEntry:
    entry_id: int
    keyword: str
    order: int


class SpeechManager:
    _instance: Optional['SpeechManager'] = None

    def __init__(self):
        self.entries: List[SpeechEntry] = []
        self.reload()

    @classmethod
    def get_instance(cls) -> 'SpeechManager':
        if cls._instance is None:
            cls._instance = SpeechManager()
        return cls._instance

    def reload(self):
        fm = FileManager.get_instance()
        path = fm.get_file_path("speech.mul")
        self.entries.clear()

        if not path or not os.path.exists(path):
            return

        with open(path, "rb") as f:
            data = f.read()

        offset = 0
        order = 0
        while offset + 4 <= len(data):
            entry_id, length = struct.unpack_from(">hh", data, offset)
            offset += 4

            if length > 256:
                length = 256
            if offset + length > len(data):
                break

            raw = data[offset: offset + length]
            offset += length

            keyword = raw.decode("utf-8", errors="replace")
            self.entries.append(SpeechEntry(entry_id=entry_id, keyword=keyword, order=order))
            order += 1

    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            for e in self.entries:
                kw_bytes = e.keyword.encode("utf-8")
                f.write(struct.pack(">hh", e.entry_id, len(kw_bytes)))
                f.write(kw_bytes)
