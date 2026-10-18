"""
TileData manager for reading, modifying, and saving tiledata.mul.
Supports both classic (32-bit flags) and High Seas (64-bit flags) formats.
"""

import os
import struct
from enum import IntFlag
from typing import List, Optional
from dataclasses import dataclass
from uofiddler.core.files import FileManager


class TileFlag(IntFlag):
    None_ = 0x00000000
    Background = 0x00000001
    Weapon = 0x00000002
    Transparent = 0x00000004
    Translucent = 0x00000008
    Wall = 0x00000010
    Damaging = 0x00000020
    Impassable = 0x00000040
    Wet = 0x00000080
    Unknown1 = 0x00000100
    Surface = 0x00000200
    Bridge = 0x00000400
    Generic = 0x00000800
    Window = 0x00001000
    NoShoot = 0x00002000
    PrefixA = 0x00004000
    PrefixAn = 0x00008000
    Internal = 0x00010000
    Foliage = 0x00020000
    PartialHue = 0x00040000
    Unknown2 = 0x00080000
    Map = 0x00100000
    Container = 0x00200000
    Wearable = 0x00400000
    LightSource = 0x00800000
    Animated = 0x01000000
    NoDiagonal = 0x02000000
    Unknown3 = 0x04000000
    Armor = 0x08000000
    Roof = 0x10000000
    Door = 0x20000000
    StairBack = 0x40000000
    StairRight = 0x80000000
    # High Seas (64-bit) additions
    AlphaBlend = 0x0000000100000000
    UseNewArt = 0x0000000200000000
    ArtUsed = 0x0000000400000000
    NoHouse = 0x0000000800000000
    NoDraw = 0x0000001000000000
    HoverOver = 0x0000002000000000


@dataclass
class LandTileData:
    flags: int = 0
    texture_id: int = 0
    name: str = ""


@dataclass
class ItemTileData:
    flags: int = 0
    weight: int = 0
    quality: int = 0
    misc_data: int = 0
    unk2: int = 0
    quantity: int = 0
    anim_id: int = 0
    unk3: int = 0
    hue: int = 0
    stacking_offset: int = 0
    value: int = 0
    height: int = 0
    name: str = ""


