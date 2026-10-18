"""
Zoomable, pannable image canvas with transparency checkerboard background.
"""

from typing import Optional
from PIL import Image
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPixmap, QImage, QColor, QWheelEvent, QMouseEvent, QPen
from PyQt6.QtCore import Qt, QPoint, QRectF


class ImageCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._pixmap: Optional[QPixmap] = None
        self._zoom: float = 1.0
        self._pan: QPoint = QPoint(0, 0)
        self._drag_start: Optional[QPoint] = None
        self._show_grid: bool = True
        self._overlay_rect: Optional[QRectF] = None
        self._overlay_label: Optional[str] = None
        self.setStyleSheet("background-color: #141418;")

    def set_pil_image(self, img: Optional[Image.Image]):
        if img is None:
            self._pixmap = None
        else:
            rgba = img.convert("RGBA")
            data = rgba.tobytes("raw", "RGBA")
            qimg = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888)
            self._pixmap = QPixmap.fromImage(qimg)
        self.reset_view()
        self.update()

    def set_qimage(self, qimg: Optional[QImage]):
        if qimg is None:
            self._pixmap = None
        else:
            self._pixmap = QPixmap.fromImage(qimg)
        self.reset_view()
        self.update()

    def reset_view(self):
        self._zoom = 1.0
        if self._pixmap and self.width() > 0 and self.height() > 0:
            pw, ph = self._pixmap.width(), self._pixmap.height()
            self._pan = QPoint((self.width() - pw) // 2, (self.height() - ph) // 2)
        else:
            self._pan = QPoint(0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

        # Draw dark canvas background
        painter.fillRect(self.rect(), QColor("#141418"))

        if not self._pixmap or self._pixmap.isNull():
            painter.setPen(QColor("#606070"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Image Selected")
            return

        target_w = int(self._pixmap.width() * self._zoom)
        target_h = int(self._pixmap.height() * self._zoom)
        tx = self._pan.x()
        ty = self._pan.y()

        # Draw checkerboard behind image
        if self._show_grid:
            cell_size = 8
            c1 = QColor("#22222a")
            c2 = QColor("#1a1a20")
            for cy in range(ty, ty + target_h, cell_size):
                for cx in range(tx, tx + target_w, cell_size):
                    w = min(cell_size, (tx + target_w) - cx)
                    h = min(cell_size, (ty + target_h) - cy)
                    color = c1 if ((cx - tx) // cell_size + (cy - ty) // cell_size) % 2 == 0 else c2
                    painter.fillRect(cx, cy, w, h, color)

        # Draw scaled pixmap
        target_rect = QRectF(tx, ty, target_w, target_h)
        painter.drawPixmap(target_rect, self._pixmap, QRectF(self._pixmap.rect()))

        # Draw subtle border around image
        painter.setPen(QPen(QColor("#3f51b5"), 1, Qt.PenStyle.DashLine))
        painter.drawRect(target_rect)

        # Draw container bounding box overlay if specified
        if self._overlay_rect and not self._overlay_rect.isNull():
            ox = tx + self._overlay_rect.x() * self._zoom
            oy = ty + self._overlay_rect.y() * self._zoom
            ow = self._overlay_rect.width() * self._zoom
            oh = self._overlay_rect.height() * self._zoom
            o_rect = QRectF(ox, oy, ow, oh)

            # Draw semi-transparent green fill
            painter.fillRect(o_rect, QColor(76, 175, 80, 60))

            # Draw crisp border
            painter.setPen(QPen(QColor("#4caf50"), 2, Qt.PenStyle.SolidLine))
            painter.drawRect(o_rect)

            if self._overlay_label:
                painter.setPen(QColor("#a5d6a7"))
                painter.drawText(
                    o_rect.adjusted(6, 6, -6, -6),
                    Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                    self._overlay_label
                )

    def set_overlay_rect(self, rect: Optional[Tuple[int, int, int, int]] = None, label: Optional[str] = None):
        """
        Sets a bounding box overlay in image pixel coordinates: (x, y, width, height).
        Pass None to clear the overlay.
        """
        if rect:
            self._overlay_rect = QRectF(rect[0], rect[1], rect[2], rect[3])
            self._overlay_label = label
        else:
            self._overlay_rect = None
            self._overlay_label = None
        self.update()

    def wheelEvent(self, event: QWheelEvent):
        degrees = event.angleDelta().y() / 8.0
        steps = degrees / 15.0
        factor = 1.25 ** steps

        # Zoom centered on mouse
        mouse_pos = event.position().toPoint()
        old_zoom = self._zoom
        self._zoom = max(0.2, min(32.0, self._zoom * factor))

        # Adjust pan so mouse point remains stationary
        ratio = self._zoom / old_zoom
        self._pan = mouse_pos - (mouse_pos - self._pan) * ratio
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self._drag_start = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start is not None:
            delta = event.pos() - self._drag_start
            self._pan += delta
            self._drag_start = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._zoom == 1.0 and self._pixmap:
            self.reset_view()
