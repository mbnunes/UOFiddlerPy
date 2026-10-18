"""
AnimData Tab: Animation tile frame count, interval, delay, and frame offset editor.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox
)
from PyQt6.QtCore import Qt
from uofiddler.core.animdata import AnimDataManager, AnimDataEntry
from uofiddler.core.art import ArtManager
from uofiddler.gui.widgets.image_canvas import ImageCanvas


class AnimDataTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animdata_mgr = AnimDataManager.get_instance()
        self.art_mgr = ArtManager.get_instance()
        self.current_entry: Optional[AnimDataEntry] = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Table of animated tiles
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Animated Items (animdata.mul):"))
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Item ID", "Frames", "Interval", "Start"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        self.populate_table()
        self.table.currentCellChanged.connect(lambda r, c, pr, pc: self.on_row_selected(r))
        left_layout.addWidget(self.table)

        splitter.addWidget(left_widget)

        # Right panel: Canvas & Editor
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.canvas = ImageCanvas(self)
        self.canvas.setMinimumSize(200, 200)
        right_layout.addWidget(self.canvas, stretch=2)

        prop_box = QGroupBox("Animation Data Properties")
        form = QFormLayout(prop_box)

        self.lbl_id = QLabel("-")
        self.spin_count = QSpinBox()
        self.spin_count.setRange(0, 64)
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(0, 255)
        self.spin_start = QSpinBox()
        self.spin_start.setRange(0, 255)
        self.lbl_offsets = QLabel("-")
        self.lbl_offsets.setWordWrap(True)

        form.addRow("Item ID:", self.lbl_id)
        form.addRow("Frame Count:", self.spin_count)
        form.addRow("Frame Interval:", self.spin_interval)
        form.addRow("Start Delay:", self.spin_start)
        form.addRow("Frame Offsets:", self.lbl_offsets)

        apply_btn = QPushButton("Apply Edit")
        apply_btn.clicked.connect(self.on_apply)
        form.addRow("", apply_btn)
        right_layout.addWidget(prop_box)

        save_btn = QPushButton("Save animdata.mul")
        save_btn.clicked.connect(self.on_save)
        right_layout.addWidget(save_btn)
        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def populate_table(self):
        sorted_keys = sorted(self.animdata_mgr.entries.keys())
        self.table.setRowCount(len(sorted_keys))
        for r, k in enumerate(sorted_keys):
            e = self.animdata_mgr.entries[k]
            self.table.setItem(r, 0, QTableWidgetItem(f"0x{e.item_id:04X} ({e.item_id})"))
            self.table.setItem(r, 1, QTableWidgetItem(str(e.frame_count)))
            self.table.setItem(r, 2, QTableWidgetItem(str(e.frame_interval)))
            self.table.setItem(r, 3, QTableWidgetItem(str(e.frame_start)))
            self.table.item(r, 0).setData(Qt.ItemDataRole.UserRole, e.item_id)

    def on_row_selected(self, row: int):
        if row < 0:
            return
        item = self.table.item(row, 0)
        if not item:
            return
        item_id = item.data(Qt.ItemDataRole.UserRole)
        e = self.animdata_mgr.get_anim_data(item_id)
        self.current_entry = e

        img = self.art_mgr.get_static(item_id)
        self.canvas.set_pil_image(img)

        if e:
            self.lbl_id.setText(f"0x{e.item_id:04X} ({e.item_id})")
            self.spin_count.setValue(e.frame_count)
            self.spin_interval.setValue(e.frame_interval)
            self.spin_start.setValue(e.frame_start)
            non_zero_offsets = e.frames[:e.frame_count]
            self.lbl_offsets.setText(str(non_zero_offsets))

    def on_apply(self):
        if not self.current_entry:
            return
        self.current_entry.frame_count = self.spin_count.value()
        self.current_entry.frame_interval = self.spin_interval.value()
        self.current_entry.frame_start = self.spin_start.value()
        row = self.table.currentRow()
        if row >= 0:
            self.table.setItem(row, 1, QTableWidgetItem(str(self.current_entry.frame_count)))
            self.table.setItem(row, 2, QTableWidgetItem(str(self.current_entry.frame_interval)))
            self.table.setItem(row, 3, QTableWidgetItem(str(self.current_entry.frame_start)))
        QMessageBox.information(self, "Applied", "Animation timing applied.")

    def on_save(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save animdata.mul", "animdata.mul", "MUL Files (*.mul)")
        if fn:
            try:
                self.animdata_mgr.save(fn)
                QMessageBox.information(self, "Saved", f"Saved animdata.mul to {fn}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save animdata.mul: {e}")
