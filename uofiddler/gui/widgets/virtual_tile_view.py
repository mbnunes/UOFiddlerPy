"""
Virtualized tile browser widget with dual Grid (IconMode) and List (TableView) views.
Enables 60fps instant browsing, search, and selection across 65,536+ items, land tiles,
textures, hues, and radar colors.
"""

from typing import Callable, Optional, Dict, List
from PIL import Image
from PyQt6.QtCore import Qt, QAbstractListModel, QAbstractTableModel, QModelIndex, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QColor, QPainter, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QListView, QTableView, QButtonGroup, QHeaderView,
    QAbstractItemView, QMessageBox
)


class VirtualTileGridModel(QAbstractListModel):
    """Virtual model for Grid view (QListView in IconMode)."""

    def __init__(
        self,
        count: int,
        get_label: Callable[[int], str],
        get_image: Optional[Callable[[int], Optional[Image.Image]]] = None,
        get_swatch: Optional[Callable[[int], Optional[QPixmap]]] = None,
        get_text: Optional[Callable[[int], str]] = None,
        get_tooltip: Optional[Callable[[int], str]] = None,
        ids: Optional[List[int]] = None,
        pixmap_cache: Optional[Dict[int, QPixmap]] = None,
        icon_size: QSize = QSize(44, 44),
        parent=None,
    ):
        super().__init__(parent)
        self.ids = ids
        self.total_count = len(ids) if ids is not None else count
        self.get_label = get_label
        self.get_image = get_image
        self.get_swatch = get_swatch
        self.get_text = get_text
        self.get_tooltip = get_tooltip
        self.icon_size = icon_size
        self._cache = pixmap_cache if pixmap_cache is not None else {}
        self._empty_pix = QPixmap(self.icon_size)
        self._empty_pix.fill(Qt.GlobalColor.transparent)

    def rowCount(self, parent=QModelIndex()) -> int:
        return self.total_count

    def get_real_id(self, row: int) -> int:
        return self.ids[row] if self.ids is not None else row

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        real_id = self.get_real_id(row)

        if role == Qt.ItemDataRole.DisplayRole:
            if self.get_text:
                return self.get_text(real_id)
            return f"0x{real_id:04X}"

        elif role == Qt.ItemDataRole.DecorationRole:
            if real_id in self._cache:
                return self._cache[real_id]

            pix = self._render_thumbnail(real_id)
            if len(self._cache) > 2500:
                self._cache.clear()
            self._cache[real_id] = pix
            return pix

        elif role == Qt.ItemDataRole.ToolTipRole:
            if self.get_tooltip:
                return self.get_tooltip(real_id)
            label = self.get_label(real_id)
            if label:
                return f"0x{real_id:04X} ({real_id})\n{label}"
            return f"0x{real_id:04X} ({real_id})"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        return None

    def _render_thumbnail(self, real_id: int) -> QPixmap:
        # Check if direct swatch provider exists (e.g. Hues)
        swatch_pix = self.get_swatch(real_id) if self.get_swatch else None
        img = self.get_image(real_id) if self.get_image else None

        if img is None and swatch_pix is not None:
            return swatch_pix

        if img is not None:
            rgba = img.convert("RGBA")
            target_w = self.icon_size.width()
            target_h = self.icon_size.height()
            rgba.thumbnail((target_w, target_h), Image.Resampling.NEAREST)
            data = rgba.tobytes("raw", "RGBA")
            qimg = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888)
            art_pix = QPixmap.fromImage(qimg)

            # If both img and swatch exist (e.g. RadarCol), composite them
            if swatch_pix is not None:
                composite = QPixmap(self.icon_size)
                composite.fill(Qt.GlobalColor.transparent)
                painter = QPainter(composite)
                # Draw centered art
                ax = (target_w - art_pix.width()) // 2
                ay = (target_h - art_pix.height()) // 2
                painter.drawPixmap(ax, ay, art_pix)
                # Draw small swatch in bottom-right corner
                sw_w = min(16, swatch_pix.width())
                sw_h = min(16, swatch_pix.height())
                painter.drawPixmap(target_w - sw_w - 1, target_h - sw_h - 1, swatch_pix.scaled(sw_w, sw_h))
                painter.end()
                return composite

            return art_pix

        return self._empty_pix


