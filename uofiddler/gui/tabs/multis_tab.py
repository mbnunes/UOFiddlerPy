"""
Multis Tab: Multi buildings and structures viewer, isometric renderer, and component inspector.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView, QSlider
)
from PyQt6.QtCore import Qt
from uofiddler.core.multis import MultisManager, MultiStructure
from uofiddler.core.tiledata import TileDataManager
from uofiddler.gui.widgets.image_canvas import ImageCanvas


class MultisTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.multi_mgr = MultisManager.get_instance()
        self.tile_mgr = TileDataManager.get_instance()
        self.current_multi_id = 0
        self.max_z_cutoff = 300
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: List & Search
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Multi ID...")
        self.search_input.returnPressed.connect(self.on_search)
        search_btn = QPushButton("Go")
        search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        left_layout.addLayout(search_layout)

        self.list_widget = QListWidget()
        self.populate_list()
        self.list_widget.currentRowChanged.connect(self.on_multi_selected)
        left_layout.addWidget(self.list_widget)

        splitter.addWidget(left_widget)

        # Center/Right panel: Isometric Canvas & Cutoff slider
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)

        self.canvas = ImageCanvas(self)
        self.canvas.setMinimumSize(350, 350)
        center_layout.addWidget(self.canvas, stretch=2)

        # Floor / Height cutoff slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Height Cutoff (Floor):"))
        self.z_slider = QSlider(Qt.Orientation.Horizontal)
        self.z_slider.setRange(-20, 100)
        self.z_slider.setValue(100)
        self.z_slider.valueChanged.connect(self.on_z_slider_changed)
        slider_layout.addWidget(self.z_slider)
        self.lbl_z = QLabel("All")
        slider_layout.addWidget(self.lbl_z)
        center_layout.addLayout(slider_layout)

        # Actions
        btn_layout = QHBoxLayout()
        export_img_btn = QPushButton("Export PNG")
        export_img_btn.clicked.connect(self.on_export_png)
        export_txt_btn = QPushButton("Export Multi Script (TXT)")
        export_txt_btn.clicked.connect(self.on_export_txt)
        btn_layout.addWidget(export_img_btn)
        btn_layout.addWidget(export_txt_btn)
        center_layout.addLayout(btn_layout)

        splitter.addWidget(center_widget)

        # Far Right panel: Component list table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("Multi Components Table:"))
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Item", "X", "Y", "Z", "Flags"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        right_layout.addWidget(self.table)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 3)

        main_layout.addWidget(splitter)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def populate_list(self):
        self.list_widget.clear()
        for i in range(self.multi_mgr.max_multis):
            if self.multi_mgr.is_valid(i):
                item = QListWidgetItem(f"Multi 0x{i:04X} ({i})")
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.list_widget.addItem(item)

    def on_multi_selected(self, row: int):
        if row < 0:
            return
        item = self.list_widget.item(row)
        if not item:
            return
        multi_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_multi(multi_id)

    def load_multi(self, multi_id: int):
        self.current_multi_id = multi_id
        m = self.multi_mgr.get_multi(multi_id)
        if not m:
            self.canvas.set_pil_image(None)
            self.table.setRowCount(0)
            return

        # Render isometric
        img = m.render_isometric(max_z=self.max_z_cutoff)
        self.canvas.set_pil_image(img)

        # Populate table
        self.table.setRowCount(len(m.components))
        for r, c in enumerate(m.components):
            tile = self.tile_mgr.get_item(c.item_id)
            name_str = tile.name if tile and tile.name else f"0x{c.item_id:04X}"
            self.table.setItem(r, 0, QTableWidgetItem(name_str))
            self.table.setItem(r, 1, QTableWidgetItem(str(c.offset_x)))
            self.table.setItem(r, 2, QTableWidgetItem(str(c.offset_y)))
            self.table.setItem(r, 3, QTableWidgetItem(str(c.offset_z)))
            self.table.setItem(r, 4, QTableWidgetItem(f"0x{c.flags:X}"))

    def on_z_slider_changed(self, val: int):
        if val >= 100:
            self.max_z_cutoff = 300
            self.lbl_z.setText("All")
        else:
            self.max_z_cutoff = val
            self.lbl_z.setText(f"Z <= {val}")

        m = self.multi_mgr.get_multi(self.current_multi_id)
        if m:
            img = m.render_isometric(self.max_z_cutoff)
            self.canvas.set_pil_image(img)

    def on_search(self):
        text = self.search_input.text().strip()
        if not text:
            return
        try:
            target = int(text, 16) if text.lower().startswith("0x") else int(text)
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == target:
                    self.list_widget.setCurrentRow(i)
                    self.list_widget.scrollToItem(item)
                    return
            QMessageBox.information(self, "Search", f"Multi {text} not found.")
        except ValueError:
            QMessageBox.warning(self, "Search", "Enter a valid numeric or hex ID.")

    def on_export_png(self):
        m = self.multi_mgr.get_multi(self.current_multi_id)
        if not m:
            return
        img = m.render_isometric(self.max_z_cutoff)
        if not img:
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Export Multi Image", f"multi_0x{self.current_multi_id:04X}.png", "PNG Files (*.png)")
        if fn:
            img.save(fn)
            QMessageBox.information(self, "Export", f"Saved to {fn}")

    def on_export_txt(self):
        m = self.multi_mgr.get_multi(self.current_multi_id)
        if not m:
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Export Multi Script", f"multi_0x{self.current_multi_id:04X}.txt", "Text Files (*.txt)")
        if fn:
            with open(fn, "w") as f:
                f.write(f"// Multi 0x{self.current_multi_id:04X} ({len(m.components)} components)\n")
                for c in m.components:
                    f.write(f"0x{c.item_id:04X} {c.offset_x} {c.offset_y} {c.offset_z} {c.flags}\n")
            QMessageBox.information(self, "Export", f"Saved to {fn}")
