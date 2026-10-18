"""
File path discovery, configuration, and case-insensitive file resolution for Ultima Online files.
Crucial for seamless Linux operation where ext4/btrfs is case-sensitive!
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict

CONFIG_DIR = Path.home() / ".config" / "uofiddler_py"
SETTINGS_FILE = CONFIG_DIR / "settings.json"


class FileManager:
    _instance: Optional['FileManager'] = None

    def __init__(self, uo_dir: Optional[str] = None):
        self.uo_dir: Optional[str] = None
        self._file_cache: Dict[str, str] = {}
        self.high_seas: bool = True
        self.load_settings()

        if uo_dir and os.path.isdir(uo_dir):
            self.set_uo_dir(uo_dir)
        elif not self.uo_dir or not os.path.isdir(self.uo_dir):
            self.auto_detect_dir()

    @classmethod
    def get_instance(cls) -> 'FileManager':
        if cls._instance is None:
            cls._instance = FileManager()
        return cls._instance

    def load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.uo_dir = data.get("uo_dir")
                    self.high_seas = data.get("high_seas", True)
            except Exception as e:
                print(f"[FileManager] Failed to load settings: {e}")

    def save_settings(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "uo_dir": self.uo_dir,
                    "high_seas": self.high_seas
                }, f, indent=4)
        except Exception as e:
            print(f"[FileManager] Failed to save settings: {e}")

    def set_uo_dir(self, directory: str):
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        self.uo_dir = os.path.abspath(directory)
        self._build_file_cache()
        self.save_settings()

    def _build_file_cache(self):
        """Index all files in the UO directory case-insensitively."""
        self._file_cache.clear()
        if not self.uo_dir or not os.path.isdir(self.uo_dir):
            return

        for root, dirs, files in os.walk(self.uo_dir):
            for file in files:
                lower = file.lower()
                full_path = os.path.join(root, file)
                # First one seen in top directory takes precedence
                if lower not in self._file_cache:
                    self._file_cache[lower] = full_path

    def get_file_path(self, filename: str) -> Optional[str]:
        """
        Gets the absolute path to a file case-insensitively.
        E.g. get_file_path("art.mul") finds "Art.mul", "ART.MUL", etc.
        """
        lower = filename.lower()
        if lower in self._file_cache:
            p = self._file_cache[lower]
            if os.path.exists(p):
                return p

        # Check directly in uo_dir
        if self.uo_dir and os.path.isdir(self.uo_dir):
            target = os.path.join(self.uo_dir, filename)
            if os.path.exists(target):
                return target

            # Fallback scan directory
            for f in os.listdir(self.uo_dir):
                if f.lower() == lower:
                    resolved = os.path.join(self.uo_dir, f)
                    self._file_cache[lower] = resolved
                    return resolved

        return None

    def auto_detect_dir(self) -> Optional[str]:
        """
        Scans common Linux paths for Ultima Online clients.
        """
        candidates = [
            "/opt/hd_jogos/UOC",
            "/opt/hd_jogos/UOML",
            str(Path.home() / "Documentos" / "Mysterious Age"),
            str(Path.home() / "Documents" / "Mysterious Age"),
            str(Path.home() / ".wine" / "drive_c" / "Program Files (x86)" / "Electronic Arts" / "Ultima Online Classic"),
            str(Path.home() / ".wine" / "drive_c" / "Program Files" / "Electronic Arts" / "Ultima Online Classic"),
            str(Path.home() / ".wine" / "drive_c" / "UO"),
            str(Path.home() / "Ultima Online"),
            str(Path.home() / "uo"),
        ]

        for cand in candidates:
            if os.path.isdir(cand):
                # Verify it looks like a UO directory
                for test_file in ["artidx.mul", "art.mul", "tiledata.mul", "MainData.uop"]:
                    if any(f.lower() == test_file.lower() for f in os.listdir(cand)):
                        print(f"[FileManager] Auto-detected UO directory: {cand}")
                        self.set_uo_dir(cand)
                        return cand

        return None
