"""
Automated PyQt6 GUI test for UOFiddlerPy.
Tests creating the MainWindow with all 17 tabs in offscreen mode.
"""

import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication
from uofiddler.gui.app import MainWindow


class TestGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize QApplication in offscreen mode for automated headless testing
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(["UOFiddlerPyTest", "-platform", "offscreen"])

    def test_main_window_creation(self):
        win = MainWindow()
        self.assertIsNotNone(win)
        self.assertEqual(win.tab_widget.count(), 18)

        expected_tabs = [
            "Items", "Land Tiles", "TileData", "Gumps", "Hues",
            "Textures", "RadarCol", "Animations", "Cliloc", "Sounds",
            "Map", "Multis", "Light", "Fonts", "Skills", "Speech", "AnimData", "GameData"
        ]

        actual_tabs = [win.tab_widget.tabText(i) for i in range(win.tab_widget.count())]
        self.assertEqual(actual_tabs, expected_tabs)

        # Switch through each tab to verify rendering
        for i in range(win.tab_widget.count()):
            win.tab_widget.setCurrentIndex(i)
            self.assertEqual(win.tab_widget.currentIndex(), i)

        win.close()

    def test_grid_list_tabs(self):
        win = MainWindow()

        # The 6 tabs with Grid/List support:
        tab_indices = {
            "Items": 0,
            "Land Tiles": 1,
            "TileData": 2,
            "Hues": 4,
            "Textures": 5,
            "RadarCol": 6,
        }

        for tab_name, idx in tab_indices.items():
            win.tab_widget.setCurrentIndex(idx)
            tab = win.tab_widget.widget(idx)
            self.assertTrue(hasattr(tab, "browser"), f"{tab_name} tab must have a 'browser' attribute")
            browser = tab.browser

            # 1. Verify default view mode is GRID
            self.assertTrue(browser.btn_grid.isChecked(), f"{tab_name} default should be Grid button checked")
            self.assertEqual(browser.stack.currentIndex(), 0, f"{tab_name} default page should be 0 (Grid view)")

            # 2. Verify switching to LIST mode
            browser.btn_list.click()
            self.assertTrue(browser.btn_list.isChecked(), f"{tab_name} List button should be checked after click")
            self.assertEqual(browser.stack.currentIndex(), 1, f"{tab_name} page should be 1 (List view)")

            # 3. Verify switching back to GRID mode
            browser.btn_grid.click()
            self.assertTrue(browser.btn_grid.isChecked(), f"{tab_name} Grid button should be checked after click")
            self.assertEqual(browser.stack.currentIndex(), 0, f"{tab_name} page should be 0 (Grid view)")

            # 4. Verify selection sync
            browser.select_id(1)
            self.assertEqual(browser.get_selected_id(), 1)

        win.close()

    def test_splash_screen(self):
        from uofiddler.gui.widgets.splash_screen import SplashScreen
        splash = SplashScreen()
        self.assertIsNotNone(splash)
        splash.set_progress(50, "Testing splash progress...", pause_ms=0)
        self.assertEqual(splash.progress.value(), 50)
        self.assertEqual(splash.lbl_msg.text(), "Testing splash progress...")
        splash.close()

    def test_lazy_tab_wrapper(self):
        from uofiddler.gui.widgets.lazy_tab import LazyTabWrapper
        from PyQt6.QtWidgets import QLabel

        wrapper = LazyTabWrapper("MockTab", lambda p: QLabel("RealContent", p))
        self.assertFalse(wrapper.is_loaded)
        self.assertIsNone(wrapper.real_tab)

        # Trigger load
        real = wrapper.load()
        self.assertTrue(wrapper.is_loaded)
        self.assertIsNotNone(wrapper.real_tab)
        self.assertEqual(real.text(), "RealContent")

        # Attribute delegation test
        self.assertEqual(wrapper.text(), "RealContent")

    def test_interactive_map_view(self):
        from uofiddler.gui.widgets.interactive_map_view import InteractiveMapView
        from uofiddler.gui.tabs.map_tab import MapTab
        from PyQt6.QtCore import QPoint

        # 1. Test InteractiveMapView standalone
        view = InteractiveMapView()
        view.resize(800, 600)
        view.set_map_id(0)
        self.assertEqual(view.map_id, 0)
        self.assertEqual(view.current_map_info.width, 7168)
        self.assertEqual(view.current_map_info.height, 4096)

        # Center jump
        view.go_to(1400.0, 1600.0)
        self.assertEqual(view.center_x, 1400.0)
        self.assertEqual(view.center_y, 1600.0)

        # Zoom in / out
        initial_zoom = view.zoom
        view.zoom_in()
        self.assertGreater(view.zoom, initial_zoom)
        view.zoom_out()
        self.assertAlmostEqual(view.zoom, initial_zoom, places=2)

        # Screen to world conversion
        wx, wy = view.screen_to_world(400, 300)
        self.assertAlmostEqual(wx, 1400.0, delta=1.0)
        self.assertAlmostEqual(wy, 1600.0, delta=1.0)

        # World to screen conversion
        sx, sy = view.world_to_screen(1400.0, 1600.0)
        self.assertAlmostEqual(sx, 400.0, delta=1.0)
        self.assertAlmostEqual(sy, 300.0, delta=1.0)

        # 2. Test MapTab integration
        tab = MapTab()
        tab.resize(1024, 768)
        self.assertTrue(hasattr(tab, "map_view"))
        self.assertTrue(hasattr(tab, "preset_combo"))

        # Select landmark preset (e.g. Britain)
        for i in range(tab.preset_combo.count()):
            if "Britain" in tab.preset_combo.itemText(i):
                tab.preset_combo.setCurrentIndex(i)
                break

        self.assertAlmostEqual(tab.map_view.center_x, 1420.0, delta=2.0)
        self.assertAlmostEqual(tab.map_view.center_y, 1690.0, delta=2.0)

        tab.close()
        view.close()

    def test_animations_tab(self):
        from uofiddler.gui.tabs.animations_tab import AnimationsTab
        tab = AnimationsTab()
        self.assertGreater(tab.body_combo.count(), 100)
        self.assertGreater(len(tab._all_entries), 500)

        # Test selecting Dragon (body 12)
        idx_dragon = tab.body_combo.findData(12)
        if idx_dragon >= 0:
            tab.body_combo.setCurrentIndex(idx_dragon)
            self.assertGreater(len(tab.frames), 0)

        # Test selecting UOP creature (body 713)
        idx_uop = tab.body_combo.findData(713)
        if idx_uop >= 0:
            tab.body_combo.setCurrentIndex(idx_uop)
            self.assertGreater(len(tab.frames), 0)

        tab.close()

    def test_equipment_linker_and_container_overlay(self):
        win = MainWindow()

        # 1. Test Items Tab equipment linker
        items_tab = win.tab_items
        # Select Robe (0x1F03 = 7939) which has Anim ID 0x01D3 = 467
        items_tab.update_display(7939)
        self.assertIsNotNone(items_tab.current_male_gump)
        self.assertIsNotNone(items_tab.current_female_gump)
        self.assertGreater(items_tab.current_male_gump, 50000)
        self.assertGreater(items_tab.current_female_gump, 60000)

        # 2. Test Navigation from Items to Gump
        win.navigate_to_gump(items_tab.current_male_gump)
        self.assertEqual(win.tab_widget.currentIndex(), 3)  # Gumps Tab

        # 3. Test Gumps Tab Container Overlay
        gumps_tab = win.tab_gumps
        # Select Backpack gump (60)
        gumps_tab.select_gump(60)
        self.assertEqual(gumps_tab.current_gump_id, 60)
        self.assertIn("backpack", gumps_tab.lbl_container.text().lower())
        self.assertIsNotNone(gumps_tab.canvas._overlay_rect)
        self.assertEqual(gumps_tab.canvas._overlay_rect.x(), 44.0)
        self.assertEqual(gumps_tab.canvas._overlay_rect.y(), 65.0)
        self.assertEqual(gumps_tab.canvas._overlay_rect.width(), 142.0)
        self.assertEqual(gumps_tab.canvas._overlay_rect.height(), 94.0)

        # 4. Test Toggling overlay checkbox
        gumps_tab.chk_container.setChecked(False)
        self.assertIsNone(gumps_tab.canvas._overlay_rect)
        gumps_tab.chk_container.setChecked(True)
        self.assertIsNotNone(gumps_tab.canvas._overlay_rect)

        win.close()

    def test_gamedata_tab(self):
        win = MainWindow()
        tab = win.tab_gamedata
        self.assertEqual(tab.list_widget.count(), 79)

        # Load legacycontainers.csv
        tab.load_table("legacycontainers.csv")
        self.assertGreater(tab.table_widget.rowCount(), 10)
        self.assertGreater(tab.table_widget.columnCount(), 4)
        self.assertIn("legacycontainers.csv", tab.lbl_name.text())
        self.assertGreater(len(tab.raw_text_view.toPlainText()), 100)

        # Test filter
        tab.on_filter_changed("recipe")
        visible_count = sum(1 for i in range(tab.list_widget.count()) if not tab.list_widget.item(i).isHidden())
        self.assertGreater(visible_count, 0)
        tab.on_filter_changed("")

        win.close()

    def test_textures_tab_ec(self):
        win = MainWindow()
        tab = win.tab_textures

        # Switch to Enhanced Legacy mode (UOP)
        tab.combo_client.setCurrentIndex(1)
        self.assertGreater(tab.browser.count, 50000)
        tab.select_tex(0)
        self.assertIsNotNone(tab.canvas._pixmap)

        # Switch back to Classic mode
        tab.combo_client.setCurrentIndex(0)
        self.assertLess(tab.browser.count, 50000)

        win.close()

    def test_items_tab_ec(self):
        win = MainWindow()
        tab = win.tab_items

        # Verify initial classic mode
        self.assertEqual(tab.combo_client.currentData(), "classic")
        tab.select_item(2)  # Ankh / item with 3D model in legacy_to_new
        self.assertIsNotNone(tab.canvas._pixmap)
        self.assertIn("NewID", tab.lbl_ec_model.text())

        tab.select_item(3821)  # Gold coins (fallback to legacy texture)
        self.assertIn("Legacy Tile Texture", tab.lbl_ec_model.text())

        # Switch to Enhanced 3D mode
        tab.combo_client.setCurrentIndex(1)
        self.assertEqual(tab.combo_client.currentData(), "enhanced")
        tab.select_item(3821)
        self.assertIsNotNone(tab.canvas._pixmap)

        # Switch back to Classic mode
        tab.combo_client.setCurrentIndex(0)
        self.assertEqual(tab.combo_client.currentData(), "classic")

        win.close()

    def test_land_tiles_tab_ec(self):
        win = MainWindow()
        tab = win.tab_land_tiles

        # Verify initial classic mode
        self.assertEqual(tab.combo_client.currentData(), "classic")
        tab.select_tile(749)  # dirt
        self.assertIsNotNone(tab.canvas._pixmap)
        self.assertIn("dirt", tab.lbl_ec_terrain_name.text())
        self.assertIn("749", tab.lbl_ec_texmap.text())

        # Switch to Enhanced 3D mode
        tab.combo_client.setCurrentIndex(1)
        self.assertEqual(tab.combo_client.currentData(), "enhanced")
        tab.select_tile(749)
        self.assertIsNotNone(tab.canvas._pixmap)

        # Switch back to Classic mode
        tab.combo_client.setCurrentIndex(0)
        self.assertEqual(tab.combo_client.currentData(), "classic")

        win.close()


if __name__ == "__main__":
    unittest.main()


