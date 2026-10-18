# UOFiddlerPy 🗡️

> 🌐 **Language / Idioma**: **English** | [Português (README_pt-br.md)](README_pt-br.md)  
> 👤 **Author**: Mauricio Nunes + Gemini  
> 🔗 **GitHub**: [https://github.com/mbnunes/UOFiddlerPy](https://github.com/mbnunes/UOFiddlerPy)

**UOFiddlerPy** is a complete, native, high-performance **Python 3** recreation of the classic **UOFiddler** for Ultima Online. It is designed to run smoothly, stably, and elegantly on **any Linux distribution** (Ubuntu, Debian, Fedora, Arch Linux, openSUSE, etc.) and other operating systems, completely eliminating any dependency on the **.NET runtime**, **Mono**, or **Wine**.

---

## 💡 Why was UOFiddlerPy created?

Running the original C#/.NET version of UOFiddler on Linux through Wine or Mono frequently leads to:
- Graphical glitches, font rendering crashes, and memory leaks (GDI+ / WinForms limitations).
- Path resolution errors caused by Linux case-sensitive filesystems (*ext4, btrfs, xfs*), whereas Ultima Online clients mix case arbitrarily (`Art.mul`, `artidx.mul`, `ARTLegacyMUL.uop`).
- Cumbersome Wine prefix management and heavyweight .NET Desktop Runtime dependencies.

**UOFiddlerPy** solves all of these issues:
1. **100% Native Python 3 + PyQt6**: Uses system-native libraries with hardware-accelerated rendering.
2. **Case-Insensitive File Resolution**: `FileManager` indexes and locates client files regardless of casing.
3. **Smart Auto-Detection**: Automatically detects existing Ultima Online client installations across Linux (including `/opt/hd_jogos/`, `~/.wine/`, Lutris, Steam, current directory, and user folders).
4. **60 FPS Performance via Virtualization**: Instantaneous navigation across tables with **65,536 items** and **16,384 land tiles** utilizing on-demand Model-View architecture without memory bloat.
5. **Modern Dark Theme**: Clean, high-contrast user interface tailored for long editing sessions.
6. **Native Audio without Windows Drivers**: Direct sound playback using standard Linux audio servers (`PipeWire`, `PulseAudio`, `ALSA`).
7. **Hybrid Startup Architecture (Splash Screen + Lazy Loading)**: Fast, dark splash screen at launch with real-time progress steps (~1s), paired with on-demand tab loading (*Lazy Loading*) featuring animated loading indicators on first access, keeping memory footprint low and response times instantaneous.

---

## 📑 Comprehensive Overview of all 18 Tabs

### 1. ⚔️ Items (Statics)
- **Dual-Client Engine Switcher**: Toggle seamlessly between **Classic (2D Art)** and **Enhanced 3D (UOP)**.
- **Enhanced Client DDS Textures**: Direct decoding of `LegacyTexture.uop` high-fidelity Direct3D DDS textures with alpha channel.
- **EC 3D Model Inspector**: Live resolution of classic item IDs to new 3D model replacements (`legacy_to_new_items.csv` `NewID` and `SubType`) or fallback indicator.
- **Grid (Default) & List Modes**: Switch between a visual icon grid (`⊞ Grid`) with hexadecimal labels and a detailed table view (`☰ List`).
- **Virtualized Navigation**: Instant access to all 65,536 static item IDs at 60 FPS with zero memory freeze.
- **Fast Search**: Search by decimal ID, hexadecimal (`0x0EED`), or item name across both view modes.
- **Interactive Canvas**: Full mouse wheel zoom, click-and-drag pan, and checkerboard transparency background.
- **Hue Tester**: Preview any of the 3,000 hues applied directly to the item (with proper `PartialHue` flag handling).
- **TileData Inspector**: View name, flags, weight, layer/quality, height, and associated animation ID.
- **🔗 Worn Equipment & Gump Linker**:
  - Automatic **Item ID ➔ Paperdoll Gump ID** resolution for armor, clothing, weapons, and cloaks.
  - Race/Body selector: Humans (400/401), Elves (605/606), and Gargoyles (666/667).
  - Automated lookup of `Equipconv` tables and gender rules (+10000 female offset).
  - One-click **"View Male Gump"** and **"View Female Gump"** buttons with instant navigation to the Gumps tab!
- **Operations**: Export artwork to PNG/BMP, replace graphics with external images, and remove entries.

### 2. 🌿 Land Tiles (Terrain)
- **Dual-Client Engine Switcher**: Toggle on the fly between **Classic (2D Diamond)** and **Enhanced 3D (Texture & XML)**.
- **Enhanced Client 3D Terrain & Textures**: Displays the actual surface texture mapped by the 3D GPU engine (`texMap` in `Texture.uop` / `Texmaps.mul`).
- **3D Terrain XML Inspector**: Full metadata inspection from `LegacyTerrain.uop` showing EC terrain name (`dirt`, `snow`, `brick`, etc.), `texMap` ID, and physical 3D flags (`impassable`, `wet`, `surface`).
- **Grid (Default) & List Modes**: Fluid switching between isometric diamond grids and detailed technical tables.
- **44x44 Rhombus Geometry**: Exact decoding of the classic isometric 16-bit RGB 555 terrain diamond format.
- **Navigation & Filtering**: Filter all 16,384 land tiles by ID or name.
- **Tile Properties**: Display terrain flags (`Impassable`, `Surface`, `Bridge`, `Wet`, etc.) and Texture ID.
- **Export & Replace**: Import external PNG/BMP textures while preserving standard client geometry.

### 3. 📋 TileData
- **Grid (Default) & List Modes**: Choose between visual thumbnail grids and complete technical attribute tables.
- **Full Flags Editor**: Dual format support for classic clients (32-bit flags) and modern **High Seas clients (64-bit flags)**.
- **Dual Section Toggle**: Seamless switching between `ItemData` and `LandData`.
- **Complete Checkboxes for All Flags**:
  - `Background`, `Weapon`, `Transparent`, `Translucent`, `Wall`, `Damaging`, `Impassable`, `Wet`, `Surface`, `Bridge`, `Generic`, `Window`, `NoShoot`, `PrefixA`, `PrefixAn`, `Internal`, `Foliage`, `PartialHue`, `Map`, `Container`, `Wearable`, `LightSource`, `Animated`, `NoDiagonal`, `Armor`, `Roof`, `Door`, `StairBack`, `StairRight`, `AlphaBlend`, `UseNewArt`, `ArtUsed`, `NoHouse`, `NoDraw`, `HoverOver`.
- **Field Editing**: Name (up to 20 characters), weight, layer/quality, height, animation ID, hue, and terrain texture.
- **Direct Save**: Clean, structured saving directly into `tiledata.mul`.

### 4. 🖼️ Gumps
- **Dual-Client Client Switcher**: On-the-fly switching between **Classic (2D)** and **Enhanced (3D)** clients.
- **Dual Format Support**: Reads classic `gumpart.mul` / `gumpidx.mul` and modern Mythic `gumpartLegacyMUL.uop` packages.
- **📦 Container Bounding Box Overlay**:
  - Automatic container recognition from `data/gamedata/legacycontainers.csv` inside `GameData.uop`.
  - Displays exact container bounding box (`left, top, right, bottom, width, height`).
  - Real-time semi-transparent green overlay of valid drag-and-drop area with toggle checkbox.
- **Full Decompression Pipeline**: Transparent dual decompression (Zlib + Mythic Move-to-Front block decompressor).
- **Interactive Zoom Canvas**: Inspect large UI windows (e.g., 640x480 book menus) or small buttons and icons.
- **Export & Import**: Export gumps to transparent PNG or import custom UI assets.

### 5. 🎨 Hues
- **Grid Mode (Default) with Color Swatches**: In Grid mode, each cell displays a solid color square sampled from the hue's mid-tone palette, labeled with its numeric ID.
- **List Mode**: Table view displaying ID, hexadecimal code, name, and color sample.
- **3,000 Loaded Hues**: Full 375 groups of 8 hues each, mirroring `hues.mul`.
- **32-Color Palette Bar**: Interactive, clickable visual representation of all 32 shades in the hue scale.
- **Color Picker**: Modify any of the 32 individual color shades using the native system color dialog.
- **Live Re-Hue Preview**: Test the tint effect on any game item in real-time.
- **Name Editing & Saving**: Rename hues and save alterations back into `hues.mul`.

### 6. 🧱 Textures
- **Multi-Source Client Selector**: Switch on the fly between **Classic (2D MUL)**, **Enhanced Legacy (UOP)**, and **Enhanced 3D (UOP)**.
- **Enhanced Client DDS Textures**: Full native reading of **over 52,940 DDS textures** from `LegacyTexture.uop` and **9,790 modern textures** from `Texture.uop`!
- **Grid (Default) & List Modes**: Fast visual thumbnail navigation or detailed table with exact dimensions (64x64, 64x128, 128x128, etc.).
- **Terrain Textures**: Full support for classic 64x64 and 128x128 16-bit RGB 555 formats as well as modern DirectX DDS textures.
- **Accurate Color Conversion**: Precise decoding from 16-bit RGB 555 and DXT compression directly into 32-bit RGBA.
- **Import & Export**: Extract textures for Photoshop/GIMP editing or import new PNG files.

### 7. 🛰️ RadarCol (Minimap Colors)
- **Grid (Default) & List Modes**: Grid displays item/terrain artwork with a radar color indicator badge in the corner (or solid color swatch).
- **Full Color Table**: 16-bit color mapping for every land tile (0x0000..0x3FFF) and static item (0x4000..0x13FFF).
- **Smart Auto Color Generator**: Calculates the average representative color of any item or land tile (skipping transparent pixels) and fills the radar color automatically with one click!
- **Color Picker & Saving**: Fine-tune colors and save changes directly into `radarcol.mul`.

### 8. 🐉 Animations (Creatures, Characters & Equipment)
- **Over 1,320 Bodies Cataloged**: Comprehensive body catalog integrating `Animationlist.xml` and `mobtypes.txt` with real names and categories (Monsters, Animals, Sea Creatures, Humans, and Equipment).
- **Native Modern UOP Support**: Full decoding of packages `AnimationFrame1.uop` through `AnimationFrame6.uop` using 64-bit Jenkins `lookup3` hashes (including modern Stygian Abyss, Time of Legends, and High Seas creatures such as Gargoyles, Abyssal Infernals, etc. — over 10,980 animation entries decoded).
- **Animation Sequence Aliasing**: Automatically parses `AnimationSequence.uop` for action alias replacement and group mapping.
- **Classic Multi-File Support**: Reads `anim.mul` through `anim6.mul` with body translation via `bodyconv.def` and `body.def`.
- **Category Filter & Real-Time Search**: Search creatures by name or ID (decimal or hexadecimal) with instantaneous filtering.
- **Smart Action Detection**: Action dropdown dynamically adapts to the body's type (Monster, Sea, Animal, or Human) with checkmark indicators (`✓`) highlighting actions with available frames.
- **Interactive Player**: Play, Pause, Next Frame, Previous Frame, FPS speed slider (2 to 30 fps), and 8-direction selector with automatic mirroring.

### 9. 🌐 Cliloc (Localization & Text)
- **Ultra-Fast Search**: Instant search by ID number or any substring contained in localized strings.
- **Integrated Editor**: Edit system messages, spells, or item descriptions.
- **Creation & Deletion**: Add new custom strings or remove obsolete entries.
- **Saving**: Direct, compatible writing into `cliloc.*` files (e.g., `cliloc.enu`).

### 10. 🔊 Sounds (Audio & Sound Effects)
- **Native Linux Audio Player**: Listen to sound effects without freezing the UI, using standard Linux audio utilities (`pw-play`, `paplay`, or `aplay`).
- **Sound.def Support**: Automatic resolution of sound redirections and index translations.
- **WAV Export & Import**: Extract sounds to standard WAVE format (22,050 Hz Mono 16-bit) or import custom audio clips.

### 11. 🗺️ Map (World Viewer - High-Performance Google Maps Style with LOD)
- **Google Maps-Style Navigation**: Map fills the entire tab area. Navigate freely by dragging with the left mouse button (smooth Pan & Drag) and zoom with the mouse wheel focused precisely on the cursor location.
- **Stutter-Free LOD (Level of Detail)**: When zooming out (`zoom < 0.55`), the viewer switches to the global overview layer with hardware-accelerated bilinear filtering, guaranteeing **60 FPS under 1ms per frame** with zero CPU overhead or disk thrashing.
- **Column-Contiguous Disk I/O**: Reads contiguous land blocks and static index entries in single read operations, decoding chunks in milliseconds.
- **Intelligent LRU Chunk Cache**: Least-Recently-Used cache bounded to **1,500 chunks (~150MB)**, evicting only oldest entries to ensure ultra-smooth panning without cache wipes.
- **Continuous Zoom & Double Click**: Zoom range from 0.08x (entire world view) to 16.0x (individual tile inspection). Double-clicking zooms in on the clicked location.
- **All Facets Supported**: Felucca, Trammel, Ilshenar, Malas, Tokuno, and Ter Mur with native resolutions (7168x4096, 2304x1600, etc.).
- **24 Landmark Presets**: Dropdown with instant jumps to major cities and points of interest (Britain, Moonglow, Trinsic, Yew, Minoc, Luna, Umbra, Zento, Royal City, Delucia, etc.).
- **Coordinate Jump (X, Y)**: Enter specific coordinates to jump directly anywhere in Britannia.
- **Statics Toggle**: Instantly show or hide static structures and objects.
- **Real-Time HUD**: Scale bar, live cursor coordinates `Cursor: (X, Y)`, current camera center, and zoom percentage.

### 12. 🏰 Multis (Buildings, Houses & Ships)
- **2.5D Isometric Renderer**: Renders buildings by projecting each component with its respective Z height and sorting depth.
- **Height Cutoff Slider**: Interactively slice through upper floors and roofs to inspect house interiors.
- **Components Table**: Detailed list of every ItemID, relative X, Y, Z offsets, and construction flags.
- **Script Export**: Export building blueprints into compatible text script formats.

### 13. 💡 Light (Lighting Masks)
- View light sources and masks from `light.mul` and `lightidx.mul`.
- Render intensity gradients over dark backgrounds.

### 14. 🔤 Fonts (ASCII Fonts)
- Full support for all ASCII client fonts (0 through 9).
- View complete character glyph tables.
- Interactive live text sandbox to test phrases rendered with in-game typography.

### 15. 🏹 Skills
- Complete skills table from `skills.mul` and `skills.idx`.
- Direct action button configuration (*Use Skill*).
- Skill group hierarchy display from `skillgrp.mul`.

### 16. 💬 Speech (Triggers & Keywords)
- Keyword and speech trigger table from `speech.mul`.
- Big-endian ID decoding and UTF-8 string encoding.
- Filter and edit NPC speech keywords.

### 17. ⏱️ AnimData (Tile Animation Timing)
- Read and edit `animdata.mul`.
- Configure frame counts, animation intervals, start delays, and frame offset sequences for animated world tiles.

### 18. 📊 GameData (3D Enhanced Tables & CSVs Inspector)
- **Full `GameData.uop` Explorer**: Native extraction and browsing across all **79 metadata configuration tables** from the Enhanced Client (3D).
- **Interactive Table Grid**: Formatted grid view (`QTableWidget`) with headers, alternating row colors, column resizing, and real-time text filter.
- **Raw CSV / XML Inspector**: Monospaced text tab to view and copy the raw configuration text verbatim.
- **Key Cataloged Tables**:
  - `legacycontainers.csv`: Exact drag-and-drop bounding boxes for all game containers.
  - `legacy_to_new_items.csv`: Direct translation mapping from 2D Classic item IDs to new 3D models and textures.
  - `body_to_mesh.csv`: Translation of classic body types to high-definition 3D mesh files (`.dds`).
  - `recipes.csv`: Comprehensive crafting recipe catalog, skill requirements, and ingredient limits.
  - House placement data, house sign gumps, skin hues, horn styles, and skill definitions.
- **Batch & Table Export**:
  - Export individual tables to **CSV** or **JSON**.
  - One-click **"Export All 79 Tables..."** batch exporter to any folder on your machine.

---

## 🛠️ Core Technologies & Algorithms

- **⚡ Native C99 High-Performance Acceleration Engine (`uofiddler/native/`)**:
  - Direct RLE static decompression writing directly into 32-bit RGBA memory buffers (**~58x faster** than pure Python).
  - In-place palette transformation for Hues (**~75x faster**).
  - Isometric 44x44 terrain diamond rasterizer (**~48x faster**).
  - Bob Jenkins `lookup3` 64-bit hashing and Mythic Move-To-Front / frequency table decompressor in native C.
  - **Zero External Dependencies & Auto-Compilation**: Written in strictly compliant ANSI C99; automatically compiles into a shared library (`libuo_core.so` / `uo_core.dll` / `libuo_core.dylib`) on first run using `gcc`, `clang`, or MSVC.
  - **Graceful Fallback**: If no C compiler is present on the host system, UOFiddlerPy falls back transparently to its pure Python implementation without errors.
- **Bob Jenkins lookup3 (hashlittle2)**: Exact 64-bit hash algorithm used by `.uop` Mythic packages for constant-time entry lookups.
- **Adler32 Checksum**: Data integrity verification inside UOP entry tables.
- **Zlib & Mythic Decompression**: `MoveToFront` algorithm combined with frequency table decoding for modern compressed archives.
- **ARGB1555 Color Conversion**: Precomputed lookup tables converting 5-bit (0..31) and 8-bit (0..255) color channels for maximum execution speed.
- **RLE Decoders & Encoders**: Bidirectional Run-Length Encoding stream processing for static items and gumps.

---

## 📦 Requirements & Installation

### Prerequisites
- **Python 3.10 or higher**
- **PyQt6** (or PyQt5)
- **Pillow** (PIL)
- *(Optional)* GCC, Clang, or MSVC compiler for native C99 acceleration (automatically detected).

### Installing System Dependencies

On your Linux distribution, install packages via the system package manager or via `pip`:

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pyqt6 python3-pil build-essential
```

**Arch Linux / Manjaro:**
```bash
sudo pacman -S python python-pyqt6 python-pillow base-devel
```

**Fedora:**
```bash
sudo dnf install python3 python3-pyqt6 python3-pillow gcc
```

**Via pip (Virtual Environment or User):**
```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run

### 1. Graphical User Interface (GUI)

Inside the `UOFiddlerPy/` directory:

```bash
./run.sh
```

Or directly using the Python interpreter:
```bash
python3 main.py
```

Upon launch, UOFiddlerPy will automatically scan and detect your Ultima Online installation directory. To customize paths manually, use the top menu:  
**File ➔ Options / Directory Paths...**

---

### 2. Command Line Interface (CLI)

UOFiddlerPy includes a powerful CLI utility (`cli.py`) for headless inspections, automation scripts, and batch image extractions:

```bash
# Print summary of detected Ultima Online client files
./cli.py --info

# Export an item image to PNG (e.g., Gold Coins 0x0EED / 3821)
./cli.py --export-item 3821 --out /tmp/gold.png

# Export a land tile (e.g., Grass 0x0002)
./cli.py --export-land 2 --out /tmp/grass.png

# Export a Gump (e.g., Gump ID 0)
./cli.py --export-gump 0 --out /tmp/gump0.png

# Export an isometric multi house blueprint (e.g., Multi 0)
./cli.py --export-multi 0 --out /tmp/house.png
```

---

## 🧪 Automated Testing

The project includes an automated test suite of **32 comprehensive unit tests** verifying the binary parsing engine, 100% pixel-parity between C and Python implementations, and the PyQt6 GUI in offscreen (headless) mode:

```bash
# Run core file parser tests (Art, TileData, Hues, Gumps, Multis, Maps, Animations)
python3 -m unittest tests/test_core.py

# Run native C99 accelerator tests (validating pixel parity & benchmarks against pure Python)
python3 -m unittest tests/test_native.py

# Run PyQt6 GUI tests (in offscreen mode)
python3 -m unittest tests/test_gui.py

# Run all 32 tests together
python3 -m unittest discover tests
```

---

## 📂 Project Structure

```
UOFiddlerPy/
├── main.py                     # GUI application entry point
├── cli.py                      # Command-line interface
├── run.sh                      # Shell launch script
├── requirements.txt            # Python dependencies (PyQt6, Pillow)
├── README.md                   # Main documentation (English)
├── README_pt-br.md             # Documentação em Português
├── Animationlist.xml           # XML creature and equipment catalog
├── tests/
│   ├── test_core.py            # Core engine unit tests
│   ├── test_native.py          # Native C99 pixel-parity & performance tests
│   └── test_gui.py             # Headless PyQt6 GUI unit tests
└── uofiddler/
    ├── native/                 # High-performance C99 acceleration engine
    │   ├── __init__.py         # ctypes loader & auto-compiler with Python fallback
    │   ├── uo_core.h           # Native C99 declarations
    │   └── uo_core.c           # High-speed RLE, land, hue, lookup3 & mythic routines
    ├── core/                   # Binary UO engine (GUI-independent)
    │   ├── files.py            # Path detection & case-insensitive file resolution
    │   ├── file_index.py       # File indexing (.idx, .mul, and Mythic .uop)
    │   ├── hash_utils.py       # Bob Jenkins lookup3 & Adler32 implementations
    │   ├── mythic.py           # Mythic Move-To-Front decompressor
    │   ├── colors.py           # 16-bit RGB 555 / 32-bit RGBA color conversion
    │   ├── art.py              # Item & land tile encoder/decoder (C-accelerated)
    │   ├── tiledata.py         # Classic & High Seas tiledata parser & writer
    │   ├── hues.py             # 3,000 hues palette engine (C-accelerated)
    │   ├── gumps.py            # Gump image decoder & encoder
    │   ├── textures.py         # 64x64 and 128x128 land texture decoder
    │   ├── radar_col.py        # Minimap color reader & auto-average calculator
    │   ├── sounds.py           # Audio parser, WAV header generator & Linux playback
    │   ├── cliloc.py           # Cliloc string localization table reader/writer
    │   ├── skills.py           # Skill table & skill group parser
    │   ├── speech.py           # NPC speech keyword trigger parser
    │   ├── animdata.py         # Tile animation timing & cycle offsets
    │   ├── light.py            # Light source masks
    │   ├── multis.py           # 2.5D building components & isometric projector
    │   ├── animations.py       # Animation frames & directions (MUL + UOP)
    │   ├── maps.py             # Facets, 8x8 terrain blocks, statics & column I/O
    │   ├── gamedata.py         # GameData.uop parser (79 tables & legacy terrain XML)
    │   └── defs.py             # Parsers for bodyconv.def, body.def, mobtypes.txt & Animationlist.xml
    └── gui/                    # Modern PyQt6 user interface
        ├── app.py              # Main window & tab coordinator with Lazy Loading
        ├── theme.py            # Dark theme style sheet (QSS)
        ├── widgets/
        │   ├── splash_screen.py# Fast splash screen with animated progress steps (~1s)
        │   ├── lazy_tab.py     # Lazy load wrapper with progress bar
        │   ├── image_canvas.py # Interactive canvas with zoom and pan
        │   ├── color_bar.py    # 32-color Hue palette bar
        │   ├── virtual_tile_view.py # Virtualized Grid / List browser (60 FPS)
        │   └── interactive_map_view.py # Google Maps-style viewer with LOD & LRU
        └── tabs/               # All 18 tabs implemented
            ├── items_tab.py
            ├── land_tiles_tab.py
            ├── tiledata_tab.py
            ├── gumps_tab.py
            ├── hues_tab.py
            ├── textures_tab.py
            ├── radar_col_tab.py
            ├── animations_tab.py
            ├── cliloc_tab.py
            ├── sounds_tab.py
            ├── map_tab.py
            ├── multis_tab.py
            ├── light_tab.py
            ├── fonts_tab.py
            ├── skills_tab.py
            ├── speech_tab.py
            ├── animdata_tab.py
            ├── gamedata_tab.py
            └── settings_dialog.py
```

---

## 👤 Author & Acknowledgments

- **Author**: Mauricio Nunes + Gemini
- **GitHub Repository**: [https://github.com/mbnunes/UOFiddlerPy](https://github.com/mbnunes/UOFiddlerPy)

---

## 📄 License

Distributed under the open-source spirit of the Ultima Online community. Feel free to use, modify, and enhance!
