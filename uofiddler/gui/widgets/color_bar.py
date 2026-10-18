"""
ColorBar widget for displaying the 32 colors in an Ultima Online Hue palette.
"""

from typing import List, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, pyqtSignal
from uofiddler.core.colors import color16_to_rgba


class ColorBar(QWidget):
    colorSelected = pyqtSignal(int, int)  # color_index (0..31), color16

    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors: List[int] = [0] * 32
        self.selected_index: int = 0
        self.setFixedHeight(28)
        self.setMinimumWidth(320)

    def set_colors(self, colors: List[int]):
        self.colors = (colors + [0] * 32)[:32]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w = self.width()
        h = self.height()
        swatch_w = w / 32.0

        for i, c in enumerate(self.colors):
            r, g, b, a = color16_to_rgba(c | 0x8000)
            x1 = int(i * swatch_w)
            x2 = int((i + 1) * swatch_w)
            painter.fillRect(x1, 0, x2 - x1, h, QColor(r, g, b))

            if i == self.selected_index:
                painter.setPen(QPen(QColor("#ffffff"), 2))
                painter.drawRect(x1 + 1, 1, max(1, x2 - x1 - 2), h - 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            swatch_w = self.width() / 32.0
            idx = int(event.pos().x() / swatch_w)
            idx = max(0, min(31, idx))
            self.selected_index = idx
            self.colorSelected.emit(idx, self.colors[idx])
            self.update()
