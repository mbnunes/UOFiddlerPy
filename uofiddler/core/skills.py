"""
Skills and skill groups manager: skills.mul, skills.idx, and skillgrp.mul.
"""

import os
import struct
from typing import List, Optional
from dataclasses import dataclass
from uofiddler.core.files import FileManager
from uofiddler.core.file_index import FileIndex


@dataclass
class SkillEntry:
    index: int
    name: str
    has_action: bool
    extra: int = 0


@dataclass
class SkillGroup:
    index: int
    name: str


class SkillsManager:
    _instance: Optional['SkillsManager'] = None

    def __init__(self):
        self.skills: List[SkillEntry] = []
        self.groups: List[SkillGroup] = []
        self._file_index: Optional[FileIndex] = None
        self.reload()

    @classmethod
    def get_instance(cls) -> 'SkillsManager':
        if cls._instance is None:
            cls._instance = SkillsManager()
        return cls._instance

    def reload(self):
        if self._file_index:
            self._file_index.close()
        self.skills.clear()
        self.groups.clear()

        self._file_index = FileIndex("skills.idx", "skills.mul", max_entries=100, file_id=16)
        if self._file_index:
            for i in range(100):
                if not self._file_index.is_valid(i):
                    break
                data = self._file_index.get_data(i)
                if not data or len(data) < 1:
                    break
                action = data[0] != 0
                raw_name = data[1:]
                name = raw_name.split(b"\x00")[0].decode("ascii", errors="replace")
                extra = self._file_index.entries[i].extra
                self.skills.append(SkillEntry(index=i, name=name, has_action=action, extra=extra))

        # Skill groups
        fm = FileManager.get_instance()
        grp_path = fm.get_file_path("skillgrp.mul")
        if grp_path and os.path.exists(grp_path):
            try:
                with open(grp_path, "rb") as f:
                    data = f.read()
                # 4-byte count or header
                if len(data) >= 4:
                    count = struct.unpack_from("<I", data, 0)[0]
                    offset = 4
                    for g in range(count):
                        if offset >= len(data):
                            break
                        # Null-terminated name or 17-byte string
                        raw_name = data[offset: offset + 17]
                        name = raw_name.split(b"\x00")[0].decode("ascii", errors="replace")
                        self.groups.append(SkillGroup(index=g, name=name))
                        offset += 17
            except Exception as e:
                print(f"[SkillsManager] Failed to read skillgrp.mul: {e}")

    def save(self, directory: str):
        idx_path = os.path.join(directory, "skills.idx")
        mul_path = os.path.join(directory, "skills.mul")

        current_offset = 0
        with open(idx_path, "wb") as f_idx, open(mul_path, "wb") as f_mul:
            for s in self.skills:
                payload = bytes([1 if s.has_action else 0]) + s.name.encode("ascii") + b"\x00"
                f_mul.write(payload)
                f_idx.write(struct.pack("<iii", current_offset, len(payload), s.extra))
                current_offset += len(payload)