class VirtualTileModel(QAbstractTableModel):
    """Virtual model for List/Table view (QTableView)."""

    def __init__(
        self,
        count: int,
        get_label: Callable[[int], str],
        get_image: Optional[Callable[[int], Optional[Image.Image]]] = None,
        get_swatch: Optional[Callable[[int], Optional[QPixmap]]] = None,
        columns: Optional[List[str]] = None,
        ids: Optional[List[int]] = None,
        pixmap_cache: Optional[Dict[int, QPixmap]] = None,
        icon_size: QSize = QSize(44, 44),
        parent=None,
    ):
        super().__init__(parent)
        self.ids = ids
        self.total_count = len(ids) if ids is not None else count
        self.get_label = get_label
        self.get_image = get_image
        self.get_swatch = get_swatch
        self.icon_size = icon_size
        self._cache = pixmap_cache if pixmap_cache is not None else {}
        self.columns = columns or ["ID", "Hex", "Name", "Graphic"]
        self._empty_pix = QPixmap(self.icon_size)
        self._empty_pix.fill(Qt.GlobalColor.transparent)

    def rowCount(self, parent=QModelIndex()) -> int:
        return self.total_count

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.columns)

    def get_real_id(self, row: int) -> int:
        return self.ids[row] if self.ids is not None else row

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.columns[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        real_id = self.get_real_id(row)
        col_name = self.columns[col]

        if role == Qt.ItemDataRole.DisplayRole:
            if col_name == "ID":
                return str(real_id)
            elif col_name == "Hex":
                return f"0x{real_id:04X}"
            elif col_name == "Name" or col_name == "Dimensions":
                return self.get_label(real_id)
            elif col_name == "Radar Color":
                return self.get_label(real_id)
            return None

        elif role == Qt.ItemDataRole.DecorationRole:
            if col_name in ("Graphic", "Color", "Radar Color"):
                if real_id in self._cache:
                    return self._cache[real_id]

                swatch_pix = self.get_swatch(real_id) if self.get_swatch else None
                img = self.get_image(real_id) if self.get_image else None

                if img is None and swatch_pix is not None:
                    pix = swatch_pix
                elif img is not None:
                    rgba = img.convert("RGBA")
                    target_w = self.icon_size.width()
                    target_h = self.icon_size.height()
                    rgba.thumbnail((target_w, target_h), Image.Resampling.NEAREST)
                    data = rgba.tobytes("raw", "RGBA")
                    qimg = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888)
                    art_pix = QPixmap.fromImage(qimg)

                    if swatch_pix is not None:
                        composite = QPixmap(self.icon_size)
                        composite.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(composite)
                        ax = (target_w - art_pix.width()) // 2
                        ay = (target_h - art_pix.height()) // 2
                        painter.drawPixmap(ax, ay, art_pix)
                        sw_w = min(16, swatch_pix.width())
                        sw_h = min(16, swatch_pix.height())
                        painter.drawPixmap(target_w - sw_w - 1, target_h - sw_h - 1, swatch_pix.scaled(sw_w, sw_h))
                        painter.end()
                        pix = composite
                    else:
                        pix = art_pix
                else:
                    pix = self._empty_pix

                if len(self._cache) > 2500:
                    self._cache.clear()
                self._cache[real_id] = pix
                return pix
            return None

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col_name in ("ID", "Hex"):
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        return None


class VirtualGridView(QListView):
    """High-performance virtual IconMode grid view."""

    def __init__(self, parent=None, grid_size=QSize(68, 68), icon_size=QSize(44, 44)):
        super().__init__(parent)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setUniformItemSizes(True)
        self.setMovement(QListView.Movement.Static)
        self.setWordWrap(False)
        self.setSpacing(3)
        self.setGridSize(grid_size)
        self.setIconSize(icon_size)
        self.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)


