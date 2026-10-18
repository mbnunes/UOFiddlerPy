"""
Textures Tab: Terrain textures viewer, inspector, and editor with PNG export/import.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from uofiddler.core.textures import TextureManager
from uofiddler.gui.widgets.image_canvas import ImageCanvas
from uofiddler.gui.widgets.virtual_tile_view import TileBrowserWidget


class TexturesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tex_mgr = TextureManager.get_instance()
        self.current_tex_id = 0
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Browser Widget (Grid default + List view option)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.browser = TileBrowserWidget(self, grid_size=QSize(72, 72), icon_size=QSize(48, 48))
        valid_ids = [
            i for i, entry in enumerate(self.tex_mgr._file_index.entries) if entry.is_valid
        ] if self.tex_mgr._file_index else []

        self.browser.set_data(
            count=len(valid_ids),
            ids=valid_ids,
            get_label=self.get_tex_label,
            get_image=self.tex_mgr.get_texture,
            get_tooltip=self.get_tex_tooltip,
            columns=["ID", "Hex", "Dimensions", "Graphic"],
        )
        left_layout.addWidget(self.browser)

        splitter.addWidget(left_widget)

        # Right panel: Canvas, Info, Actions
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.canvas = ImageCanvas(self)
        self.canvas.setMinimumSize(250, 250)
        right_layout.addWidget(self.canvas, stretch=2)

        prop_box = QGroupBox("Texture Properties")
        form_layout = QFormLayout(prop_box)
        self.lbl_id = QLabel("0 (0x0000)")
        self.lbl_size = QLabel("-")
        form_layout.addRow("Texture ID:", self.lbl_id)
        form_layout.addRow("Dimensions:", self.lbl_size)
        right_layout.addWidget(prop_box)

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

        self.browser.itemSelected.connect(self.load_tex)
        if valid_ids:
            self.select_tex(valid_ids[0])

    def get_tex_label(self, tex_id: int) -> str:
        if self.tex_mgr._file_index and tex_id < len(self.tex_mgr._file_index.entries):
            entry = self.tex_mgr._file_index.entries[tex_id]
            if entry.is_valid:
                return "128x128" if entry.extra != 0 else "64x64"
        return ""

    def get_tex_tooltip(self, tex_id: int) -> str:
        dim = self.get_tex_label(tex_id)
        return f"Texture 0x{tex_id:04X} ({tex_id}) [{dim}]" if dim else f"Texture 0x{tex_id:04X} ({tex_id})"

    def select_tex(self, tex_id: int):
        self.browser.select_id(tex_id)

    def load_tex(self, tex_id: int):
        self.current_tex_id = tex_id
        img = self.tex_mgr.get_texture(tex_id)
        self.canvas.set_pil_image(img)

        self.lbl_id.setText(f"{tex_id} (0x{tex_id:04X})")
        if img:
            self.lbl_size.setText(f"{img.width} x {img.height} px")
        else:
            self.lbl_size.setText("(empty)")

    def on_export(self):
        img = self.tex_mgr.get_texture(self.current_tex_id)
        if not img:
            QMessageBox.warning(self, "Export", "Selected texture has no image.")
            return

        fn, _ = QFileDialog.getSaveFileName(self, "Export Texture", f"texture_0x{self.current_tex_id:04X}.png", "PNG Files (*.png)")
        if fn:
            img.save(fn)
            QMessageBox.information(self, "Export", f"Saved to {fn}")

    def on_replace(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Replace Texture", "", "Images (*.png *.bmp *.jpg)")
        if fn:
            try:
                from PIL import Image
                new_img = Image.open(fn)
                self.tex_mgr.replace(self.current_tex_id, new_img)
                self.browser.refresh()
                self.load_tex(self.current_tex_id)
                QMessageBox.information(self, "Replace", f"Replaced texture 0x{self.current_tex_id:04X}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {e}")

    def on_remove(self):
        self.tex_mgr.remove(self.current_tex_id)
        self.browser.refresh()
        self.load_tex(self.current_tex_id)
