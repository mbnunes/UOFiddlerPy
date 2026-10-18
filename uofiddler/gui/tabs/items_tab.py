"""
Items Tab: Static item art viewer, inspector, and editor with hue testing and export/import.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox, QSpinBox
)
from PyQt6.QtCore import Qt
from uofiddler.core.art import ArtManager
from uofiddler.core.tiledata import TileDataManager
from uofiddler.core.hues import HuesManager
from uofiddler.gui.widgets.image_canvas import ImageCanvas
from uofiddler.gui.widgets.virtual_tile_view import TileBrowserWidget


class ItemsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.art_mgr = ArtManager.get_instance()
        self.tile_mgr = TileDataManager.get_instance()
        self.hue_mgr = HuesManager.get_instance()
        self.current_item_id = 0
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Browser Widget (Grid default + List view option)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.browser = TileBrowserWidget(self)
        count = len(self.tile_mgr.item_tiles) if self.tile_mgr.item_tiles else 0x10000
        self.browser.set_data(
            count=count,
            get_label=self.get_item_label,
            get_image=self.get_item_thumb,
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

        # Hue testing
        hue_box = QGroupBox("Test Hue")
        hue_layout = QHBoxLayout(hue_box)
        self.hue_spin = QSpinBox()
        self.hue_spin.setRange(0, 2999)
        self.hue_spin.valueChanged.connect(self.on_hue_changed)
        hue_layout.addWidget(QLabel("Hue ID:"))
        hue_layout.addWidget(self.hue_spin)
        right_layout.addWidget(hue_box)

        # Properties
        prop_box = QGroupBox("Item Properties (TileData)")
        prop_layout = QFormLayout(prop_box)
        self.lbl_id = QLabel("0 (0x0000)")
        self.lbl_name = QLabel("-")
        self.lbl_flags = QLabel("-")
        self.lbl_weight = QLabel("-")
        self.lbl_height = QLabel("-")
        self.lbl_anim = QLabel("-")

        prop_layout.addRow("Item ID:", self.lbl_id)
        prop_layout.addRow("Name:", self.lbl_name)
        prop_layout.addRow("Flags:", self.lbl_flags)
        prop_layout.addRow("Weight:", self.lbl_weight)
        prop_layout.addRow("Height:", self.lbl_height)
        prop_layout.addRow("Anim ID:", self.lbl_anim)
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
        # Select item 0
        if count > 0:
            self.select_item(0)

    def get_item_label(self, item_id: int) -> str:
        tile = self.tile_mgr.get_item(item_id)
        return tile.name if tile and tile.name else ""

    def get_item_thumb(self, item_id: int):
        return self.art_mgr.get_static(item_id)

    def select_item(self, item_id: int):
        self.browser.select_id(item_id)

    def update_display(self, item_id: int):
        self.current_item_id = item_id
        img = self.art_mgr.get_static(item_id)

        # Apply hue if selected
        hue_id = self.hue_spin.value()
        if hue_id > 0 and img:
            hue = self.hue_mgr.get_hue(hue_id)
            if hue:
                tile = self.tile_mgr.get_item(item_id)
                partial = bool(tile and (tile.flags & 0x40000))  # PartialHue flag
                img = hue.apply_to(img, only_gray=partial)

        self.canvas.set_pil_image(img)

        # Update properties
        tile = self.tile_mgr.get_item(item_id)
        self.lbl_id.setText(f"{item_id} (0x{item_id:04X})")
        if tile:
            self.lbl_name.setText(tile.name or "(none)")
            self.lbl_flags.setText(f"0x{tile.flags:08X}")
            self.lbl_weight.setText(str(tile.weight))
            self.lbl_height.setText(str(tile.height))
            self.lbl_anim.setText(f"0x{tile.anim_id:04X} ({tile.anim_id})")
        else:
            self.lbl_name.setText("(none)")
            self.lbl_flags.setText("-")
            self.lbl_weight.setText("-")
            self.lbl_height.setText("-")
            self.lbl_anim.setText("-")

    def on_hue_changed(self):
        self.update_display(self.current_item_id)

    def on_search(self):
        text = self.search_input.text().strip()
        if not text:
            return

        # Try hex or decimal ID
        try:
            if text.lower().startswith("0x"):
                target_id = int(text, 16)
            else:
                target_id = int(text)
            self.select_item(target_id)
            return
        except ValueError:
            pass

        # Search by name
        q = text.lower()
        for i, tile in enumerate(self.tile_mgr.item_tiles):
            if tile and tile.name and q in tile.name.lower():
                self.select_item(i)
                return

        QMessageBox.information(self, "Search", f"No item found matching '{text}'")

    def on_export(self):
        img = self.art_mgr.get_static(self.current_item_id)
        if not img:
            QMessageBox.warning(self, "Export", "Selected item has no image.")
            return

        fn, _ = QFileDialog.getSaveFileName(self, "Export Item Image", f"item_0x{self.current_item_id:04X}.png", "PNG Files (*.png);;BMP Files (*.bmp)")
        if fn:
            img.save(fn)
            QMessageBox.information(self, "Export", f"Saved to {fn}")

    def on_replace(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Replace Item Image", "", "Images (*.png *.bmp *.jpg)")
        if fn:
            try:
                from PIL import Image
                new_img = Image.open(fn)
                self.art_mgr.replace_static(self.current_item_id, new_img)
                self.browser.refresh()
                self.update_display(self.current_item_id)
                QMessageBox.information(self, "Replace", f"Replaced item 0x{self.current_item_id:04X}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {e}")

    def on_remove(self):
        self.art_mgr.remove_static(self.current_item_id)
        self.browser.refresh()
        self.update_display(self.current_item_id)