class TileDataManager:
    _instance: Optional['TileDataManager'] = None

    def __init__(self):
        self.land_tiles: List[LandTileData] = [LandTileData() for _ in range(0x4000)]
        self.item_tiles: List[ItemTileData] = [ItemTileData() for _ in range(0x10000)]
        self.is_high_seas: bool = True
        self._land_headers: List[int] = []
        self._item_headers: List[int] = []
        self.reload()

    @classmethod
    def get_instance(cls) -> 'TileDataManager':
        if cls._instance is None:
            cls._instance = TileDataManager()
        return cls._instance

    def reload(self):
        fm = FileManager.get_instance()
        path = fm.get_file_path("tiledata.mul")
        if not path or not os.path.exists(path):
            return

        with open(path, "rb") as f:
            data = f.read()

        file_len = len(data)
        # Old format land block = 4 + 32 * 26 = 836 bytes; 512 blocks = 428,032 bytes
        # High Seas land block = 4 + 32 * 30 = 964 bytes; 512 blocks = 493,568 bytes
        # Old item block = 4 + 32 * 37 = 1188 bytes
        # High Seas item block = 4 + 32 * 41 = 1316 bytes

        # Test High Seas vs Old by checking file size
        # Total items: usually 0x4000 (classic), 0x8000, or 0x10000 (HS)
        # Check if 493,568 can divide into land blocks
        # Let's inspect bytes 0..836 vs 0..964:
        # In land blocks, each entry has name[20].
        # In Old format, name is at offset 4 + 2 = 6 to 26 (index 0).
        # In HS format, name is at offset 8 + 2 = 10 to 30.
        # Check null-termination or printable ASCII of entry 1 name:
        old_test_name = data[4 + 6: 4 + 26]
        hs_test_name = data[4 + 10: 4 + 30]

        # In UO, land tile 1 is usually "grass" or "dirt" or similar
        def is_printable_uo_name(b: bytes) -> bool:
            try:
                s = b.split(b"\x00")[0].decode("ascii")
                return len(s) > 0 and all(32 <= ord(c) < 127 for c in s)
            except Exception:
                return False

        if is_printable_uo_name(hs_test_name):
            self.is_high_seas = True
        elif is_printable_uo_name(old_test_name):
            self.is_high_seas = False
        else:
            # Fallback to file size test
            self.is_high_seas = file_len > 1500000

        self._parse(data)

    def _parse(self, data: bytes):
        offset = 0
        self.land_tiles = [LandTileData() for _ in range(0x4000)]
        self._land_headers = []

        land_struct_size = 30 if self.is_high_seas else 26
        land_flag_format = "<Q" if self.is_high_seas else "<I"

        for block in range(512):
            if offset + 4 > len(data):
                break
            header = struct.unpack_from("<I", data, offset)[0]
            self._land_headers.append(header)
            offset += 4

            for i in range(32):
                idx = block * 32 + i
                if offset + land_struct_size > len(data):
                    break
                if self.is_high_seas:
                    flags, tex_id = struct.unpack_from("<QH", data, offset)
                    raw_name = data[offset + 10: offset + 30]
                else:
                    flags, tex_id = struct.unpack_from("<IH", data, offset)
                    raw_name = data[offset + 6: offset + 26]

                name = raw_name.split(b"\x00")[0].decode("ascii", errors="replace")
                self.land_tiles[idx] = LandTileData(flags=flags, texture_id=tex_id, name=name)
                offset += land_struct_size

        # Item tiles
        item_struct_size = 41 if self.is_high_seas else 37
        block_size = 4 + 32 * item_struct_size
        remaining = len(data) - offset
        item_block_count = remaining // block_size
        total_items = item_block_count * 32

        self.item_tiles = [ItemTileData() for _ in range(total_items)]
        self._item_headers = []

        for block in range(item_block_count):
            if offset + 4 > len(data):
                break
            header = struct.unpack_from("<I", data, offset)[0]
            self._item_headers.append(header)
            offset += 4

            for i in range(32):
                idx = block * 32 + i
                if offset + item_struct_size > len(data):
                    break
                if self.is_high_seas:
                    flags, weight, quality, misc, unk2, qty, anim, unk3, hue, stack_off, val, height = struct.unpack_from(
                        "<QBBhBBhBBBBB", data, offset
                    )
                    raw_name = data[offset + 21: offset + 41]
                else:
                    flags, weight, quality, misc, unk2, qty, anim, unk3, hue, stack_off, val, height = struct.unpack_from(
                        "<IBBhBBhBBBBB", data, offset
                    )
                    raw_name = data[offset + 17: offset + 37]

                name = raw_name.split(b"\x00")[0].decode("ascii", errors="replace")
                self.item_tiles[idx] = ItemTileData(
                    flags=flags,
                    weight=weight,
                    quality=quality,
                    misc_data=misc,
                    unk2=unk2,
                    quantity=qty,
                    anim_id=anim,
                    unk3=unk3,
                    hue=hue,
                    stacking_offset=stack_off,
                    value=val,
                    height=height,
                    name=name
                )
                offset += item_struct_size

    def get_land(self, index: int) -> Optional[LandTileData]:
        if 0 <= index < len(self.land_tiles):
            return self.land_tiles[index]
        return None

    def get_item(self, index: int) -> Optional[ItemTileData]:
        if 0 <= index < len(self.item_tiles):
            return self.item_tiles[index]
        return None

    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            # Land blocks
            land_flag_fmt = "<Q" if self.is_high_seas else "<I"
            header_idx = 0
            for block in range(512):
                h = self._land_headers[header_idx] if header_idx < len(self._land_headers) else 0
                header_idx += 1
                f.write(struct.pack("<I", h))

                for i in range(32):
                    idx = block * 32 + i
                    tile = self.land_tiles[idx] if idx < len(self.land_tiles) else LandTileData()
                    f.write(struct.pack(land_flag_fmt, tile.flags))
                    f.write(struct.pack("<H", tile.texture_id))
                    name_bytes = tile.name.encode("ascii", errors="replace")[:20]
                    f.write(name_bytes.ljust(20, b"\x00"))

            # Item blocks
            item_blocks = (len(self.item_tiles) + 31) // 32
            header_idx = 0
            for block in range(item_blocks):
                h = self._item_headers[header_idx] if header_idx < len(self._item_headers) else 0
                header_idx += 1
                f.write(struct.pack("<I", h))

                for i in range(32):
                    idx = block * 32 + i
                    tile = self.item_tiles[idx] if idx < len(self.item_tiles) else ItemTileData()
                    if self.is_high_seas:
                        f.write(struct.pack(
                            "<QBBhBBhBBBBB",
                            tile.flags, tile.weight, tile.quality, tile.misc_data,
                            tile.unk2, tile.quantity, tile.anim_id, tile.unk3,
                            tile.hue, tile.stacking_offset, tile.value, tile.height
                        ))
                    else:
                        f.write(struct.pack(
                            "<IBBhBBhBBBBB",
                            tile.flags, tile.weight, tile.quality, tile.misc_data,
                            tile.unk2, tile.quantity, tile.anim_id, tile.unk3,
                            tile.hue, tile.stacking_offset, tile.value, tile.height
                        ))
                    name_bytes = tile.name.encode("ascii", errors="replace")[:20]
                    f.write(name_bytes.ljust(20, b"\x00"))
