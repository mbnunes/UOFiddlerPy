"""
Sounds Tab: Audio player, WAV exporter/importer, and sound.mul inspector.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from uofiddler.core.sounds import SoundManager


class SoundsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sound_mgr = SoundManager.get_instance()
        self.current_sound_id = 0
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
        self.search_input.setPlaceholderText("Sound ID or Name...")
        self.search_input.returnPressed.connect(self.on_search)
        search_btn = QPushButton("Go")
        search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        left_layout.addLayout(search_layout)

        self.list_widget = QListWidget()
        self.populate_list()
        self.list_widget.currentRowChanged.connect(self.on_sound_selected)
        left_layout.addWidget(self.list_widget)

        splitter.addWidget(left_widget)

        # Right panel: Player & Actions
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        prop_box = QGroupBox("Sound Details")
        form_layout = QFormLayout(prop_box)
        self.lbl_id = QLabel("0 (0x0000)")
        self.lbl_name = QLabel("-")
        self.lbl_len = QLabel("-")

        form_layout.addRow("Sound ID:", self.lbl_id)
        form_layout.addRow("Name / Tag:", self.lbl_name)
        form_layout.addRow("Audio Size:", self.lbl_len)
        right_layout.addWidget(prop_box)

        # Player
        player_box = QGroupBox("Audio Playback")
        player_layout = QVBoxLayout(player_box)

        self.play_btn = QPushButton("▶ Play Sound")
        self.play_btn.setMinimumHeight(36)
        self.play_btn.clicked.connect(self.on_play)
        player_layout.addWidget(self.play_btn)
        right_layout.addWidget(player_box)

        # Export/Import Actions
        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Export WAV")
        export_btn.clicked.connect(self.on_export)
        import_btn = QPushButton("Import WAV")
        import_btn.clicked.connect(self.on_import)

        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(import_btn)
        right_layout.addLayout(btn_layout)
        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def populate_list(self):
        self.list_widget.clear()
        for i in range(self.sound_mgr.max_sounds):
            if self.sound_mgr.is_valid(i):
                sound = self.sound_mgr.get_sound(i)
                name_str = f" - {sound.name}" if sound and sound.name else ""
                item = QListWidgetItem(f"Sound 0x{i:04X} ({i}){name_str}")
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.list_widget.addItem(item)

    def on_sound_selected(self, row: int):
        if row < 0:
            return
        item = self.list_widget.item(row)
        if not item:
            return
        sound_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_sound(sound_id)

    def load_sound(self, sound_id: int):
        self.current_sound_id = sound_id
        sound = self.sound_mgr.get_sound(sound_id)

        self.lbl_id.setText(f"{sound_id} (0x{sound_id:04X})")
        if sound:
            self.lbl_name.setText(sound.name or "(no name)")
            self.lbl_len.setText(f"{len(sound.wav_bytes)} bytes (WAV 22050Hz Mono)")
        else:
            self.lbl_name.setText("(empty)")
            self.lbl_len.setText("-")

    def on_play(self):
        self.sound_mgr.play_sound(self.current_sound_id)

    def on_export(self):
        sound = self.sound_mgr.get_sound(self.current_sound_id)
        if not sound or not sound.wav_bytes:
            QMessageBox.warning(self, "Export", "Selected sound is empty.")
            return

        fn, _ = QFileDialog.getSaveFileName(self, "Export WAV", f"sound_0x{self.current_sound_id:04X}.wav", "WAV Files (*.wav)")
        if fn:
            with open(fn, "wb") as f:
                f.write(sound.wav_bytes)
            QMessageBox.information(self, "Export", f"Saved to {fn}")

    def on_import(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Import WAV", "", "WAV Files (*.wav)")
        if fn:
            try:
                with open(fn, "rb") as f:
                    wav_data = f.read()
                # Store
                self.sound_mgr._cache[self.current_sound_id] = SoundEntry(
                    sound_id=self.current_sound_id,
                    name=os.path.basename(fn),
                    wav_bytes=wav_data
                )
                self.load_sound(self.current_sound_id)
                QMessageBox.information(self, "Import", "Sound imported.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import WAV: {e}")

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
        except ValueError:
            pass

        q = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if q in item.text().lower():
                self.list_widget.setCurrentRow(i)
                self.list_widget.scrollToItem(item)
                return
        QMessageBox.information(self, "Search", f"No sound found matching '{text}'")
