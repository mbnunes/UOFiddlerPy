"""
Light Tab: Light source mask viewer and intensity inspector.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel,
    QGroupBox, QFormLayout, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from uofiddler.core.light import LightManager
from uofiddler.gui.widgets.image_canvas import ImageCanvas


class LightTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.light_mgr = LightManager.get_instance()
        self.current_light_id = 0
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Light Patterns:"))
        self.list_widget = QListWidget()
        self.populate_list()
        self.list_widget.currentRowChanged.connect(self.on_light_selected)
        left_layout.addWidget(self.list_widget)

        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.canvas = ImageCanvas(self)
        self.canvas.setMinimumSize(250, 250)
        right_layout.addWidget(self.canvas, stretch=2)

        prop_box = QGroupBox("Light Information")
        form_layout = QFormLayout(prop_box)
        self.lbl_id = QLabel("0")
        self.lbl_size = QLabel("-")
        form_layout.addRow("Light ID:", self.lbl_id)
        form_layout.addRow("Dimensions:", self.lbl_size)
        right_layout.addWidget(prop_box)
        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def populate_list(self):
        self.list_widget.clear()
        for i in range(self.light_mgr.max_lights):
            if self.light_mgr.is_valid(i):
                item = QListWidgetItem(f"Light {i} (0x{i:02X})")
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.list_widget.addItem(item)

    def on_light_selected(self, row: int):
        if row < 0:
            return
        item = self.list_widget.item(row)
        if not item:
            return
        light_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_light_id = light_id

        img = self.light_mgr.get_light(light_id)
        self.canvas.set_pil_image(img)
        self.lbl_id.setText(str(light_id))
        self.lbl_size.setText(f"{img.width} x {img.height} px" if img else "(empty)")
