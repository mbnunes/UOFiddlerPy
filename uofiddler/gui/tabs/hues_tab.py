"""
Hues Tab: 3000 Hues palette editor, name editor, item test preview, and hues.mul saver.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QColorDialog, QSpinBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPixmap, QPainter
from uofiddler.core.hues import HuesManager, Hue
from uofiddler.core.art import ArtManager
from uofiddler.core.colors import color16_to_rgba, rgba_to_color16
from uofiddler.gui.widgets.color_bar import ColorBar
from uofiddler.gui.widgets.image_canvas import ImageCanvas
from uofiddler.gui.widgets.virtual_tile_view import TileBrowserWidget


class HuesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hue_mgr = HuesManager.get_instance()
        self.art_mgr = ArtManager.get_instance()
        self.current_hue_id = 0
        self.selected_swatch_idx = 0
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Hues Browser (Grid default with color swatch + List view)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.browser = TileBrowserWidget(self, grid_size=QSize(60, 60), icon_size=QSize(36, 36))
        count = len(self.hue_mgr.hues) if self.hue_mgr.hues else 3000
        self.browser.set_data(
            count=count,
            get_label=self.get_hue_label,
            get_swatch=self.get_hue_swatch,
            get_text=lambda h_id: f"{h_id}",
            get_tooltip=self.get_hue_tooltip,
            columns=["ID", "Hex", "Name", "Color"],
        )
        left_layout.addWidget(self.browser)

        splitter.addWidget(left_widget)

        # Right panel: 32-Color Palette Bar, Editor, Item Tester
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 32-Color Palette Bar
        bar_box = QGroupBox("32-Color Palette Bar (Click a color to edit)")
        bar_layout = QVBoxLayout(bar_box)
        self.color_bar = ColorBar(self)
        self.color_bar.colorSelected.connect(self.on_swatch_selected)
        bar_layout.addWidget(self.color_bar)

        edit_color_btn = QPushButton("Edit Selected Color...")
        edit_color_btn.clicked.connect(self.on_edit_color)
        bar_layout.addWidget(edit_color_btn)
        right_layout.addWidget(bar_box)

        # Hue Properties
        prop_box = QGroupBox("Hue Properties")
        form_layout = QFormLayout(prop_box)
        self.lbl_id = QLabel("0 (0x0000)")
        self.txt_name = QLineEdit()
        form_layout.addRow("Hue ID:", self.lbl_id)
        form_layout.addRow("Name:", self.txt_name)
        apply_name_btn = QPushButton("Apply Name")
        apply_name_btn.clicked.connect(self.on_apply_name)
        form_layout.addRow("", apply_name_btn)
        right_layout.addWidget(prop_box)

        # Item Hue Preview Tester
        test_box = QGroupBox("Item Hue Preview Tester")
        test_layout = QVBoxLayout(test_box)
        item_sel_layout = QHBoxLayout()
        item_sel_layout.addWidget(QLabel("Test Item ID:"))
        self.test_item_spin = QSpinBox()
        self.test_item_spin.setRange(0, 0xFFFF)
        self.test_item_spin.setValue(0x0EED)  # Gold coins
        self.test_item_spin.valueChanged.connect(self.update_preview)
        item_sel_layout.addWidget(self.test_item_spin)
        test_layout.addLayout(item_sel_layout)

        self.canvas = ImageCanvas(self)
        self.canvas.setMinimumSize(200, 200)
        test_layout.addWidget(self.canvas)
        right_layout.addWidget(test_box, stretch=2)

        # Save hues.mul
        save_btn = QPushButton("Save hues.mul")
        save_btn.clicked.connect(self.on_save)
        right_layout.addWidget(save_btn)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        self.browser.itemSelected.connect(self.load_hue)
        if count > 0:
            self.select_hue(0)

    def get_hue_label(self, hue_id: int) -> str:
        hue = self.hue_mgr.get_hue(hue_id)
        return hue.name if hue and hue.name else ""

    def get_hue_tooltip(self, hue_id: int) -> str:
        hue = self.hue_mgr.get_hue(hue_id)
        name = hue.name if hue and hue.name else ""
        return f"Hue {hue_id} (0x{hue_id:04X})\n{name}" if name else f"Hue {hue_id} (0x{hue_id:04X})"

    def get_hue_swatch(self, hue_id: int) -> Optional[QPixmap]:
        hue = self.hue_mgr.get_hue(hue_id)
        if not hue or not hue.colors:
            return None
        # Representative color (middle color of the 32 palette colors)
        c16 = hue.colors[len(hue.colors) // 2]
        r, g, b, _ = color16_to_rgba(c16 | 0x8000)
        pix = QPixmap(36, 36)
        pix.fill(QColor(r, g, b))
        painter = QPainter(pix)
        painter.setPen(QColor(60, 60, 75))
        painter.drawRect(0, 0, 35, 35)
        painter.end()
        return pix

    def select_hue(self, hue_id: int):
        self.browser.select_id(hue_id)

    def load_hue(self, hue_id: int):
        self.current_hue_id = hue_id
        hue = self.hue_mgr.get_hue(hue_id)
        if not hue:
            return

        self.lbl_id.setText(f"{hue_id} (0x{hue_id:04X})")
        self.txt_name.setText(hue.name)
        self.color_bar.set_colors(hue.colors)
        self.update_preview()

    def on_swatch_selected(self, index: int, color16: int):
        self.selected_swatch_idx = index

    def on_edit_color(self):
        hue = self.hue_mgr.get_hue(self.current_hue_id)
        if not hue or self.selected_swatch_idx >= len(hue.colors):
            return

        c16 = hue.colors[self.selected_swatch_idx]
        r, g, b, a = color16_to_rgba(c16 | 0x8000)

        color = QColorDialog.getColor(initial=QColor(r, g, b), parent=self, title="Select Color for Palette Swatch")
        if color.isValid():
            new_c16 = rgba_to_color16(color.red(), color.green(), color.blue()) & 0x7FFF
            hue.colors[self.selected_swatch_idx] = new_c16
            self.color_bar.set_colors(hue.colors)
            self.browser.refresh()
            self.update_preview()

    def update_preview(self):
        item_id = self.test_item_spin.value()
        base_img = self.art_mgr.get_static(item_id)
        if base_img:
            hue = self.hue_mgr.get_hue(self.current_hue_id)
            hued_img = hue.apply_to(base_img) if hue else base_img
            self.canvas.set_pil_image(hued_img)
        else:
            self.canvas.set_pil_image(None)

    def on_apply_name(self):
        hue = self.hue_mgr.get_hue(self.current_hue_id)
        if hue:
            hue.name = self.txt_name.text()[:20]
            self.browser.refresh()
            QMessageBox.information(self, "Applied", "Hue name updated.")

    def on_save(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save hues.mul", "hues.mul", "MUL Files (*.mul)")
        if fn:
            try:
                self.hue_mgr.save(fn)
                QMessageBox.information(self, "Saved", f"Successfully saved hues.mul to {fn}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save hues.mul: {e}")
