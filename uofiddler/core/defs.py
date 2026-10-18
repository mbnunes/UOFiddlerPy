"""
Definition files parser: bodyconv.def, body.def, and mobtypes.txt.
Handles monster/character body conversions between different anim files.
"""

import os
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
import xml.etree.ElementTree as ET
from uofiddler.core.files import FileManager


@dataclass
class AnimationDef:
    body: int
    name: str
    mob_type: int  # 0: Monster, 1: Sea, 2: Animal, 3: Human / Equipment
    is_equip: bool = False
    is_uop: bool = False


class DefsManager:
    _instance: Optional['DefsManager'] = None

    def __init__(self):
        # Body conversions: original_body -> (anim_file_index, new_body_id)
        self.bodyconv: Dict[int, Tuple[int, int]] = {}
        # Body translations: original_body -> translated_body
        self.body_def: Dict[int, int] = {}
        # Mob types: body_id -> category string (HUMAN, MONSTER, ANIMAL, etc.)
        self.mobtypes: Dict[int, str] = {}
        # Mob flags: body_id -> integer flags (0x10000 = UOP asset)
        self.mob_flags: Dict[int, int] = {}
        # Defined animation list entries
        self.anim_entries: List[AnimationDef] = []
        self._entries_by_body: Dict[int, AnimationDef] = {}
        self.reload()

    @classmethod
    def get_instance(cls) -> 'DefsManager':
        if cls._instance is None:
            cls._instance = DefsManager()
        return cls._instance

    def reload(self):
        self.bodyconv.clear()
        self.body_def.clear()
        self.mobtypes.clear()
        self.mob_flags.clear()
        self.anim_entries.clear()
        self._entries_by_body.clear()
        fm = FileManager.get_instance()

        # 1. bodyconv.def
        p_bodyconv = fm.get_file_path("bodyconv.def")
        if p_bodyconv and os.path.exists(p_bodyconv):
            try:
                with open(p_bodyconv, "r", encoding="latin1") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                body = int(parts[0])
                                # file2, file3, file4, file5 columns
                                for file_idx, col in enumerate(parts[1:5], start=2):
                                    val = int(col)
                                    if val != -1:
                                        self.bodyconv[body] = (file_idx, val)
                                        break
                            except ValueError:
                                pass
            except Exception as e:
                print(f"[DefsManager] Error parsing bodyconv.def: {e}")

        # 2. body.def
        p_body = fm.get_file_path("body.def")
        if p_body and os.path.exists(p_body):
            try:
                with open(p_body, "r", encoding="latin1") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                src = int(parts[0])
                                tgt_str = parts[1].replace("{", "").replace("}", "")
                                tgt = int(tgt_str)
                                self.body_def[src] = tgt
                            except ValueError:
                                pass
            except Exception as e:
                print(f"[DefsManager] Error parsing body.def: {e}")

        # 3. mobtypes.txt
        p_mob = fm.get_file_path("mobtypes.txt")
        if p_mob and os.path.exists(p_mob):
            try:
                with open(p_mob, "r", encoding="latin1") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                body = int(parts[0])
                                category = parts[1].upper()
                                self.mobtypes[body] = category
                                if len(parts) >= 3:
                                    try:
                                        flag = int(parts[2], 16)
                                        self.mob_flags[body] = flag
                                    except ValueError:
                                        pass
                            except ValueError:
                                pass
            except Exception as e:
                print(f"[DefsManager] Error parsing mobtypes.txt: {e}")

        # 4. Animationlist.xml (Search app folder and repo paths)
        xml_candidates = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Animationlist.xml"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Animationlist.xml"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "UoFiddler", "Animationlist.xml"),
            fm.get_file_path("Animationlist.xml"),
        ]

        xml_path = next((p for p in xml_candidates if p and os.path.exists(p)), None)
        seen_bodies = set()

        if xml_path and os.path.exists(xml_path):
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                for elem in root:
                    tag = elem.tag
                    if tag in ("Mob", "Equip"):
                        try:
                            body = int(elem.attrib.get("body", -1))
                            name = elem.attrib.get("name", f"Body {body}")
                            t_val = int(elem.attrib.get("type", 3 if tag == "Equip" else 0))
                            is_eq = (tag == "Equip")
                            is_u = bool(self.mob_flags.get(body, 0) & 0x10000)

                            entry = AnimationDef(
                                body=body,
                                name=name,
                                mob_type=t_val,
                                is_equip=is_eq,
                                is_uop=is_u
                            )
                            self.anim_entries.append(entry)
                            self._entries_by_body[body] = entry
                            seen_bodies.add(body)
                        except (ValueError, KeyError):
                            pass
            except Exception as e:
                print(f"[DefsManager] Error parsing Animationlist.xml: {e}")

        # 5. Populate any remaining bodies found in mobtypes.txt not in Animationlist.xml
        cat_to_type = {"MONSTER": 0, "SEA": 1, "ANIMAL": 2, "HUMAN": 3, "EQUIPMENT": 3}
        for body, cat in sorted(self.mobtypes.items()):
            if body not in seen_bodies:
                t_val = cat_to_type.get(cat, 0)
                is_u = bool(self.mob_flags.get(body, 0) & 0x10000)
                entry = AnimationDef(
                    body=body,
                    name=f"{cat.capitalize()} ({body})",
                    mob_type=t_val,
                    is_equip=(cat == "EQUIPMENT"),
                    is_uop=is_u
                )
                self.anim_entries.append(entry)
                self._entries_by_body[body] = entry
                seen_bodies.add(body)

    def is_uop_body(self, body: int) -> bool:
        return bool(self.mob_flags.get(body, 0) & 0x10000)

    def get_animation_def(self, body: int) -> Optional[AnimationDef]:
        return self._entries_by_body.get(body)

    def convert_body(self, body: int) -> Tuple[int, int]:
        """
        Translates body ID through body.def and bodyconv.def.
        Returns (anim_file_index, target_body_id).
        anim_file_index: 1 for anim.mul, 2 for anim2.mul, 3 for anim3.mul, etc.
        """
        # Apply body.def first
        if body in self.body_def:
            body = self.body_def[body]

        # Apply bodyconv.def
        if body in self.bodyconv:
            return self.bodyconv[body]

        return (1, body)
