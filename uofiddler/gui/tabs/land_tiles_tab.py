"""
Land Tiles Tab: Terrain tile art viewer, inspector, and editor with export/import.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from uofiddler.core.art import ArtManager
from uofiddler.core.tiledata import TileDataManager
from uofiddler.gui.widgets.image_canvas import ImageCanvas
from uofiddler.gui.widgets.virtual_tile_view import TileBrowserWidget


class LandTilesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.art_mgr = ArtManager.get_instance()
        self.tile_mgr = TileDataManager.get_instance()
        self.current_tile_id = 0
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Browser Widget (Grid default + List view option)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.browser = TileBrowserWidget(self)
        count = len(self.tile_mgr.land_tiles) if self.tile_mgr.land_tiles else 0x4000
        self.browser.set_data(
            count=count,
            get_label=self.get_land_label,
            get_image=self.get_land_thumb,
        )
        left_layout.addWidget(self.browser)

        splitter.addWidget(left_widget)

        # Right panel: Image Canvas, Details, and Tools
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Canvas
        self.canvas = ImageCanvas(self)
        self.canvas.setMinimumSize(250, 250)
        right_layout.addWidget(self.canvas, stretch=2)

        # Properties
        prop_box = QGroupBox("Land Tile Properties (TileData)")
        prop_layout = QFormLayout(prop_box)
        self.lbl_id = QLabel("0 (0x0000)")
        self.lbl_name = QLabel("-")
        self.lbl_flags = QLabel("-")
        self.lbl_tex = QLabel("-")

        prop_layout.addRow("Tile ID:", self.lbl_id)
        prop_layout.addRow("Name:", self.lbl_name)
        prop_layout.addRow("Flags:", self.lbl_flags)
        prop_layout.addRow("Texture ID:", self.lbl_tex)
        right_layout.addWidget(prop_box)

        # Buttons: Export, Replace, Remove
        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Export PNG")
        export_btn.clicked.connect(self.on_export)
        replace_btn = QPushButton("Replace Image")
        replace_btn.clicked.connect(self.on_replace)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.on_remove)

        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(replace_btn)
        btn_layout.addWidget(remove_btn)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

        self.browser.itemSelected.connect(self.update_display)
        if count > 0:
            self.select_tile(0)

    def get_land_label(self, tile_id: int) -> str:
        tile = self.tile_mgr.get_land(tile_id)
        return tile.name if tile and tile.name else ""

    def get_land_thumb(self, tile_id: int):
        return self.art_mgr.get_land(tile_id)

    def select_tile(self, tile_id: int):
        self.browser.select_id(tile_id)

    def update_display(self, tile_id: int):
        self.current_tile_id = tile_id
        img = self.art_mgr.get_land(tile_id)
        self.canvas.set_pil_image(img)

        tile = self.tile_mgr.get_land(tile_id)
        self.lbl_id.setText(f"{tile_id} (0x{tile_id:04X})")
        if tile:
            self.lbl_name.setText(tile.name or "(none)")
            self.lbl_flags.setText(f"0x{tile.flags:08X}")
            self.lbl_tex.setText(f"0x{tile.texture_id:04X} ({tile.texture_id})")
        else:
            self.lbl_name.setText("(none)")
            self.lbl_flags.setText("-")
            self.lbl_tex.setText("-")

    def on_export(self):
        img = self.art_mgr.get_land(self.current_tile_id)
        if not img:
            QMessageBox.warning(self, "Export", "Selected land tile has no image.")
            return

        fn, _ = QFileDialog.getSaveFileName(self, "Export Land Tile Image", f"land_0x{self.current_tile_id:04X}.png", "PNG Files (*.png);;BMP Files (*.bmp)")
        if fn:
            img.save(fn)
            QMessageBox.information(self, "Export", f"Saved to {fn}")

    def on_replace(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Replace Land Tile Image", "", "Images (*.png *.bmp *.jpg)")
        if fn:
            try:
                from PIL import Image
                new_img = Image.open(fn)
                self.art_mgr.replace_land(self.current_tile_id, new_img)
                self.browser.refresh()
                self.update_display(self.current_tile_id)
                QMessageBox.information(self, "Replace", f"Replaced land tile 0x{self.current_tile_id:04X}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {e}")

    def on_remove(self):
        self.art_mgr.remove_land(self.current_tile_id)
        self.browser.refresh()
        self.update_display(self.current_tile_id)
