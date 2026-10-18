"""
Interactive Google Maps-style world map viewer for Ultima Online.
Supports seamless smooth click-and-drag panning, cursor-centered mouse wheel zoom,
chunked on-demand tile caching, overview base layer, and world coordinate tracking.
"""

from typing import Dict, Tuple, Optional
from collections import OrderedDict
from PIL import Image
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QPixmap, QImage, QPen, QFont, QWheelEvent, QMouseEvent

from uofiddler.core.maps import MapManager


CHUNK_TILES = 128  # 16 blocks * 8 tiles = 128x128 tiles per chunk
BLOCKS_PER_CHUNK = CHUNK_TILES // 8  # 16 blocks


class InteractiveMapView(QWidget):
    """
    Fluid, Google Maps-style map canvas for Ultima Online worlds.
    """

    coordinatesChanged = pyqtSignal(int, int)  # Emits (cursor_x, cursor_y)
    centerChanged = pyqtSignal(int, int)       # Emits (center_x, center_y)
    zoomChanged = pyqtSignal(float)            # Emits zoom level

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        self.map_mgr = MapManager.get_instance()
        self.map_id = 0
        self.center_x: float = 1420.0  # Britain Bank default
        self.center_y: float = 1690.0
        self.zoom: float = 1.0         # 1.0 = 1 pixel per tile
        self.show_statics: bool = True

        self._is_dragging: bool = False
        self._last_mouse: QPoint = QPoint()
        self._chunk_cache: OrderedDict = OrderedDict()
        self._overview_pixmaps: Dict[int, QPixmap] = {}

        self.setStyleSheet("background-color: #0e0e13;")

    @property
    def current_map_info(self):
        return next((m for m in self.map_mgr.maps if m.map_id == self.map_id), self.map_mgr.maps[0])

    def set_map_id(self, map_id: int):
        if self.map_id != map_id:
            self.map_id = map_id
            m_info = self.current_map_info
            self.center_x = min(self.center_x, m_info.width)
            self.center_y = min(self.center_y, m_info.height)
            self.clear_cache()
            self.update()

    def set_show_statics(self, enabled: bool):
        if self.show_statics != enabled:
            self.show_statics = enabled
            self.clear_cache()
            self.update()

    def clear_cache(self):
        self._chunk_cache.clear()

    def go_to(self, wx: float, wy: float, zoom: Optional[float] = None):
        """Pans the map center directly to world coordinates (wx, wy)."""
        m_info = self.current_map_info
        self.center_x = max(0.0, min(float(m_info.width), float(wx)))
        self.center_y = max(0.0, min(float(m_info.height), float(wy)))
        if zoom is not None:
            self.zoom = max(0.08, min(16.0, float(zoom)))
            self.zoomChanged.emit(self.zoom)
        self.centerChanged.emit(int(self.center_x), int(self.center_y))
        self.update()

    def zoom_in(self, factor: float = 1.3):
        self._apply_zoom_at(self.width() / 2.0, self.height() / 2.0, factor)

    def zoom_out(self, factor: float = 0.77):
        self._apply_zoom_at(self.width() / 2.0, self.height() / 2.0, factor)

    def reset_zoom(self):
        self.zoom = 1.0
        self.zoomChanged.emit(self.zoom)
        self.update()

    def fit_whole_map(self):
        """Zooms and centers so the entire map facet fits into the viewport."""
        m_info = self.current_map_info
        if self.width() <= 0 or self.height() <= 0:
            return
        zx = self.width() / float(m_info.width)
        zy = self.height() / float(m_info.height)
        self.zoom = min(zx, zy) * 0.95
        self.center_x = m_info.width / 2.0
        self.center_y = m_info.height / 2.0
        self.zoomChanged.emit(self.zoom)
        self.centerChanged.emit(int(self.center_x), int(self.center_y))
        self.update()

    def world_to_screen(self, wx: float, wy: float) -> Tuple[float, float]:
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        sx = cx + (wx - self.center_x) * self.zoom
        sy = cy + (wy - self.center_y) * self.zoom
        return sx, sy

    def screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        wx = self.center_x + (sx - cx) / self.zoom
        wy = self.center_y + (sy - cy) / self.zoom
        return wx, wy

    def _apply_zoom_at(self, sx: float, sy: float, factor: float):
        old_zoom = self.zoom
        new_zoom = max(0.08, min(16.0, old_zoom * factor))
        if abs(new_zoom - old_zoom) < 1e-4:
            return

        wx, wy = self.screen_to_world(sx, sy)
        cx = self.width() / 2.0
        cy = self.height() / 2.0

        self.center_x = wx - (sx - cx) / new_zoom
        self.center_y = wy - (sy - cy) / new_zoom
        self.zoom = new_zoom

        # Clamp center inside map bounds
        m_info = self.current_map_info
        self.center_x = max(0.0, min(float(m_info.width), self.center_x))
        self.center_y = max(0.0, min(float(m_info.height), self.center_y))

        self.zoomChanged.emit(self.zoom)
        self.centerChanged.emit(int(self.center_x), int(self.center_y))
        self.update()

    def _get_overview_pixmap(self) -> Optional[QPixmap]:
        if self.map_id in self._overview_pixmaps:
            return self._overview_pixmaps[self.map_id]

        pil_img = self.map_mgr.render_overview(self.map_id)
        if pil_img:
            data = pil_img.tobytes("raw", "RGBA")
            qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
            pix = QPixmap.fromImage(qimg)
            self._overview_pixmaps[self.map_id] = pix
            return pix
        return None

    def _render_chunk(self, cx: int, cy: int) -> QPixmap:
        cache_key = (self.map_id, self.show_statics, cx, cy)
        if cache_key in self._chunk_cache:
            self._chunk_cache.move_to_end(cache_key)
            return self._chunk_cache[cache_key]

        start_bx = cx * BLOCKS_PER_CHUNK
        start_by = cy * BLOCKS_PER_CHUNK

        pil_img = self.map_mgr.render_minimap(
            map_id=self.map_id,
            start_bx=start_bx,
            start_by=start_by,
            num_blocks_x=BLOCKS_PER_CHUNK,
            num_blocks_y=BLOCKS_PER_CHUNK,
            show_statics=self.show_statics
        )

        data = pil_img.tobytes("raw", "RGBA")
        qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
        pix = QPixmap.fromImage(qimg)

        # Bound LRU cache size to 1500 chunks (~150MB RAM)
        if len(self._chunk_cache) >= 1500:
            self._chunk_cache.popitem(last=False)

        self._chunk_cache[cache_key] = pix
        return pix

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, self.zoom < 1.0)

        # 1. Dark empty background
        painter.fillRect(self.rect(), QColor("#0c0c10"))

        m_info = self.current_map_info
        world_w = m_info.width
        world_h = m_info.height

        # Screen coordinates of world (0, 0) and (world_w, world_h)
        sx0, sy0 = self.world_to_screen(0, 0)
        sx1, sy1 = self.world_to_screen(world_w, world_h)
        world_rect = QRectF(sx0, sy0, sx1 - sx0, sy1 - sy0)

        # 2. Base overview layer (always rendered underneath when map area is in viewport)
        overview_pix = self._get_overview_pixmap()
        if overview_pix and not overview_pix.isNull():
            painter.drawPixmap(world_rect, overview_pix, QRectF(overview_pix.rect()))

        # 3. Detailed chunks layer (only when zoomed close enough to discern tile details: LOD >= 0.55)
        # When zoomed out (< 0.55), the overview pixmap provides a smooth, instantaneous 60 FPS view.
        if self.zoom >= 0.55:
            min_wx, min_wy = self.screen_to_world(0, 0)
            max_wx, max_wy = self.screen_to_world(self.width(), self.height())

            max_cx = (world_w + CHUNK_TILES - 1) // CHUNK_TILES
            max_cy = (world_h + CHUNK_TILES - 1) // CHUNK_TILES

            c_start_x = max(0, int(min_wx) // CHUNK_TILES)
            c_end_x = min(max_cx - 1, int(max_wx) // CHUNK_TILES)
            c_start_y = max(0, int(min_wy) // CHUNK_TILES)
            c_end_y = min(max_cy - 1, int(max_wy) // CHUNK_TILES)

            chunk_screen_w = CHUNK_TILES * self.zoom
            chunk_screen_h = CHUNK_TILES * self.zoom

            for cx in range(c_start_x, c_end_x + 1):
                chunk_wx = cx * CHUNK_TILES
                csx, _ = self.world_to_screen(chunk_wx, 0)

                for cy in range(c_start_y, c_end_y + 1):
                    chunk_wy = cy * CHUNK_TILES
                    _, csy = self.world_to_screen(0, chunk_wy)

                    target_rect = QRectF(csx, csy, chunk_screen_w, chunk_screen_h)
                    pix = self._render_chunk(cx, cy)
                    painter.drawPixmap(target_rect, pix, QRectF(pix.rect()))

        # 4. World border outline
        painter.setPen(QPen(QColor("#3f51b5"), 1.5, Qt.PenStyle.SolidLine))
        painter.drawRect(world_rect)

        # 5. Subtle Center Crosshair
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        painter.setPen(QPen(QColor(255, 255, 255, 70), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(cx - 12), int(cy), int(cx + 12), int(cy))
        painter.drawLine(int(cx), int(cy - 12), int(cx), int(cy + 12))

        # 6. Scale Indicator Bar in bottom-right (Google Maps style)
        self._draw_scale_bar(painter)

    def _draw_scale_bar(self, painter: QPainter):
        bar_screen_w = 80.0
        world_dist = int(bar_screen_w / self.zoom)

        bx = self.width() - 110
        by = self.height() - 25

        painter.setPen(QPen(QColor("#ffffff"), 1.5))
        painter.drawLine(bx, by, bx + int(bar_screen_w), by)
        painter.drawLine(bx, by - 4, bx, by + 4)
        painter.drawLine(bx + int(bar_screen_w), by - 4, bx + int(bar_screen_w), by + 4)

        painter.setFont(QFont("sans-serif", 9))
        painter.drawText(bx, by - 16, int(bar_screen_w), 14, Qt.AlignmentFlag.AlignCenter, f"{world_dist} tiles")

    def wheelEvent(self, event: QWheelEvent):
        degrees = event.angleDelta().y() / 8.0
        steps = degrees / 15.0
        factor = 1.25 ** steps
        pos = event.position()
        self._apply_zoom_at(pos.x(), pos.y(), factor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._last_mouse = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        wx, wy = self.screen_to_world(pos.x(), pos.y())
        m_info = self.current_map_info
        if 0 <= wx < m_info.width and 0 <= wy < m_info.height:
            self.coordinatesChanged.emit(int(wx), int(wy))

        if self._is_dragging:
            delta = pos.toPoint() - self._last_mouse
            self._last_mouse = pos.toPoint()

            self.center_x -= delta.x() / self.zoom
            self.center_y -= delta.y() / self.zoom

            # Clamp center
            self.center_x = max(0.0, min(float(m_info.width), self.center_x))
            self.center_y = max(0.0, min(float(m_info.height), self.center_y))

            self.centerChanged.emit(int(self.center_x), int(self.center_y))
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double click centers and zooms in at the clicked world coordinate."""
        pos = event.position()
        wx, wy = self.screen_to_world(pos.x(), pos.y())
        self.go_to(wx, wy)
        self._apply_zoom_at(pos.x(), pos.y(), 1.6)
