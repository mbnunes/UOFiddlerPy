"""
GameData Manager: Parses GameData.uop (MYP v5) from Ultima Online Enhanced (3D) and Equipconv.def.
Provides container bounding boxes (legacycontainers.csv), 2D-to-3D item conversions,
body mappings, and equipment-to-gump resolution.
"""

import os
import struct
import zlib
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List
from uofiddler.core.files import FileManager
from uofiddler.core.hash_utils import hash_file_name


@dataclass
class ContainerBounds:
    gump_id: int
    left: int
    top: int
    right: int
    bottom: int
    name: str

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        """Returns (x, y, width, height) suitable for Qt QRect."""
        return (self.left, self.top, self.width, self.height)


@dataclass
class EquipConvEntry:
    body_type: int
    equipment_id: int
    convert_to_id: int
    gump_id_to_use: int
    hue: int = 0


@dataclass
class ECTerrainInfo:
    tile_id: int
    name: str
    tex_map: int
    flags: List[str]


@dataclass
class GameDataEntry:
    index: int
    hash: int
    compressed_size: int
    decompressed_size: int
    compression: int
    name: str = ""
    raw_data: Optional[bytes] = None


class GameDataManager:
    _instance: Optional['GameDataManager'] = None

    # Known hashes in GameData.uop
    HASH_CONTAINERS = 0xE840D2286751791C  # data/gamedata/legacycontainers.csv
    HASH_LEGACY_CONV = 0x78AFB72A49CD9BE9  # legacyId,newId,newSubType
    HASH_BODY_CONV = 0xBF2AE37FAFC672E7    # BodyType,Filename,Description
    HASH_RECIPES = 0xF45CF6B325F9D01A      # data/gamedata/recipes.csv

    def __init__(self):
        self.containers: Dict[int, ContainerBounds] = {}
        self.legacy_to_new: Dict[int, Tuple[int, int]] = {}  # legacyId -> (newId, newSubType)
        self.body_to_mesh: Dict[int, Tuple[str, str]] = {}   # bodyType -> (filename, description)
        self.equip_conversions: Dict[Tuple[int, int], EquipConvEntry] = {}  # (body, animID) -> entry
        self.legacy_terrain: Dict[int, ECTerrainInfo] = {}   # tileId -> ECTerrainInfo
        self.entries_by_hash: Dict[int, GameDataEntry] = {}
        self.entries_by_name: Dict[str, GameDataEntry] = {}
        self.is_loaded: bool = False
        self.reload()

    @classmethod
    def get_instance(cls) -> 'GameDataManager':
        if cls._instance is None:
            cls._instance = GameDataManager()
        return cls._instance

    def reload(self):
        self.containers.clear()
        self.legacy_to_new.clear()
        self.body_to_mesh.clear()
        self.equip_conversions.clear()
        self.legacy_terrain.clear()
        self.entries_by_hash.clear()
        self.entries_by_name.clear()
        self.is_loaded = False

        fm = FileManager.get_instance()

        # 1. Parse Classic Equipconv.def if present
        p_equipconv = fm.get_file_path("Equipconv.def")
        if p_equipconv and os.path.exists(p_equipconv):
            self._load_classic_equipconv(p_equipconv)

        # 2. Parse 3D GameData.uop if present
        p_gamedata = fm.get_ec_file_path("GameData.uop") or fm.get_file_path("GameData.uop")
        if p_gamedata and os.path.exists(p_gamedata):
            try:
                self._load_gamedata_uop(p_gamedata)
                self.is_loaded = True
            except Exception as e:
                print(f"[GameDataManager] Error parsing GameData.uop: {e}")

        # 3. Parse 3D LegacyTerrain.uop if present
        p_terrain = fm.get_ec_file_path("LegacyTerrain.uop") or fm.get_file_path("LegacyTerrain.uop")
        if p_terrain and os.path.exists(p_terrain):
            try:
                self._load_legacy_terrain_uop(p_terrain)
            except Exception as e:
                print(f"[GameDataManager] Error parsing LegacyTerrain.uop: {e}")

    def _load_legacy_terrain_uop(self, uop_path: str):
        import xml.etree.ElementTree as ET
        with open(uop_path, "rb") as f:
            hdr = f.read(28)
            if len(hdr) < 28:
                return
            magic, ver, sig, next_block, cap, count = struct.unpack("<IIIQII", hdr)
            if magic != 0x50594D:
                return

            while next_block != 0:
                f.seek(next_block)
                block_hdr = f.read(12)
                if len(block_hdr) < 12:
                    break
                f_count, next_block = struct.unpack("<IQ", block_hdr)
                for _ in range(f_count):
                    entry_raw = f.read(34)
                    if len(entry_raw) < 34:
                        break
                    offset, h_len, c_len, d_len, h, crc, comp = struct.unpack("<QIIIQIH", entry_raw)
                    if offset != 0:
                        pos = f.tell()
                        f.seek(offset + h_len)
                        data = f.read(c_len)
                        if comp == 1:
                            data = zlib.decompress(data)
                        f.seek(pos)
                        try:
                            root = ET.fromstring(data)
                            tt = root.find("terrainType")
                            if tt is not None:
                                t_id = int(tt.get("id", -1))
                                t_name = tt.get("name", "")
                                t_tex = int(tt.get("texMap", -1))
                                tf = tt.find("typeFlags")
                                flags = [child.tag for child in tf] if tf is not None else []
                                self.legacy_terrain[t_id] = ECTerrainInfo(
                                    tile_id=t_id,
                                    name=t_name,
                                    tex_map=t_tex,
                                    flags=flags
                                )
                        except Exception:
                            pass

    def get_legacy_terrain(self, tile_id: int) -> Optional[ECTerrainInfo]:
        return self.legacy_terrain.get(tile_id)

    def _load_classic_equipconv(self, path: str):
        try:
            with open(path, "r", encoding="latin1") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            body = int(parts[0])
                            anim_id = int(parts[1])
                            convert_to = int(parts[2])
                            gump_to_use = int(parts[3])
                            hue = int(parts[4]) if len(parts) >= 5 else 0
                            entry = EquipConvEntry(
                                body_type=body,
                                equipment_id=anim_id,
                                convert_to_id=convert_to,
                                gump_id_to_use=gump_to_use,
                                hue=hue
                            )
                            self.equip_conversions[(body, anim_id)] = entry
                        except ValueError:
                            pass
        except Exception as e:
            print(f"[GameDataManager] Error parsing Equipconv.def: {e}")

    def _load_gamedata_uop(self, uop_path: str):
        with open(uop_path, "rb") as f:
            hdr = f.read(28)
            if len(hdr) < 28:
                return
            magic, ver, sig, next_block, cap, count = struct.unpack("<IIIQII", hdr)
            if magic != 0x50594D:
                return

            entry_idx = 0
            while next_block != 0:
                f.seek(next_block)
                block_hdr = f.read(12)
                if len(block_hdr) < 12:
                    break
                files_count, next_block = struct.unpack("<IQ", block_hdr)

                for _ in range(files_count):
                    entry_raw = f.read(34)
                    if len(entry_raw) < 34:
                        break
                    offset, h_len, c_len, d_len, h, crc, comp = struct.unpack("<QIIIQIH", entry_raw)
                    if offset == 0:
                        continue

                    # Read and decompress entry payload
                    pos = f.tell()
                    f.seek(offset + h_len)
                    raw_data = f.read(c_len)
                    if comp == 1:
                        try:
                            data = zlib.decompress(raw_data)
                        except Exception:
                            data = raw_data
                    else:
                        data = raw_data
                    f.seek(pos)

                    # Identify name
                    name = self._identify_entry_name(h, data, entry_idx)

                    entry = GameDataEntry(
                        index=entry_idx,
                        hash=h,
                        compressed_size=c_len,
                        decompressed_size=d_len,
                        compression=comp,
                        name=name,
                        raw_data=data
                    )
                    self.entries_by_hash[h] = entry
                    self.entries_by_name[name] = entry

                    # Parse specific well-known tables
                    if h == self.HASH_CONTAINERS or "legacycontainers" in name:
                        self._parse_containers_csv(data)
                    elif h == self.HASH_LEGACY_CONV or "legacyId,newId" in name:
                        self._parse_legacy_conv_csv(data)
                    elif h == self.HASH_BODY_CONV or "BodyType,Filename" in name:
                        self._parse_body_conv_csv(data)

                    entry_idx += 1

    def _identify_entry_name(self, h: int, data: bytes, idx: int) -> str:
        if h == self.HASH_CONTAINERS:
            return "legacycontainers.csv"
        elif h == self.HASH_LEGACY_CONV:
            return "legacy_to_new_items.csv"
        elif h == self.HASH_BODY_CONV:
            return "body_to_mesh.csv"
        elif h == self.HASH_RECIPES:
            return "recipes.csv"

        # Check first line for table title
        first_line = data.split(b"\n")[0].decode("latin1", errors="replace").strip()
        if first_line.startswith("#"):
            first_line = first_line.lstrip("#").strip()
        if first_line and len(first_line) < 40 and not first_line.startswith("int,"):
            clean_title = first_line.replace(",", "_").replace(" ", "_").lower()
            return f"{idx:02d}_{clean_title}.csv"

        return f"{idx:02d}_table_{h:016x}.csv"

    def _parse_containers_csv(self, data: bytes):
        text = data.decode("latin1", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("gumpId") or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                try:
                    gump_id = int(parts[0])
                    left = int(parts[1])
                    top = int(parts[2])
                    right = int(parts[3])
                    bottom = int(parts[4])
                    name = parts[5] if len(parts) > 5 else f"Container {gump_id}"
                    self.containers[gump_id] = ContainerBounds(
                        gump_id=gump_id,
                        left=left,
                        top=top,
                        right=right,
                        bottom=bottom,
                        name=name
                    )
                except ValueError:
                    pass

    def _parse_legacy_conv_csv(self, data: bytes):
        text = data.decode("latin1", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("legacyId") or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                try:
                    legacy_id = int(parts[0])
                    new_id = int(parts[1])
                    new_sub_type = int(parts[2])
                    self.legacy_to_new[legacy_id] = (new_id, new_sub_type)
                except ValueError:
                    pass

    def _parse_body_conv_csv(self, data: bytes):
        text = data.decode("latin1", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("BodyType") or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                try:
                    body_type = int(parts[0])
                    filename = parts[1]
                    desc = parts[2] if len(parts) > 2 else ""
                    self.body_to_mesh[body_type] = (filename, desc)
                except ValueError:
                    pass

    def get_container(self, gump_id: int) -> Optional[ContainerBounds]:
        """Returns bounding box for a container gump, or None if not a known container."""
        return self.containers.get(gump_id)

    def get_all_containers(self) -> Dict[int, ContainerBounds]:
        return self.containers

    def get_legacy_conversion(self, legacy_item_id: int) -> Optional[Tuple[int, int]]:
        """Returns (newId, newSubType) for an item ID in Enhanced Client."""
        return self.legacy_to_new.get(legacy_item_id)

    def get_equip_gump(self, anim_id: int, body_type: int = 400, gender: int = 0) -> int:
        """
        Calculates the Gump ID for worn equipment based on anim_id, body_type, and gender.
        Implements the exact logic discovered via static analysis:
          1. Check (body_type, anim_id) in Equipconv.
          2. Calculate base gump ID (+50000 / override).
          3. If female (gender == 1), test +60000 offset.
        """
        if anim_id <= 0:
            return 0

        # Check equipconv table
        key = (body_type, anim_id)
        if key in self.equip_conversions:
            entry = self.equip_conversions[key]
            if entry.gump_id_to_use == -1:
                base_gump = entry.convert_to_id + 50000
            elif entry.gump_id_to_use > 0:
                base_gump = entry.gump_id_to_use
            else:
                base_gump = anim_id + 50000
        else:
            base_gump = anim_id + 50000

        # If female mobile, test if gender-specific gump (+10000 -> 60000 + anim_id) exists
        if gender == 1:
            female_candidate = base_gump + 10000
            from uofiddler.core.gumps import GumpManager
            gm = GumpManager.get_instance()
            if gm.is_valid(female_candidate):
                return female_candidate

        return base_gump

    def list_table_names(self) -> List[str]:
        return list(self.entries_by_name.keys())

    def get_table_csv(self, name_or_hash) -> Optional[str]:
        entry = None
        if isinstance(name_or_hash, int):
            entry = self.entries_by_hash.get(name_or_hash)
        elif isinstance(name_or_hash, str):
            entry = self.entries_by_name.get(name_or_hash)
        if entry and entry.raw_data:
            return entry.raw_data.decode("latin1", errors="replace")
        return None
