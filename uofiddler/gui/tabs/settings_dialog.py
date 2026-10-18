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

        # Classic UO (2D) Path Group
        path_box = QGroupBox("Ultima Online Classic (2D) Directory")
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

        # Enhanced Client (3D) Path Group
        ec_box = QGroupBox("Ultima Online Enhanced (3D) Directory")
        ec_layout = QVBoxLayout(ec_box)

        ec_input_row = QHBoxLayout()
        self.txt_ec_dir = QLineEdit(self.fm.uo_ec_dir or "")
        ec_browse_btn = QPushButton("Browse...")
        ec_browse_btn.clicked.connect(self.on_browse_ec)
        ec_auto_btn = QPushButton("Auto-Detect")
        ec_auto_btn.clicked.connect(self.on_auto_detect_ec)

        ec_input_row.addWidget(self.txt_ec_dir)
        ec_input_row.addWidget(ec_browse_btn)
        ec_input_row.addWidget(ec_auto_btn)
        ec_layout.addLayout(ec_input_row)

        layout.addWidget(ec_box)

        # File Status Group
        status_box = QGroupBox("File Detection Status")
        self.status_form = QFormLayout(status_box)
        self.lbl_art = QLabel()
        self.lbl_tiledata = QLabel()
        self.lbl_gumps = QLabel()
        self.lbl_gamedata = QLabel()
        self.lbl_tileart = QLabel()

        self.status_form.addRow("Classic Art (artLegacyMUL.uop / art.mul):", self.lbl_art)
        self.status_form.addRow("TileData (tiledata.mul):", self.lbl_tiledata)
        self.status_form.addRow("Gumps (gumpartLegacyMUL.uop / mul):", self.lbl_gumps)
        self.status_form.addRow("3D GameData (GameData.uop):", self.lbl_gamedata)
        self.status_form.addRow("3D TileArt (tileart.uop):", self.lbl_tileart)
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
            if path and os.path.exists(path):
                return f"<font color='#4caf50'>✔ Found:</font> {os.path.basename(path)}"
            return "<font color='#f44336'>✘ Not Found</font>"

        self.lbl_art.setText(fmt(self.fm.get_file_path("artLegacyMUL.uop") or self.fm.get_file_path("art.mul")))
        self.lbl_tiledata.setText(fmt(self.fm.get_file_path("tiledata.mul")))
        self.lbl_gumps.setText(fmt(self.fm.get_file_path("gumpartLegacyMUL.uop") or self.fm.get_ec_file_path("gumpartLegacyMUL.uop") or self.fm.get_file_path("gumpart.mul")))
        self.lbl_gamedata.setText(fmt(self.fm.get_ec_file_path("GameData.uop") or self.fm.get_file_path("GameData.uop")))
        self.lbl_tileart.setText(fmt(self.fm.get_ec_file_path("tileart.uop") or self.fm.get_file_path("tileart.uop")))

    def on_browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Ultima Online Classic Directory", self.txt_dir.text())
        if d:
            self.txt_dir.setText(d)
            self.fm.set_uo_dir(d)
            self.update_status_labels()

    def on_browse_ec(self):
        d = QFileDialog.getExistingDirectory(self, "Select Ultima Online Enhanced (3D) Directory", self.txt_ec_dir.text())
        if d:
            self.txt_ec_dir.setText(d)
            self.fm.set_uo_ec_dir(d)
            self.update_status_labels()

    def on_auto_detect(self):
        detected = self.fm.auto_detect_dir()
        if detected:
            self.txt_dir.setText(detected)
            self.update_status_labels()
            QMessageBox.information(self, "Auto-Detect", f"Detected Classic UO at:\n{detected}")
        else:
            QMessageBox.warning(self, "Auto-Detect", "Could not locate a standard UO installation directory.")

    def on_auto_detect_ec(self):
        detected = self.fm.auto_detect_ec_dir()
        if detected:
            self.txt_ec_dir.setText(detected)
            self.update_status_labels()
            QMessageBox.information(self, "Auto-Detect EC", f"Detected Enhanced UO (3D) at:\n{detected}")
        else:
            QMessageBox.warning(self, "Auto-Detect EC", "Could not locate an Enhanced UO installation directory.")

    def on_save_reload(self):
        new_dir = self.txt_dir.text().strip()
        if new_dir and not os.path.isdir(new_dir):
            QMessageBox.critical(self, "Error", "Classic directory does not exist.")
            return

        new_ec_dir = self.txt_ec_dir.text().strip()
        if new_ec_dir and not os.path.isdir(new_ec_dir):
            QMessageBox.critical(self, "Error", "Enhanced (3D) directory does not exist.")
            return

        self.fm.high_seas = self.chk_hs.isChecked()
        if new_dir and os.path.isdir(new_dir):
            self.fm.set_uo_dir(new_dir)
        if new_ec_dir and os.path.isdir(new_ec_dir):
            self.fm.set_uo_ec_dir(new_ec_dir)
        self.accept()

