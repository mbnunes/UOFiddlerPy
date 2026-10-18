"""
Main Application Window for UOFiddlerPy.
Contains all tabs matching UOFiddler in native, high-performance Python + PyQt6.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QMenuBar, QMenu, QMessageBox, QApplication
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt

from uofiddler.core.files import FileManager
from uofiddler.core.art import ArtManager
from uofiddler.core.tiledata import TileDataManager
from uofiddler.core.hues import HuesManager
from uofiddler.core.gumps import GumpManager
from uofiddler.core.textures import TextureManager
from uofiddler.core.radar_col import RadarColManager
from uofiddler.core.cliloc import ClilocManager
from uofiddler.core.sounds import SoundManager
from uofiddler.core.skills import SkillsManager
from uofiddler.core.speech import SpeechManager
from uofiddler.core.animdata import AnimDataManager
from uofiddler.core.light import LightManager
from uofiddler.core.multis import MultisManager
from uofiddler.core.animations import AnimationsManager
from uofiddler.core.fonts import FontsManager
from uofiddler.core.maps import MapManager
from uofiddler.core.gamedata import GameDataManager

from uofiddler.gui.theme import DARK_THEME_QSS
from uofiddler.gui.tabs.items_tab import ItemsTab
from uofiddler.gui.tabs.land_tiles_tab import LandTilesTab
from uofiddler.gui.tabs.tiledata_tab import TileDataTab
from uofiddler.gui.tabs.gumps_tab import GumpsTab
from uofiddler.gui.tabs.hues_tab import HuesTab
from uofiddler.gui.tabs.textures_tab import TexturesTab
from uofiddler.gui.tabs.radar_col_tab import RadarColorTab
from uofiddler.gui.tabs.animations_tab import AnimationsTab
from uofiddler.gui.tabs.cliloc_tab import ClilocTab
from uofiddler.gui.tabs.sounds_tab import SoundsTab
from uofiddler.gui.tabs.map_tab import MapTab
from uofiddler.gui.tabs.multis_tab import MultisTab
from uofiddler.gui.tabs.light_tab import LightTab
from uofiddler.gui.tabs.fonts_tab import FontsTab
from uofiddler.gui.tabs.skills_tab import SkillsTab
from uofiddler.gui.tabs.speech_tab import SpeechTab
from uofiddler.gui.tabs.animdata_tab import AnimDataTab
from uofiddler.gui.tabs.gamedata_tab import GameDataTab
from uofiddler.gui.tabs.settings_dialog import SettingsDialog
from uofiddler.gui.widgets.lazy_tab import LazyTabWrapper


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UOFiddlerPy - Ultima Online Client Viewer & Editor (100% Python)")
        self.resize(1280, 850)
        self.fm = FileManager.get_instance()

        self.init_menu()
        self.init_tabs()
        self.init_status_bar()

    def init_menu(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        settings_act = QAction("&Options / Directory Paths...", self)
        settings_act.triggered.connect(self.open_settings)
        file_menu.addAction(settings_act)

        reload_act = QAction("&Reload Client Files", self)
        reload_act.setShortcut("Ctrl+R")
        reload_act.triggered.connect(self.reload_all)
        file_menu.addAction(reload_act)

        file_menu.addSeparator()

        exit_act = QAction("E&xit", self)
        exit_act.setShortcut("Ctrl+Q")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        about_act = QAction("&About UOFiddlerPy", self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)

    def init_tabs(self):
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)

        # Tab definitions: (Title, Factory)
        self.tab_defs = [
            ("Items", lambda p: ItemsTab(p)),
            ("Land Tiles", lambda p: LandTilesTab(p)),
            ("TileData", lambda p: TileDataTab(p)),
            ("Gumps", lambda p: GumpsTab(p)),
            ("Hues", lambda p: HuesTab(p)),
            ("Textures", lambda p: TexturesTab(p)),
            ("RadarCol", lambda p: RadarColorTab(p)),
            ("Animations", lambda p: AnimationsTab(p)),
            ("Cliloc", lambda p: ClilocTab(p)),
            ("Sounds", lambda p: SoundsTab(p)),
            ("Map", lambda p: MapTab(p)),
            ("Multis", lambda p: MultisTab(p)),
            ("Light", lambda p: LightTab(p)),
            ("Fonts", lambda p: FontsTab(p)),
            ("Skills", lambda p: SkillsTab(p)),
            ("Speech", lambda p: SpeechTab(p)),
            ("AnimData", lambda p: AnimDataTab(p)),
            ("GameData", lambda p: GameDataTab(p)),
        ]

        # Tab 0 (Items) loads immediately so the main screen is active right away
        self.tab_items = ItemsTab(self)
        self.tab_widget.addTab(self.tab_items, "Items")

        # Tabs 1 to 17 are wrapped in LazyTabWrapper with loading indicator
        for title, factory in self.tab_defs[1:]:
            wrapper = LazyTabWrapper(title, factory, self)
            self.tab_widget.addTab(wrapper, title)

        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tab_widget)

    def on_tab_changed(self, index: int):
        widget = self.tab_widget.widget(index)
        if isinstance(widget, LazyTabWrapper) and not widget.is_loaded:
            widget.load()

    def __getattr__(self, name):
        tab_attr_map = {
            "tab_items": 0, "tab_land": 1, "tab_land_tiles": 1, "tab_tiledata": 2, "tab_gumps": 3,
            "tab_hues": 4, "tab_textures": 5, "tab_radar": 6, "tab_anim": 7,
            "tab_cliloc": 8, "tab_sounds": 9, "tab_map": 10, "tab_multis": 11,
            "tab_light": 12, "tab_fonts": 13, "tab_skills": 14, "tab_speech": 15,
            "tab_animdata": 16, "tab_gamedata": 17
        }
        if hasattr(self, "tab_widget") and name in tab_attr_map:
            idx = tab_attr_map[name]
            widget = self.tab_widget.widget(idx)
            if isinstance(widget, LazyTabWrapper):
                return widget.load()
            return widget
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def init_status_bar(self):
        self.status = QStatusBar(self)
        self.setStatusBar(self.status)
        self.update_status_bar()

    def update_status_bar(self):
        uo_dir = self.fm.uo_dir or "No directory configured"
        items_count = len(TileDataManager.get_instance().item_tiles)
        self.status.showMessage(f"Directory: {uo_dir} | Items loaded: {items_count} | All 17 Tabs Active")

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.reload_all()

    def reload_all(self):
        self.fm.load_settings()
        ArtManager.get_instance().reload()
        TileDataManager.get_instance().reload()
        HuesManager.get_instance().reload()
        GumpManager.get_instance().reload()
        TextureManager.get_instance().reload()
        RadarColManager.get_instance().reload()
        ClilocManager.get_instance().reload()
        SoundManager.get_instance().reload()
        SkillsManager.get_instance().reload()
        SpeechManager.get_instance().reload()
        AnimDataManager.get_instance().reload()
        LightManager.get_instance().reload()
        MultisManager.get_instance().reload()
        AnimationsManager.get_instance().reload()
        FontsManager.get_instance().reload()
        MapManager.get_instance().reload()
        GameDataManager.get_instance().reload()

        # Re-initialize tabs
        self.init_tabs()
        self.update_status_bar()
        QMessageBox.information(self, "Reload", "All client files successfully reloaded.")

    def navigate_to_gump(self, gump_id: int):
        """Switches to the Gumps tab and selects gump_id."""
        self.tab_widget.setCurrentIndex(3)
        gumps_tab = self.tab_gumps
        if hasattr(gumps_tab, "select_gump"):
            gumps_tab.select_gump(gump_id)

    def show_about(self):
        QMessageBox.about(
            self,
            "About UOFiddlerPy",
            "<h3>🗡️ UOFiddlerPy v1.0.0</h3>"
            "<p>A 100% native Python rewrite of UOFiddler for Linux and cross-platform systems.</p>"
            "<p><b>Zero .NET or Wine headaches.</b> Complete support for MUL and UOP formats, "
            "RLE decoders/encoders, 3,000 hues, High Seas tiledata, maps with LOD, animations, and multis.</p>"
            "<hr/>"
            "<p><b>Author:</b> Mauricio Nunes + Gemini</p>"
            "<p><b>GitHub:</b> <a href=\"https://github.com/mbnunes/UOFiddlerPy\" style=\"color: #64b5f6;\">"
            "https://github.com/mbnunes/UOFiddlerPy</a></p>"
            "<p>Built with PyQt6 and Pillow.</p>"
        )


def launch(show_splash: bool = True):
    import os
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("UOFiddlerPy")
    app.setStyleSheet(DARK_THEME_QSS)

    splash = None
    is_offscreen = "-platform" in sys.argv or "offscreen" in sys.argv or os.environ.get("QT_QPA_PLATFORM") == "offscreen"
    if show_splash and not is_offscreen:
        from uofiddler.gui.widgets.splash_screen import SplashScreen
        splash = SplashScreen()
        splash.show()
        splash.set_progress(15, "Verificando diretório do Ultima Online...", pause_ms=80)
        FileManager.get_instance()
        splash.set_progress(40, "Carregando configurações e índices...", pause_ms=80)
        TileDataManager.get_instance()
        splash.set_progress(70, "Carregando paletas e tema visual...", pause_ms=80)

    win = MainWindow()

    if splash:
        splash.set_progress(100, "Pronto!", pause_ms=90)
        win.show()
        splash.finish(win)
    else:
        win.show()

    return app.exec()
