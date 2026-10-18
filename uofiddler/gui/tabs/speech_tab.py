"""
Speech Tab: Speech keywords viewer, search, and editor for speech.mul.
"""

from typing import List
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from uofiddler.core.speech import SpeechManager, SpeechEntry


class SpeechTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.speech_mgr = SpeechManager.get_instance()
        self.filtered_entries: List[SpeechEntry] = []
        self.current_entry: Optional[SpeechEntry] = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search Keyword:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter keywords or IDs...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.search_input.clear())
        search_layout.addWidget(clear_btn)
        main_layout.addLayout(search_layout)

        splitter = QSplitter(Qt.Orientation.Vertical, self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID (Hex)", "Keyword", "Order"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.apply_filter("")
        self.table.currentCellChanged.connect(lambda r, c, pr, pc: self.on_row_selected(r))
        splitter.addWidget(self.table)

        # Editor
        edit_box = QGroupBox("Edit Speech Entry")
        edit_layout = QHBoxLayout(edit_box)

        self.txt_keyword = QLineEdit()
        edit_layout.addWidget(QLabel("Keyword:"))
        edit_layout.addWidget(self.txt_keyword, stretch=1)

        apply_btn = QPushButton("Apply Edit")
        apply_btn.clicked.connect(self.on_apply)
        save_btn = QPushButton("Save speech.mul")
        save_btn.clicked.connect(self.on_save)

        edit_layout.addWidget(apply_btn)
        edit_layout.addWidget(save_btn)
        splitter.addWidget(edit_box)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

    def apply_filter(self, q: str):
        q = q.lower().strip()
        if not q:
            self.filtered_entries = list(self.speech_mgr.entries)
        else:
            self.filtered_entries = [
                e for e in self.speech_mgr.entries
                if q in e.keyword.lower() or q in f"0x{e.entry_id:04x}" or q in str(e.entry_id)
            ]

        self.table.setRowCount(len(self.filtered_entries))
        for r, e in enumerate(self.filtered_entries):
            self.table.setItem(r, 0, QTableWidgetItem(f"0x{e.entry_id:04X} ({e.entry_id})"))
            self.table.setItem(r, 1, QTableWidgetItem(e.keyword))
            self.table.setItem(r, 2, QTableWidgetItem(str(e.order)))

    def on_search(self, text: str):
        self.apply_filter(text)

    def on_row_selected(self, row: int):
        if 0 <= row < len(self.filtered_entries):
            e = self.filtered_entries[row]
            self.current_entry = e
            self.txt_keyword.setText(e.keyword)
        else:
            self.current_entry = None
            self.txt_keyword.clear()

    def on_apply(self):
        if not self.current_entry:
            return
        self.current_entry.keyword = self.txt_keyword.text()
        row = self.table.currentRow()
        if row >= 0:
            self.table.setItem(row, 1, QTableWidgetItem(self.current_entry.keyword))
        QMessageBox.information(self, "Applied", "Keyword updated.")

    def on_save(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save speech.mul", "speech.mul", "MUL Files (*.mul)")
        if fn:
            try:
                self.speech_mgr.save(fn)
                QMessageBox.information(self, "Saved", f"Saved speech.mul to {fn}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save speech.mul: {e}")
