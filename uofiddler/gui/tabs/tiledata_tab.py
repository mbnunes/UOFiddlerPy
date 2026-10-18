"""
TileData Tab: Comprehensive TileData editor for both ItemData and LandData.
Provides full bitfield flag checkboxes and property editors with direct tiledata.mul save support.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QRadioButton, QButtonGroup, QScrollArea, QCheckBox, QGridLayout, QSpinBox
)
from PyQt6.QtCore import Qt
from uofiddler.core.tiledata import TileDataManager, TileFlag, ItemTileData, LandTileData
from uofiddler.gui.widgets.virtual_tile_view import TileBrowserWidget
from uofiddler.core.art import ArtManager


ALL_TILE_FLAGS = [
    ("Background", TileFlag.Background),
    ("Weapon", TileFlag.Weapon),
    ("Transparent", TileFlag.Transparent),
    ("Translucent", TileFlag.Translucent),
    ("Wall", TileFlag.Wall),
    ("Damaging", TileFlag.Damaging),
    ("Impassable", TileFlag.Impassable),
    ("Wet", TileFlag.Wet),
    ("Unknown1", TileFlag.Unknown1),
    ("Surface", TileFlag.Surface),
    ("Bridge", TileFlag.Bridge),
    ("Generic", TileFlag.Generic),
    ("Window", TileFlag.Window),
    ("NoShoot", TileFlag.NoShoot),
    ("PrefixA", TileFlag.PrefixA),
    ("PrefixAn", TileFlag.PrefixAn),
    ("Internal", TileFlag.Internal),
    ("Foliage", TileFlag.Foliage),
    ("PartialHue", TileFlag.PartialHue),
    ("Unknown2", TileFlag.Unknown2),
    ("Map", TileFlag.Map),
    ("Container", TileFlag.Container),
    ("Wearable", TileFlag.Wearable),
    ("LightSource", TileFlag.LightSource),
    ("Animated", TileFlag.Animated),
    ("NoDiagonal", TileFlag.NoDiagonal),
    ("Unknown3", TileFlag.Unknown3),
    ("Armor", TileFlag.Armor),
    ("Roof", TileFlag.Roof),
    ("Door", TileFlag.Door),
    ("StairBack", TileFlag.StairBack),
    ("StairRight", TileFlag.StairRight),
    ("AlphaBlend", TileFlag.AlphaBlend),
    ("UseNewArt", TileFlag.UseNewArt),
    ("ArtUsed", TileFlag.ArtUsed),
    ("NoHouse", TileFlag.NoHouse),
    ("NoDraw", TileFlag.NoDraw),
    ("HoverOver", TileFlag.HoverOver),
]


class TileDataTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tile_mgr = TileDataManager.get_instance()
        self.art_mgr = ArtManager.get_instance()
        self.is_items_mode = True
        self.current_id = 0
        self.flag_checkboxes: dict[TileFlag, QCheckBox] = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Mode switch & List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Radio buttons: Items vs Land
        mode_box = QHBoxLayout()
        self.rb_items = QRadioButton("Items (ItemData)")
        self.rb_land = QRadioButton("Land Tiles (LandData)")
        self.rb_items.setChecked(True)
        self.rb_items.toggled.connect(self.on_mode_toggled)

        mode_box.addWidget(self.rb_items)
        mode_box.addWidget(self.rb_land)
        left_layout.addLayout(mode_box)

        # Tile Browser (Grid default + List option)
        self.browser = TileBrowserWidget(self)
        left_layout.addWidget(self.browser)

        splitter.addWidget(left_widget)

        # Right panel: Form inputs and flag checkboxes
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Form fields
        prop_box = QGroupBox("Properties")
        form_layout = QFormLayout(prop_box)

        self.txt_name = QLineEdit()
        self.spin_weight = QSpinBox()
        self.spin_weight.setRange(0, 255)
        self.spin_quality = QSpinBox()
        self.spin_quality.setRange(0, 255)
        self.spin_height = QSpinBox()
        self.spin_height.setRange(0, 255)
        self.spin_anim = QSpinBox()
        self.spin_anim.setRange(0, 65535)
        self.spin_hue = QSpinBox()
        self.spin_hue.setRange(0, 255)
        self.spin_texture = QSpinBox()
        self.spin_texture.setRange(0, 65535)

        form_layout.addRow("Name:", self.txt_name)
        form_layout.addRow("Weight:", self.spin_weight)
        form_layout.addRow("Quality / Layer:", self.spin_quality)
        form_layout.addRow("Height:", self.spin_height)
        form_layout.addRow("Anim ID:", self.spin_anim)
        form_layout.addRow("Hue:", self.spin_hue)
        form_layout.addRow("Texture ID (Land):", self.spin_texture)

        scroll_layout.addWidget(prop_box)

        # Flags checkboxes
        flags_box = QGroupBox("Tile Flags")
        flags_grid = QGridLayout(flags_box)

        self.flag_checkboxes.clear()
        col = 0
        row = 0
        for name, flag_enum in ALL_TILE_FLAGS:
            cb = QCheckBox(name)
            flags_grid.addWidget(cb, row, col)
            self.flag_checkboxes[flag_enum] = cb
            row += 1
            if row >= 10:
                row = 0
                col += 1

        scroll_layout.addWidget(flags_box)
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)

        # Action Buttons
        btn_bar = QHBoxLayout()
        apply_btn = QPushButton("Apply Changes")
        apply_btn.clicked.connect(self.on_apply)
        save_btn = QPushButton("Save tiledata.mul")
        save_btn.clicked.connect(self.on_save)

        btn_bar.addWidget(apply_btn)
        btn_bar.addWidget(save_btn)
        right_layout.addLayout(btn_bar)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        self.browser.itemSelected.connect(self.load_row_data)
        self.reset_model()
        self.select_row(0)

    def reset_model(self):
        count = len(self.tile_mgr.item_tiles) if self.is_items_mode else len(self.tile_mgr.land_tiles)
        get_lbl = self.get_item_label if self.is_items_mode else self.get_land_label
        get_thumb = self.art_mgr.get_static if self.is_items_mode else self.art_mgr.get_land
        self.browser.set_data(count=count, get_label=get_lbl, get_image=get_thumb)

    def get_item_label(self, idx: int) -> str:
        tile = self.tile_mgr.get_item(idx)
        return tile.name if tile and tile.name else ""

    def get_land_label(self, idx: int) -> str:
        tile = self.tile_mgr.get_land(idx)
        return tile.name if tile and tile.name else ""

    def on_mode_toggled(self):
        self.is_items_mode = self.rb_items.isChecked()
        self.spin_weight.setEnabled(self.is_items_mode)
        self.spin_quality.setEnabled(self.is_items_mode)
        self.spin_height.setEnabled(self.is_items_mode)
        self.spin_anim.setEnabled(self.is_items_mode)
        self.spin_hue.setEnabled(self.is_items_mode)
        self.spin_texture.setEnabled(not self.is_items_mode)
        self.reset_model()

    def select_row(self, row: int):
        self.browser.select_id(row)

    def load_row_data(self, row: int):
        self.current_id = row
        if self.is_items_mode:
            tile = self.tile_mgr.get_item(row)
            if not tile:
                return
            self.txt_name.setText(tile.name)
            self.spin_weight.setValue(tile.weight)
            self.spin_quality.setValue(tile.quality)
            self.spin_height.setValue(tile.height)
            self.spin_anim.setValue(tile.anim_id)
            self.spin_hue.setValue(tile.hue)
            flags = tile.flags
        else:
            tile = self.tile_mgr.get_land(row)
            if not tile:
                return
            self.txt_name.setText(tile.name)
            self.spin_texture.setValue(tile.texture_id)
            flags = tile.flags

        for flag_enum, cb in self.flag_checkboxes.items():
            cb.setChecked(bool(flags & flag_enum.value))

    def on_apply(self):
        # Gather flags
        flags = 0
        for flag_enum, cb in self.flag_checkboxes.items():
            if cb.isChecked():
                flags |= flag_enum.value

        if self.is_items_mode:
            tile = self.tile_mgr.get_item(self.current_id)
            if tile:
                tile.name = self.txt_name.text()[:20]
                tile.weight = self.spin_weight.value()
                tile.quality = self.spin_quality.value()
                tile.height = self.spin_height.value()
                tile.anim_id = self.spin_anim.value()
                tile.hue = self.spin_hue.value()
                tile.flags = flags
        else:
            tile = self.tile_mgr.get_land(self.current_id)
            if tile:
                tile.name = self.txt_name.text()[:20]
                tile.texture_id = self.spin_texture.value()
                tile.flags = flags

        QMessageBox.information(self, "Applied", f"Applied changes to ID {self.current_id}")

    def on_save(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save tiledata.mul", "tiledata.mul", "MUL Files (*.mul)")
        if fn:
            try:
                self.tile_mgr.save(fn)
                QMessageBox.information(self, "Saved", f"Successfully saved tiledata.mul to {fn}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save tiledata.mul: {e}")
