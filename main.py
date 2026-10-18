#!/usr/bin/env python3
"""
UOFiddlerPy - Main Application Launcher
Runs 100% native Python with PyQt6 on any Linux distribution without .NET or Wine.
"""

import sys
import os

# Ensure current directory is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from uofiddler.gui.app import launch


def main():
    launch(show_splash=True)


if __name__ == "__main__":
    main()
