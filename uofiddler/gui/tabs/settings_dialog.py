"""
Settings Dialog: Configure Ultima Online directory path, auto-detection, and options.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QCheckBox, QGroupBox, QFormLayout, QMessageBox
)
from uofiddler.core.files import FileManager


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UOFiddlerPy - Path Settings")
        self.resize(560, 320)
        self.fm = FileManager.get_instance()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Path Group
        path_box = QGroupBox("Ultima Online Directory")
        path_layout = QVBoxLayout(path_box)

        input_row = QHBoxLayout()
        self.txt_dir = QLineEdit(self.fm.uo_dir or "")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.on_browse)
        auto_btn = QPushButton("Auto-Detect")
        auto_btn.clicked.connect(self.on_auto_detect)

        input_row.addWidget(self.txt_dir)
        input_row.addWidget(browse_btn)
        input_row.addWidget(auto_btn)
        path_layout.addLayout(input_row)

        layout.addWidget(path_box)

        # File Status Group
        status_box = QGroupBox("File Detection Status")
        self.status_form = QFormLayout(status_box)
        self.lbl_art = QLabel()
        self.lbl_tiledata = QLabel()
        self.lbl_hues = QLabel()
        self.lbl_gumps = QLabel()
        self.lbl_sound = QLabel()

        self.status_form.addRow("Art (art.mul / uop):", self.lbl_art)
        self.status_form.addRow("TileData (tiledata.mul):", self.lbl_tiledata)
        self.status_form.addRow("Hues (hues.mul):", self.lbl_hues)
        self.status_form.addRow("Gumps (gumpart.mul / uop):", self.lbl_gumps)
        self.status_form.addRow("Sounds (sound.mul / uop):", self.lbl_sound)
        layout.addWidget(status_box)

        self.update_status_labels()

        # Options
        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)
        self.chk_hs = QCheckBox("High Seas TileData & Multi format")
        self.chk_hs.setChecked(self.fm.high_seas)
        opt_layout.addWidget(self.chk_hs)
        layout.addWidget(opt_box)

        # Dialog Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save & Reload All")
        save_btn.clicked.connect(self.on_save_reload)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def update_status_labels(self):
        def fmt(path):
            if path:
                return f"<font color='#4caf50'>✔ Found:</font> {os.path.basename(path)}"
            return "<font color='#f44336'>✘ Not Found</font>"

        self.lbl_art.setText(fmt(self.fm.get_file_path("artLegacyMUL.uop") or self.fm.get_file_path("art.mul")))
        self.lbl_tiledata.setText(fmt(self.fm.get_file_path("tiledata.mul")))
        self.lbl_hues.setText(fmt(self.fm.get_file_path("hues.mul")))
        self.lbl_gumps.setText(fmt(self.fm.get_file_path("gumpartLegacyMUL.uop") or self.fm.get_file_path("gumpart.mul")))
        self.lbl_sound.setText(fmt(self.fm.get_file_path("soundLegacyMUL.uop") or self.fm.get_file_path("sound.mul")))

    def on_browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Ultima Online Directory", self.txt_dir.text())
        if d:
            self.txt_dir.setText(d)
            self.fm.set_uo_dir(d)
            self.update_status_labels()

    def on_auto_detect(self):
        detected = self.fm.auto_detect_dir()
        if detected:
            self.txt_dir.setText(detected)
            self.update_status_labels()
            QMessageBox.information(self, "Auto-Detect", f"Detected UO at:\n{detected}")
        else:
            QMessageBox.warning(self, "Auto-Detect", "Could not locate a standard UO installation directory.")

    def on_save_reload(self):
        new_dir = self.txt_dir.text().strip()
        if not os.path.isdir(new_dir):
            QMessageBox.critical(self, "Error", "Directory does not exist.")
            return

        self.fm.high_seas = self.chk_hs.isChecked()
        self.fm.set_uo_dir(new_dir)
        self.accept()
