#!/usr/bin/env python3
"""
UOFiddlerPy CLI - Command-line interface for inspecting and extracting UO files.
"""

import sys
import os
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from uofiddler.core.files import FileManager
from uofiddler.core.art import ArtManager
from uofiddler.core.tiledata import TileDataManager
from uofiddler.core.hues import HuesManager
from uofiddler.core.gumps import GumpManager
from uofiddler.core.multis import MultisManager
from uofiddler.core.maps import MapManager


def main():
    parser = argparse.ArgumentParser(description="UOFiddlerPy CLI - Command Line Tool")
    parser.add_argument("--dir", help="Ultima Online directory path")
    parser.add_argument("--info", action="store_true", help="Print loaded client summary")
    parser.add_argument("--export-item", type=int, help="Export static item ID to PNG")
    parser.add_argument("--export-land", type=int, help="Export land tile ID to PNG")
    parser.add_argument("--export-gump", type=int, help="Export gump ID to PNG")
    parser.add_argument("--export-multi", type=int, help="Export multi ID to PNG")
    parser.add_argument("--out", default="output.png", help="Output file path for exports")

    args = parser.parse_args()

    fm = FileManager.get_instance()
    if args.dir:
        fm.set_uo_dir(args.dir)

    print(f"=== UOFiddlerPy CLI ===")
    print(f"Author: Mauricio Nunes + Gemini")
    print(f"GitHub: https://github.com/mbnunes/UOFiddlerPy")
    print(f"Active UO Directory: {fm.uo_dir}")

    if args.info:
        tm = TileDataManager.get_instance()
        hm = HuesManager.get_instance()
        mm = MultisManager.get_instance()
        mapm = MapManager.get_instance()
        print(f"High Seas TileData: {tm.is_high_seas}")
        print(f"Land Tiles Count:   {len(tm.land_tiles)}")
        print(f"Item Tiles Count:   {len(tm.item_tiles)}")
        print(f"Hues Count:         {len(hm.hues)}")
        print(f"Available Maps:     {[m.name for m in mapm.maps]}")

    if args.export_item is not None:
        art = ArtManager.get_instance()
        img = art.get_static(args.export_item)
        if img:
            img.save(args.out)
            print(f"Saved item 0x{args.export_item:04X} to {args.out} ({img.size})")
        else:
            print(f"Item 0x{args.export_item:04X} not found.")

    if args.export_land is not None:
        art = ArtManager.get_instance()
        img = art.get_land(args.export_land)
        if img:
            img.save(args.out)
            print(f"Saved land 0x{args.export_land:04X} to {args.out} ({img.size})")
        else:
            print(f"Land 0x{args.export_land:04X} not found.")

    if args.export_gump is not None:
        gm = GumpManager.get_instance()
        img = gm.get_gump(args.export_gump)
        if img:
            img.save(args.out)
            print(f"Saved gump 0x{args.export_gump:04X} to {args.out} ({img.size})")
        else:
            print(f"Gump 0x{args.export_gump:04X} not found.")

    if args.export_multi is not None:
        mm = MultisManager.get_instance()
        m = mm.get_multi(args.export_multi)
        if m:
            img = m.render_isometric()
            if img:
                img.save(args.out)
                print(f"Saved multi 0x{args.export_multi:04X} to {args.out} ({img.size})")
            else:
                print(f"Could not render multi {args.export_multi}")
        else:
            print(f"Multi 0x{args.export_multi:04X} not found.")


if __name__ == "__main__":
    main()
