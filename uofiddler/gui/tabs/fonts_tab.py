"""
Fonts Tab: ASCII fonts viewer, glyph inspector, and live text rendering tester.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt
from uofiddler.core.fonts import FontsManager
from uofiddler.gui.widgets.image_canvas import ImageCanvas


class FontsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fonts_mgr = FontsManager.get_instance()
        self.current_font_idx = 0
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Controls
        ctrl_box = QGroupBox("Font Controls")
        ctrl_layout = QHBoxLayout(ctrl_box)

        ctrl_layout.addWidget(QLabel("Font Index:"))
        self.font_combo = QComboBox()
        for i in range(10):
            font = self.fonts_mgr.ascii_fonts[i]
            h_str = f" (Height: {font.height}px)" if font else " (empty)"
            self.font_combo.addItem(f"Font {i}{h_str}", i)
        self.font_combo.currentIndexChanged.connect(self.on_font_changed)
        ctrl_layout.addWidget(self.font_combo)

        ctrl_layout.addWidget(QLabel("Preview Text:"))
        self.txt_preview = QLineEdit("The quick brown fox jumps over the lazy dog! 1234567890")
        self.txt_preview.textChanged.connect(self.update_preview)
        ctrl_layout.addWidget(self.txt_preview, stretch=1)

        main_layout.addWidget(ctrl_box)

        # Canvas preview
        self.canvas = ImageCanvas(self)
        self.canvas.setMinimumSize(400, 300)
        main_layout.addWidget(self.canvas, stretch=1)

        self.update_preview()

    def on_font_changed(self):
        self.current_font_idx = self.font_combo.currentData() or 0
        self.update_preview()

    def update_preview(self):
        font = self.fonts_mgr.ascii_fonts[self.current_font_idx]
        if not font:
            self.canvas.set_pil_image(None)
            return

        text = self.txt_preview.text()
        img = font.render_text(text)
        self.canvas.set_pil_image(img)