class VirtualTileView(QTableView):
    """High-performance virtual table view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.verticalHeader().setDefaultSectionSize(48)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        self.setAlternatingRowColors(True)
        self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)


class TileBrowserWidget(QWidget):
    """
    Combined Grid & List tile browser widget with integrated search and view toggle.
    Default mode: GRID.
    """

    itemSelected = pyqtSignal(int)

    def __init__(
        self,
        parent=None,
        grid_size: QSize = QSize(68, 68),
        icon_size: QSize = QSize(44, 44),
    ):
        super().__init__(parent)
        self.grid_size = grid_size
        self.icon_size = icon_size
        self._shared_cache: Dict[int, QPixmap] = {}
        self._current_real_id = 0
        self._is_syncing = False
        self._ids: Optional[List[int]] = None
        self._id_to_row: Dict[int, int] = {}
        self.grid_model: Optional[VirtualTileGridModel] = None
        self.table_model: Optional[VirtualTileModel] = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Top Bar: Search + Mode Toggle
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)

        search_lbl = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ID (dec/hex) or name...")
        self.search_input.returnPressed.connect(self.on_search)

        btn_go = QPushButton("Go")
        btn_go.setFixedWidth(40)
        btn_go.clicked.connect(self.on_search)

        # Toggle Button Group for Grid vs List
        self.view_btn_group = QButtonGroup(self)
        self.view_btn_group.setExclusive(True)

        self.btn_grid = QPushButton("⊞ Grid")
        self.btn_grid.setCheckable(True)
        self.btn_grid.setChecked(True)  # DEFAULT IS GRID
        self.btn_grid.setToolTip("Switch to Grid View")

        self.btn_list = QPushButton("☰ List")
        self.btn_list.setCheckable(True)
        self.btn_list.setToolTip("Switch to Detailed List View")

        self.view_btn_group.addButton(self.btn_grid)
        self.view_btn_group.addButton(self.btn_list)

        self.btn_grid.toggled.connect(self.on_view_mode_changed)

        top_bar.addWidget(search_lbl)
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(btn_go)
        top_bar.addWidget(self.btn_grid)
        top_bar.addWidget(self.btn_list)
        layout.addLayout(top_bar)

        # Stacked Views
        self.stack = QStackedWidget(self)

        # Grid View (Page 0 - DEFAULT)
        self.grid_view = VirtualGridView(self, grid_size=self.grid_size, icon_size=self.icon_size)
        self.grid_view.selectionModel()

        # Table View (Page 1)
        self.table_view = VirtualTileView(self)

        self.stack.addWidget(self.grid_view)
        self.stack.addWidget(self.table_view)
        self.stack.setCurrentIndex(0)  # DEFAULT IS GRID
        layout.addWidget(self.stack)

        # Bottom status label
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #888; font-size: 11px; padding: 2px;")
        layout.addWidget(self.lbl_status)

    @property
    def count(self) -> int:
        if self._ids is not None:
            return len(self._ids)
        return self.grid_model.total_count if hasattr(self, "grid_model") and self.grid_model else 0

    @property
    def ids(self) -> Optional[List[int]]:
        return self._ids

    def set_data(
        self,
        count: int,
        get_label: Callable[[int], str],
        get_image: Optional[Callable[[int], Optional[Image.Image]]] = None,
        get_swatch: Optional[Callable[[int], Optional[QPixmap]]] = None,
        get_text: Optional[Callable[[int], str]] = None,
        get_tooltip: Optional[Callable[[int], str]] = None,
        columns: Optional[List[str]] = None,
        ids: Optional[List[int]] = None,
    ):
        """Configures data models for both Grid and List views."""
        self._shared_cache.clear()
        self._ids = ids
        if ids is not None:
            self._id_to_row = {real_id: row for row, real_id in enumerate(ids)}
            total = len(ids)
        else:
            self._id_to_row = {}
            total = count

        self.grid_model = VirtualTileGridModel(
            count=count,
            get_label=get_label,
            get_image=get_image,
            get_swatch=get_swatch,
            get_text=get_text,
            get_tooltip=get_tooltip,
            ids=ids,
            pixmap_cache=self._shared_cache,
            icon_size=self.icon_size,
            parent=self,
        )

        cols = columns or ["ID", "Hex", "Name", "Graphic"]
        self.table_model = VirtualTileModel(
            count=count,
            get_label=get_label,
            get_image=get_image,
            get_swatch=get_swatch,
            columns=cols,
            ids=ids,
            pixmap_cache=self._shared_cache,
            icon_size=self.icon_size,
            parent=self,
        )

        self.grid_view.setModel(self.grid_model)
        self.table_view.setModel(self.table_model)

        # Setup Table Header resize modes
        header = self.table_view.horizontalHeader()
        if len(cols) >= 4:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            for c in range(3, len(cols)):
                header.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        else:
            for c in range(len(cols)):
                header.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)

        # Connect selection signals
        self.grid_view.selectionModel().currentRowChanged.connect(self._on_grid_selection_changed)
        self.table_view.selectionModel().currentRowChanged.connect(self._on_table_selection_changed)

        self.lbl_status.setText(f"Total: {total:,} entries")

        if total > 0:
            initial_id = self._ids[0] if self._ids else 0
            self.select_id(initial_id, emit_signal=False)

    def refresh(self):
        """Clears cache and forces redraw of both views."""
        self._shared_cache.clear()
        if self.grid_model:
            self.grid_model.layoutChanged.emit()
        if self.table_model:
            self.table_model.layoutChanged.emit()

    def _on_grid_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        if not current.isValid() or self._is_syncing:
            return

        row = current.row()
        real_id = self.grid_model.get_real_id(row) if self.grid_model else row
        self._current_real_id = real_id

        # Sync to table without re-triggering
        self._is_syncing = True
        if self.table_model:
            t_idx = self.table_model.index(row, 0)
            self.table_view.setCurrentIndex(t_idx)
        self._is_syncing = False

        self.itemSelected.emit(real_id)

    def _on_table_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        if not current.isValid() or self._is_syncing:
            return

        row = current.row()
        real_id = self.table_model.get_real_id(row) if self.table_model else row
        self._current_real_id = real_id

        # Sync to grid without re-triggering
        self._is_syncing = True
        if self.grid_model:
            g_idx = self.grid_model.index(row, 0)
            self.grid_view.setCurrentIndex(g_idx)
        self._is_syncing = False

        self.itemSelected.emit(real_id)

    def select_id(self, real_id: int, emit_signal: bool = True):
        """Selects the item by its real ID and scrolls into view in the active view."""
        if not self.grid_model or not self.table_model:
            return

        if self._ids is not None:
            if real_id not in self._id_to_row:
                return
            row = self._id_to_row[real_id]
        else:
            if real_id < 0 or real_id >= self.grid_model.total_count:
                return
            row = real_id

        self._current_real_id = real_id
        self._is_syncing = True

        g_idx = self.grid_model.index(row, 0)
        t_idx = self.table_model.index(row, 0)

        self.grid_view.setCurrentIndex(g_idx)
        self.table_view.setCurrentIndex(t_idx)

        # Scroll active view to item
        if self.stack.currentIndex() == 0:
            self.grid_view.scrollTo(g_idx, QAbstractItemView.ScrollHint.PositionAtCenter)
        else:
            self.table_view.scrollTo(t_idx, QAbstractItemView.ScrollHint.PositionAtCenter)

        self._is_syncing = False
        if emit_signal:
            self.itemSelected.emit(real_id)

    def get_selected_id(self) -> int:
        return self._current_real_id

    def on_view_mode_changed(self, grid_checked: bool):
        if grid_checked:
            self.stack.setCurrentIndex(0)
            # Scroll grid to selected item
            if self.grid_model:
                row = self._id_to_row.get(self._current_real_id, self._current_real_id) if self._ids else self._current_real_id
                if 0 <= row < self.grid_model.total_count:
                    idx = self.grid_model.index(row, 0)
                    self.grid_view.scrollTo(idx, QAbstractItemView.ScrollHint.PositionAtCenter)
        else:
            self.stack.setCurrentIndex(1)
            # Scroll table to selected item
            if self.table_model:
                row = self._id_to_row.get(self._current_real_id, self._current_real_id) if self._ids else self._current_real_id
                if 0 <= row < self.table_model.total_count:
                    idx = self.table_model.index(row, 0)
                    self.table_view.scrollTo(idx, QAbstractItemView.ScrollHint.PositionAtCenter)

    def on_search(self):
        text = self.search_input.text().strip()
        if not text:
            return

        # 1. Try Hex (0x...) or decimal
        target_id = None
        try:
            if text.lower().startswith("0x"):
                target_id = int(text, 16)
            elif all(c in "0123456789abcdefABCDEF" for c in text) and any(c in "abcdefABCDEF" for c in text):
                target_id = int(text, 16)
            else:
                target_id = int(text)
        except ValueError:
            target_id = None

        if target_id is not None:
            if self._ids is not None:
                if target_id in self._id_to_row:
                    self.select_id(target_id)
                    return
            else:
                if 0 <= target_id < self.grid_model.total_count:
                    self.select_id(target_id)
                    return

        # 2. Search by label substring
        if self.grid_model:
            q = text.lower()
            total = self.grid_model.total_count
            for r in range(total):
                real_id = self.grid_model.get_real_id(r)
                lbl = self.grid_model.get_label(real_id)
                if lbl and q in lbl.lower():
                    self.select_id(real_id)
                    return

        QMessageBox.information(self, "Search", f"No item found matching '{text}'")
