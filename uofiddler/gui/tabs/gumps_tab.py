"""
Gumps Tab: Ultima Online Gump viewer, inspector, and editor with PNG export/import.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from uofiddler.core.gumps import GumpManager
from uofiddler.gui.widgets.image_canvas import ImageCanvas


class GumpsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gump_mgr = GumpManager.get_instance()
        self.current_gump_id = 0
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Search & List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search ID:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Gump ID (dec/hex)...")
        self.search_input.returnPressed.connect(self.on_search)
        search_btn = QPushButton("Go")
        search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        left_layout.addLayout(search_layout)

        # List of Gump IDs
        self.list_widget = QListWidget()
        self.populate_list()
        self.list_widget.currentRowChanged.connect(self.on_gump_selected)
        left_layout.addWidget(self.list_widget)

        splitter.addWidget(left_widget)

        # Right panel: Image Canvas, Details, and Tools
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.canvas = ImageCanvas(self)
        self.canvas.setMinimumSize(300, 300)
        right_layout.addWidget(self.canvas, stretch=2)

        # Info
        prop_box = QGroupBox("Gump Information")
        form_layout = QFormLayout(prop_box)
        self.lbl_id = QLabel("0 (0x0000)")
        self.lbl_size = QLabel("-")

        form_layout.addRow("Gump ID:", self.lbl_id)
        form_layout.addRow("Dimensions:", self.lbl_size)
        right_layout.addWidget(prop_box)

        # Actions
        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Export PNG")
        export_btn.clicked.connect(self.on_export)
        replace_btn = QPushButton("Replace Image")
        replace_btn.clicked.connect(self.on_replace)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.on_remove)

        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(replace_btn)
        btn_layout.addWidget(remove_btn)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def populate_list(self):
        self.list_widget.clear()
        if not self.gump_mgr._file_index:
            return

        for i, entry in enumerate(self.gump_mgr._file_index.entries):
            if entry.is_valid:
                item = QListWidgetItem(f"Gump 0x{i:04X} ({i})")
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.list_widget.addItem(item)

    def on_gump_selected(self, row: int):
        if row < 0:
            return
        item = self.list_widget.item(row)
        if not item:
            return
        gump_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_gump(gump_id)

    def load_gump(self, gump_id: int):
        self.current_gump_id = gump_id
        img = self.gump_mgr.get_gump(gump_id)
        self.canvas.set_pil_image(img)

        self.lbl_id.setText(f"{gump_id} (0x{gump_id:04X})")
        if img:
            self.lbl_size.setText(f"{img.width} x {img.height} px")
        else:
            self.lbl_size.setText("(empty / not found)")

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
            QMessageBox.information(self, "Search", f"Gump ID {text} not defined in files.")
        except ValueError:
            QMessageBox.warning(self, "Search", "Please enter a valid numeric or hex ID.")

    def on_export(self):
        img = self.gump_mgr.get_gump(self.current_gump_id)
        if not img:
            QMessageBox.warning(self, "Export", "Selected gump has no image.")
            return

        fn, _ = QFileDialog.getSaveFileName(self, "Export Gump Image", f"gump_0x{self.current_gump_id:04X}.png", "PNG Files (*.png)")
        if fn:
            img.save(fn)
            QMessageBox.information(self, "Export", f"Saved to {fn}")

    def on_replace(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Replace Gump Image", "", "PNG Files (*.png)")
        if fn:
            try:
                from PIL import Image
                new_img = Image.open(fn)
                self.gump_mgr.replace_gump(self.current_gump_id, new_img)
                self.load_gump(self.current_gump_id)
                QMessageBox.information(self, "Replace", f"Replaced gump 0x{self.current_gump_id:04X}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {e}")

    def on_remove(self):
        self.gump_mgr.remove_gump(self.current_gump_id)
        self.load_gump(self.current_gump_id)
