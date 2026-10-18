"""
Cliloc localization manager: reads, searches, modifies, and saves cliloc.* files (e.g. cliloc.enu).
"""

import os
import struct
from typing import List, Dict, Optional
from dataclasses import dataclass
from uofiddler.core.files import FileManager
from uofiddler.core.mythic import MythicDecompress


@dataclass
class ClilocEntry:
    number: int
    flag: int
    text: str


class ClilocManager:
    _instance: Optional['ClilocManager'] = None

    def __init__(self, lang: str = "enu"):
        self.lang = lang
        self.entries: List[ClilocEntry] = []
        self._entry_map: Dict[int, ClilocEntry] = {}
        self._header1: int = 0
        self._header2: int = 0
        self.reload()

    @classmethod
    def get_instance(cls) -> 'ClilocManager':
        if cls._instance is None:
            cls._instance = ClilocManager()
        return cls._instance

    def reload(self):
        fm = FileManager.get_instance()
        path = fm.get_file_path(f"cliloc.{self.lang}")
        self.entries.clear()
        self._entry_map.clear()

        if not path or not os.path.exists(path):
            return

        with open(path, "rb") as f:
            data = f.read()

        if len(data) < 6:
            return

        # Check if compressed with Mythic
        if not (data[0] == 0 or data[1] == 0 or data[2] == 0 or data[3] == 0):
            try:
                data = MythicDecompress.decompress(data)
            except Exception:
                pass

        if len(data) < 6:
            return

        self._header1, self._header2 = struct.unpack_from("<ih", data, 0)
        cursor = 6

        while cursor + 7 <= len(data):
            number, flag, text_len = struct.unpack_from("<iBH", data, cursor)
            cursor += 7

            if cursor + text_len > len(data):
                break

            raw_text = data[cursor: cursor + text_len]
            cursor += text_len

            try:
                text = raw_text.decode("utf-8")
            except Exception:
                text = raw_text.decode("latin1", errors="replace")

            entry = ClilocEntry(number=number, flag=flag, text=text)
            self.entries.append(entry)
            self._entry_map[number] = entry

    def get_string(self, number: int) -> Optional[str]:
        entry = self._entry_map.get(number)
        return entry.text if entry else None

    def set_entry(self, number: int, text: str, flag: int = 0):
        if number in self._entry_map:
            entry = self._entry_map[number]
            entry.text = text
            entry.flag = flag
        else:
            entry = ClilocEntry(number=number, flag=flag, text=text)
            self.entries.append(entry)
            self._entry_map[number] = entry

    def remove_entry(self, number: int):
        if number in self._entry_map:
            entry = self._entry_map.pop(number)
            self.entries.remove(entry)

    def search(self, query: str) -> List[ClilocEntry]:
        q = query.lower()
        results = []
        for e in self.entries:
            if q in str(e.number) or q in e.text.lower():
                results.append(e)
        return results

    def save(self, filepath: str):
        self.entries.sort(key=lambda e: e.number)
        with open(filepath, "wb") as f:
            f.write(struct.pack("<ih", self._header1, self._header2))
            for e in self.entries:
                text_bytes = e.text.encode("utf-8")
                f.write(struct.pack("<iBH", e.number, e.flag, len(text_bytes)))
                f.write(text_bytes)
