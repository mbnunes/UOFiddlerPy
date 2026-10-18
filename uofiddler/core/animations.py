"""
Animations manager: Reads and decodes character and monster animations.
Supports anim.mul through anim6.mul, AnimationFrame1.uop through AnimationFrame6.uop,
AnimationSequence.uop, frame extraction, palette decoding, and 8 directions.
"""

import os
import struct
import zlib
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from PIL import Image
from uofiddler.core.files import FileManager
from uofiddler.core.file_index import FileIndex
from uofiddler.core.colors import color16_to_rgba
from uofiddler.core.hash_utils import hash_file_name
from uofiddler.core.defs import DefsManager


@dataclass
class AnimationFrame:
    center_x: int
    center_y: int
    image: Image.Image


class AnimationsManager:
    _instance: Optional['AnimationsManager'] = None
    DOUBLE_XOR = (0x200 << 22) | (0x200 << 12)

    def __init__(self):
        self._indices: Dict[int, FileIndex] = {}
        self._frame_cache: Dict[Tuple[int, int, int], List[AnimationFrame]] = {}
        # UOP archives: hash -> (path, offset, c_size, d_size, flag)
        self._uop_entries: Dict[int, Tuple[str, int, int, int, int]] = {}
        # Sequence replacements: body -> list of 80 action replacements
        self._sequence_replacements: Dict[int, List[int]] = {}
        self.reload()

    @classmethod
    def get_instance(cls) -> 'AnimationsManager':
        if cls._instance is None:
            cls._instance = AnimationsManager()
        return cls._instance

    def reload(self):
        for fi in self._indices.values():
            fi.close()
        self._indices.clear()
        self._frame_cache.clear()
        self._uop_entries.clear()
        self._sequence_replacements.clear()
        fm = FileManager.get_instance()

        # 1. anim.mul through anim6.mul
        configs = [
            (1, "Anim.idx", "Anim.mul", 0x40000),
            (2, "Anim2.idx", "Anim2.mul", 0x10000),
            (3, "Anim3.idx", "Anim3.mul", 0x20000),
            (4, "Anim4.idx", "Anim4.mul", 0x20000),
            (5, "Anim5.idx", "Anim5.mul", 0x20000),
            (6, "Anim6.idx", "Anim6.mul", 0x20000),
        ]

        for file_idx, idx_name, mul_name, max_entries in configs:
            try:
                p_idx = fm.get_file_path(idx_name)
                p_mul = fm.get_file_path(mul_name)
                if p_idx and p_mul and os.path.exists(p_idx) and os.path.exists(p_mul):
                    self._indices[file_idx] = FileIndex(
                        idx_file=idx_name,
                        mul_file=mul_name,
                        uop_file=None,
                        max_entries=max_entries,
                        file_id=6
                    )
            except Exception as e:
                print(f"[AnimationsManager] Failed to load {mul_name}: {e}")

        # 2. Load AnimationFrame1.uop through AnimationFrame6.uop
        for i in range(1, 7):
            p = fm.get_file_path(f"AnimationFrame{i}.uop")
            if not p or not os.path.exists(p):
                continue
            try:
                with open(p, "rb") as f:
                    magic, ver, sig, next_block, block_size, count = struct.unpack("<IIIQII", f.read(28))
                    if magic != 0x50594D:
                        continue
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
                            if offset != 0:
                                self._uop_entries[h] = (p, offset + h_len, c_len, d_len, flag)
                        if next_block != 0:
                            f.seek(next_block)
            except Exception as e:
                print(f"[AnimationsManager] Error reading AnimationFrame{i}.uop: {e}")

        # 3. Load AnimationSequence.uop
        p_seq = fm.get_file_path("AnimationSequence.uop")
        if p_seq and os.path.exists(p_seq):
            try:
                seq_entries = {}
                with open(p_seq, "rb") as f:
                    magic, ver, sig, next_block, block_size, count = struct.unpack("<IIIQII", f.read(28))
                    if magic == 0x50594D:
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
                                if offset != 0:
                                    seq_entries[h] = (offset + h_len, c_len, d_len, flag)
                            if next_block != 0:
                                f.seek(next_block)

                for anim_id in range(2048):
                    h = hash_file_name(f"build/animationsequence/{anim_id:08d}.bin")
                    if h in seq_entries:
                        pos, clen, dlen, flag = seq_entries[h]
                        with open(p_seq, "rb") as f:
                            f.seek(pos)
                            buf = f.read(clen)
                        if flag != 0:
                            buf = zlib.decompress(buf)
                        if len(buf) >= 56:
                            group_count = struct.unpack_from("<i", buf, 52)[0]
                            replacements = list(range(80))
                            cursor = 56
                            for _ in range(group_count):
                                if cursor + 64 > len(buf):
                                    break
                                group, frame_count, repl_group = struct.unpack_from("<iii", buf, cursor)
                                if frame_count == 0 and 0 <= group < 80 and repl_group >= 0:
                                    replacements[group] = repl_group
                                cursor += 64
                                if cursor + 4 <= len(buf):
                                    c1 = struct.unpack_from("<i", buf, cursor)[0]
                                    cursor += 4 + max(0, c1 * 32)
                                if cursor + 4 <= len(buf):
                                    c2 = struct.unpack_from("<i", buf, cursor)[0]
                                    cursor += 4 + max(0, c2 * 4)
                            self._sequence_replacements[anim_id] = replacements
            except Exception as e:
                print(f"[AnimationsManager] Error reading AnimationSequence.uop: {e}")

    def get_resolved_action(self, body: int, action: int) -> int:
        if body in self._sequence_replacements:
            repl = self._sequence_replacements[body]
            if 0 <= action < len(repl):
                return repl[action]
        return action

    @staticmethod
    def calculate_file_index(body: int, action: int, direction: int, file_type: int) -> int:
        if file_type == 2:
            base = body * 110 if body < 200 else 22000 + ((body - 200) * 65)
        elif file_type == 3:
            if body < 300:
                base = body * 65
            elif body < 400:
                base = 33000 + ((body - 300) * 110)
            else:
                base = 35000 + ((body - 400) * 175)
        elif file_type in (1, 4, 5, 6):
            if body < 200:
                base = body * 110
            elif body < 400:
                base = 22000 + ((body - 200) * 65)
            else:
                base = 35000 + ((body - 400) * 175)
        else:
            base = body * 110

        idx = base + (action * 5)
        if direction <= 4:
            idx += direction
        else:
            # Directions 5..7 use mirrored data of directions 3..1
            idx += direction - ((direction - 4) * 2)

        return idx

    def is_action_defined(self, body: int, action: int) -> bool:
        """Returns True if the given action has frames for this body in either UOP or MUL."""
        # 1. Check UOP
        resolved = self.get_resolved_action(body, action)
        h = hash_file_name(f"build/animationlegacyframe/{body:06d}/{resolved:02d}.bin")
        if h in self._uop_entries:
            return True

        # 2. Check MUL
        defs = DefsManager.get_instance()
        file_type, conv_body = defs.convert_body(body)
        fi = self._indices.get(file_type)
        if fi:
            raw_index = self.calculate_file_index(conv_body, action, 0, file_type)
            if fi.is_valid(raw_index):
                return True

        return False

    def get_defined_actions(self, body: int, max_actions: int = 80) -> List[int]:
        """Returns all action indices that actually exist for this body."""
        return [act for act in range(max_actions) if self.is_action_defined(body, act)]

    def get_animation_frames(self, body: int, action: int, direction: int = 0) -> List[AnimationFrame]:
        cache_key = (body, action, direction)
        if cache_key in self._frame_cache:
            return self._frame_cache[cache_key]

        # 1. Try UOP first
        resolved = self.get_resolved_action(body, action)
        uop_hash = hash_file_name(f"build/animationlegacyframe/{body:06d}/{resolved:02d}.bin")
        if uop_hash in self._uop_entries:
            frames = self._get_uop_animation_frames(uop_hash, direction)
            if frames:
                self._frame_cache[cache_key] = frames
                return frames

        # 2. Fallback to MUL/IDX
        defs = DefsManager.get_instance()
        file_type, conv_body = defs.convert_body(body)
        fi = self._indices.get(file_type)
        if not fi:
            return []

        raw_index = self.calculate_file_index(conv_body, action, direction, file_type)
        if not fi.is_valid(raw_index):
            return []

        data = fi.get_data(raw_index)
        if not data or len(data) < 516:
            return []

        frames = self._decode_animation(data, flip=(direction > 4))
        self._frame_cache[cache_key] = frames
        return frames

    def _get_uop_animation_frames(self, uop_hash: int, direction: int) -> List[AnimationFrame]:
        entry = self._uop_entries.get(uop_hash)
        if not entry:
            return []

        uop_path, pos, c_len, d_len, flag = entry
        try:
            with open(uop_path, "rb") as f:
                f.seek(pos)
                raw = f.read(c_len)

            if flag != 0:
                raw = zlib.decompress(raw)

            if len(raw) < 36:
                return []

            frame_count, data_start = struct.unpack_from("<II", raw, 32)
            if frame_count <= 0 or data_start >= len(raw):
                return []

            headers = []
            pos_cursor = data_start
            for _ in range(frame_count):
                if pos_cursor + 16 > len(raw):
                    break
                _, frame_id, _, pixel_offset = struct.unpack_from("<HHQI", raw, pos_cursor)
                headers.append((pos_cursor, frame_id, pixel_offset))
                pos_cursor += 16

            filled = []
            last_id = 1
            for pos_c, fid, pix_off in headers:
                while fid - last_id > 1:
                    last_id += 1
                    filled.append((0, last_id, 0))
                filled.append((pos_c, fid, pix_off))
                last_id = fid

            real_fc = int(round(len(filled) / 5.0))
            if real_fc <= 0:
                return []

            flip = direction > 4
            read_dir = direction if direction <= 4 else (direction - ((direction - 4) * 2))

            frames: List[AnimationFrame] = []
            for pos_c, fid, pix_off in filled:
                frame_dir = (fid - 1) // real_fc
                if frame_dir < read_dir:
                    continue
                if frame_dir > read_dir:
                    break

                if pos_c == 0:
                    continue

                frame_pos = pos_c + pix_off
                if frame_pos + 520 > len(raw):
                    continue

                palette_raw = struct.unpack_from("<256H", raw, frame_pos)
                palette = [color16_to_rgba(c if c == 0 else (c | 0x8000)) for c in palette_raw]

                x_center, y_center, width, height = struct.unpack_from("<hhHH", raw, frame_pos + 512)
                if width <= 0 or height <= 0 or width > 1024 or height > 1024:
                    continue

                img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                pixels = img.load()

                cursor = frame_pos + 520
                x_base = x_center - 0x200
                y_base = (y_center + height) - 0x200

                while cursor + 4 <= len(raw):
                    header = struct.unpack_from("<I", raw, cursor)[0]
                    cursor += 4
                    if header == 0x7FFF7FFF:
                        break

                    header ^= self.DOUBLE_XOR
                    row_y = (header >> 12) & 0x3FF
                    row_x = (header >> 22) & 0x3FF
                    run = header & 0xFFF

                    if cursor + run > len(raw):
                        break

                    for r in range(run):
                        pal_idx = raw[cursor + r]
                        rgba = palette[pal_idx]
                        if not flip:
                            px = x_base + row_x + r
                            py = y_base + row_y
                        else:
                            px = width - 1 - (x_base + row_x + r)
                            py = y_base + row_y

                        if 0 <= px < width and 0 <= py < height:
                            pixels[px, py] = rgba

                    cursor += run

                eff_cx = (width - x_center) if flip else x_center
                frames.append(AnimationFrame(center_x=eff_cx, center_y=y_center, image=img))

            return frames
        except Exception as e:
            return []

    @classmethod
    def _decode_animation(cls, data: bytes, flip: bool = False) -> List[AnimationFrame]:
        # Palette: 256 words (512 bytes)
        palette_words = struct.unpack_from("<256H", data, 0)
        palette = [color16_to_rgba(c | 0x8000) for c in palette_words]

        frame_count = struct.unpack_from("<I", data, 512)[0]
        if frame_count <= 0 or frame_count > 100:
            return []

        offset_table = struct.unpack_from(f"<{frame_count}I", data, 516)
        results: List[AnimationFrame] = []

        for frame_idx, frame_offset in enumerate(offset_table):
            start = 512 + frame_offset
            if start + 8 > len(data):
                continue

            x_center, y_center, width, height = struct.unpack_from("<hhHH", data, start)
            if width <= 0 or height <= 0 or width > 1024 or height > 1024:
                continue

            img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            pixels = img.load()

            cursor = start + 8
            x_base = x_center - 0x200
            y_base = (y_center + height) - 0x200

            while cursor + 4 <= len(data):
                header = struct.unpack_from("<I", data, cursor)[0]
                cursor += 4
                if header == 0x7FFF7FFF:
                    break

                header ^= cls.DOUBLE_XOR
                row_y = (header >> 12) & 0x3FF
                row_x = (header >> 22) & 0x3FF
                run = header & 0xFFF

                if cursor + run > len(data):
                    break

                for r in range(run):
                    pal_idx = data[cursor + r]
                    rgba = palette[pal_idx]

                    if not flip:
                        px = x_base + row_x + r
                        py = y_base + row_y
                    else:
                        px = width - 1 - (x_base + row_x + r)
                        py = y_base + row_y

                    if 0 <= px < width and 0 <= py < height:
                        pixels[px, py] = rgba

                cursor += run

            eff_center_x = (width - x_center) if flip else x_center
            results.append(AnimationFrame(center_x=eff_center_x, center_y=y_center, image=img))

        return results
