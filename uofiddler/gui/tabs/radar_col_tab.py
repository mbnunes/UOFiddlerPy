"""
RadarColor Tab: Minimap radar color viewer, editor, auto-color generator, and radarcol.mul saver.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QRadioButton, QColorDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap, QPainter
from uofiddler.core.radar_col import RadarColManager
from uofiddler.core.tiledata import TileDataManager
from uofiddler.core.art import ArtManager
from uofiddler.core.colors import color16_to_rgba, rgba_to_color16
from uofiddler.gui.widgets.virtual_tile_view import TileBrowserWidget
from uofiddler.gui.widgets.image_canvas import ImageCanvas


class RadarColorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radar_mgr = RadarColManager.get_instance()
        self.tile_mgr = TileDataManager.get_instance()
        self.art_mgr = ArtManager.get_instance()
        self.is_items_mode = True
        self.current_id = 0
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Mode and Browser
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        mode_box = QHBoxLayout()
        self.rb_items = QRadioButton("Items")
        self.rb_land = QRadioButton("Land Tiles")
        self.rb_items.setChecked(True)
        self.rb_items.toggled.connect(self.on_mode_toggled)
        mode_box.addWidget(self.rb_items)
        mode_box.addWidget(self.rb_land)
        left_layout.addLayout(mode_box)

        # Browser (Grid default + List view option)
        self.browser = TileBrowserWidget(self)
        left_layout.addWidget(self.browser)

        splitter.addWidget(left_widget)

        # Right panel: Tile Image Canvas, Current Radar Color swatch, Auto calculate
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.canvas = ImageCanvas(self)
        self.canvas.setMinimumSize(200, 200)
        right_layout.addWidget(self.canvas, stretch=2)

        prop_box = QGroupBox("Radar Color Details")
        form_layout = QFormLayout(prop_box)
        self.lbl_id = QLabel("0 (0x0000)")
        self.lbl_color_hex = QLabel("0x0000")
        self.swatch_widget = QLabel()
        self.swatch_widget.setFixedSize(60, 26)
        self.swatch_widget.setStyleSheet("border: 1px solid #555;")

        form_layout.addRow("ID:", self.lbl_id)
        form_layout.addRow("16-bit Color:", self.lbl_color_hex)
        form_layout.addRow("Color Swatch:", self.swatch_widget)
        right_layout.addWidget(prop_box)

        # Buttons
        btn_layout = QVBoxLayout()
        pick_color_btn = QPushButton("Pick Color...")
        pick_color_btn.clicked.connect(self.on_pick_color)
        auto_calc_btn = QPushButton("Auto-Generate from Image")
        auto_calc_btn.clicked.connect(self.on_auto_calc)
        save_btn = QPushButton("Save radarcol.mul")
        save_btn.clicked.connect(self.on_save)

        btn_layout.addWidget(pick_color_btn)
        btn_layout.addWidget(auto_calc_btn)
        btn_layout.addWidget(save_btn)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        self.browser.itemSelected.connect(self.update_display)
        self.reset_model()
        self.select_row(0)

    def get_radar_swatch(self, idx: int) -> Optional[QPixmap]:
        c16 = self.radar_mgr.get_item_color(idx) if self.is_items_mode else self.radar_mgr.get_land_color(idx)
        r, g, b, a = color16_to_rgba(c16 | 0x8000)
        pix = QPixmap(18, 18)
        pix.fill(QColor(r, g, b))
        painter = QPainter(pix)
        border_col = QColor(240, 240, 240) if (0.299 * r + 0.587 * g + 0.114 * b) < 128 else QColor(30, 30, 30)
        painter.setPen(border_col)
        painter.drawRect(0, 0, 17, 17)
        painter.end()
        return pix

    def get_radar_tooltip(self, idx: int) -> str:
        c16 = self.radar_mgr.get_item_color(idx) if self.is_items_mode else self.radar_mgr.get_land_color(idx)
        name = self.get_item_label(idx) if self.is_items_mode else self.get_land_label(idx)
        r, g, b, _ = color16_to_rgba(c16 | 0x8000)
        title = f"0x{idx:04X} ({idx})"
        if name:
            title += f" - {name}"
        return f"{title}\nRadar Color: 0x{c16:04X} (RGB: {r},{g},{b})"

    def reset_model(self):
        count = len(self.tile_mgr.item_tiles) if self.is_items_mode else len(self.tile_mgr.land_tiles)
        get_lbl = self.get_item_label if self.is_items_mode else self.get_land_label
        get_thumb = self.art_mgr.get_static if self.is_items_mode else self.art_mgr.get_land

        self.browser.set_data(
            count=count,
            get_label=get_lbl,
            get_image=get_thumb,
            get_swatch=self.get_radar_swatch,
            get_tooltip=self.get_radar_tooltip,
            columns=["ID", "Hex", "Name", "Radar Color", "Graphic"],
        )

    def get_item_label(self, idx: int) -> str:
        tile = self.tile_mgr.get_item(idx)
        return tile.name if tile and tile.name else ""

    def get_land_label(self, idx: int) -> str:
        tile = self.tile_mgr.get_land(idx)
        return tile.name if tile and tile.name else ""

    def on_mode_toggled(self):
        self.is_items_mode = self.rb_items.isChecked()
        self.reset_model()

    def select_row(self, row: int):
        self.browser.select_id(row)

    def update_display(self, row: int):
        self.current_id = row
        img = self.art_mgr.get_static(row) if self.is_items_mode else self.art_mgr.get_land(row)
        self.canvas.set_pil_image(img)

        c16 = self.radar_mgr.get_item_color(row) if self.is_items_mode else self.radar_mgr.get_land_color(row)
        r, g, b, a = color16_to_rgba(c16 | 0x8000)

        self.lbl_id.setText(f"{row} (0x{row:04X})")
        self.lbl_color_hex.setText(f"0x{c16:04X} (R:{r} G:{g} B:{b})")
        self.swatch_widget.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid #fff;")

    def on_pick_color(self):
        c16 = self.radar_mgr.get_item_color(self.current_id) if self.is_items_mode else self.radar_mgr.get_land_color(self.current_id)
        r, g, b, _ = color16_to_rgba(c16 | 0x8000)
        color = QColorDialog.getColor(initial=QColor(r, g, b), parent=self, title="Pick Radar Color")
        if color.isValid():
            new_c16 = rgba_to_color16(color.red(), color.green(), color.blue()) & 0x7FFF
            if self.is_items_mode:
                self.radar_mgr.set_item_color(self.current_id, new_c16)
            else:
                self.radar_mgr.set_land_color(self.current_id, new_c16)
            self.browser.refresh()
            self.update_display(self.current_id)

    def on_auto_calc(self):
        img = self.art_mgr.get_static(self.current_id) if self.is_items_mode else self.art_mgr.get_land(self.current_id)
        if not img:
            QMessageBox.warning(self, "Auto-Generate", "Tile has no image.")
            return

        avg_c16 = self.radar_mgr.calculate_average_color(img)
        if self.is_items_mode:
            self.radar_mgr.set_item_color(self.current_id, avg_c16)
        else:
            self.radar_mgr.set_land_color(self.current_id, avg_c16)
        self.browser.refresh()
        self.update_display(self.current_id)
        QMessageBox.information(self, "Auto-Generate", f"Calculated radar color: 0x{avg_c16:04X}")

    def on_save(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save radarcol.mul", "radarcol.mul", "MUL Files (*.mul)")
        if fn:
            try:
                self.radar_mgr.save(fn)
                QMessageBox.information(self, "Saved", f"Successfully saved radarcol.mul to {fn}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save radarcol.mul: {e}")
