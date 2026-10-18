"""
Sound manager: Reads, plays, imports, exports, and saves sound.mul and soundidx.mul.
Supports UOP sound files (soundLegacyMUL.uop) and sound.def translations.
Includes native Linux sound playback via paplay / aplay / pw-play.
"""

import os
import struct
import subprocess
import tempfile
import threading
from typing import Optional, Dict
from dataclasses import dataclass
from uofiddler.core.files import FileManager
from uofiddler.core.file_index import FileIndex


@dataclass
class SoundEntry:
    sound_id: int
    name: str
    wav_bytes: bytes


class SoundManager:
    _instance: Optional['SoundManager'] = None

    def __init__(self):
        self._file_index: Optional[FileIndex] = None
        self._translations: Dict[int, int] = {}
        self._cache: Dict[int, SoundEntry] = {}
        self.max_sounds = 0xFFF
        self.reload()

    @classmethod
    def get_instance(cls) -> 'SoundManager':
        if cls._instance is None:
            cls._instance = SoundManager()
        return cls._instance

    def reload(self):
        if self._file_index:
            self._file_index.close()
        self._cache.clear()
        self._translations.clear()

        self._file_index = FileIndex(
            "soundidx.mul",
            "sound.mul",
            "soundLegacyMUL.uop",
            max_entries=self.max_sounds,
            file_id=8,
            uop_ext=".dat"
        )

        # Load translations from Sound.def
        fm = FileManager.get_instance()
        def_path = fm.get_file_path("sound.def")
        if def_path and os.path.exists(def_path):
            try:
                with open(def_path, "r", encoding="latin1") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                src = int(parts[0])
                                # Target might be formatted as {123}
                                tgt_str = parts[1].replace("{", "").replace("}", "")
                                tgt = int(tgt_str)
                                self._translations[src] = tgt
                            except ValueError:
                                pass
            except Exception as e:
                print(f"[SoundManager] Error reading sound.def: {e}")

    def is_valid(self, sound_id: int) -> bool:
        if 0 <= sound_id < self.max_sounds:
            if self._file_index and self._file_index.is_valid(sound_id):
                return True
            if sound_id in self._translations:
                tgt = self._translations[sound_id]
                return self._file_index.is_valid(tgt) if self._file_index else False
        return False

    def get_sound(self, sound_id: int) -> Optional[SoundEntry]:
        if sound_id < 0 or sound_id >= self.max_sounds:
            return None
        if sound_id in self._cache:
            return self._cache[sound_id]

        target_id = sound_id
        if not self._file_index or not self._file_index.is_valid(target_id):
            if sound_id in self._translations:
                target_id = self._translations[sound_id]
            else:
                return None

        if not self._file_index.is_valid(target_id):
            return None

        data = self._file_index.get_data(target_id)
        if not data or len(data) <= 40:
            return None

        # First 40 bytes: name null-terminated
        raw_name = data[:40]
        pcm_data = data[40:]
        name = raw_name.split(b"\x00")[0].decode("ascii", errors="replace")

        # Create full RIFF WAVE file buffer:
        # Standard UO Sound format: 22050 Hz, 16-bit Mono (or check PCM)
        wav_header = self._create_wave_header(len(pcm_data))
        full_wav = wav_header + pcm_data

        entry = SoundEntry(sound_id=sound_id, name=name, wav_bytes=full_wav)
        self._cache[sound_id] = entry
        return entry

    @staticmethod
    def _create_wave_header(pcm_len: int) -> bytes:
        # 44 bytes RIFF WAVE Header:
        # 22050 Hz, 1 channel (mono), 16 bits per sample
        return struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            pcm_len + 36,
            b"WAVE",
            b"fmt ",
            16,             # chunk size
            1,              # PCM format
            1,              # channels (mono)
            22050,          # sample rate
            44100,          # byte rate (22050 * 1 * 2)
            2,              # block align
            16,             # bits per sample
            b"data",
            pcm_len
        )

    def play_sound(self, sound_id: int):
        """
        Plays sound using system audio (paplay, aplay, or pw-play) in background thread.
        """
        sound = self.get_sound(sound_id)
        if not sound or not sound.wav_bytes:
            return

        def _worker():
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(sound.wav_bytes)
                    tmp_name = tmp.name

                for player in ["paplay", "pw-play", "aplay"]:
                    try:
                        res = subprocess.run([player, tmp_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        if res.returncode == 0:
                            break
                    except FileNotFoundError:
                        continue
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass
            except Exception as e:
                print(f"[SoundManager] Error playing sound {sound_id}: {e}")

        threading.Thread(target=_worker, daemon=True).start()
