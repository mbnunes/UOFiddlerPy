"""
GameData Tab: Enhanced Client (3D) GameData.uop inspector, viewer, and exporter.
Displays all 79 CSV/XML configuration tables with table grid view, raw text, and export features.
"""

import os
import csv
import json
import io
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QTabWidget, QTableWidget, QTableWidgetItem,
    QPlainTextEdit, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from uofiddler.core.gamedata import GameDataManager, GameDataEntry


class GameDataTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gdm = GameDataManager.get_instance()
        self.current_entry: Optional[GameDataEntry] = None
        self.all_table_names = []
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Search, List, and Export buttons
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Search bar
        search_box = QGroupBox("Filter Tables")
        search_layout = QVBoxLayout(search_box)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter table names or hash...")
        self.search_input.textChanged.connect(self.on_filter_changed)
        search_layout.addWidget(self.search_input)
        left_layout.addWidget(search_box)

        # Tables List
        self.list_widget = QListWidget()
        self.populate_tables()
        self.list_widget.currentRowChanged.connect(self.on_table_selected)
        left_layout.addWidget(self.list_widget)

        # Batch Export
        export_box = QGroupBox("Export")
        export_layout = QVBoxLayout(export_box)
        btn_export_csv = QPushButton("Export Current (CSV)")
        btn_export_csv.clicked.connect(self.on_export_csv)
        btn_export_json = QPushButton("Export Current (JSON)")
        btn_export_json.clicked.connect(self.on_export_json)
        btn_export_all = QPushButton("Export All 79 Tables...")
        btn_export_all.clicked.connect(self.on_export_all)

        export_layout.addWidget(btn_export_csv)
        export_layout.addWidget(btn_export_json)
        export_layout.addWidget(btn_export_all)
        left_layout.addWidget(export_box)

        splitter.addWidget(left_widget)

        # Right panel: Table Details, Table View, Raw Text View
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Info Box
        info_box = QGroupBox("Table Information")
        info_form = QFormLayout(info_box)
        self.lbl_name = QLabel("-")
        self.lbl_hash = QLabel("-")
        self.lbl_dimensions = QLabel("-")
        self.lbl_sizes = QLabel("-")

        info_form.addRow("Table Name:", self.lbl_name)
        info_form.addRow("Hash (64-bit):", self.lbl_hash)
        info_form.addRow("Rows / Columns:", self.lbl_dimensions)
        info_form.addRow("Compressed / Decompressed:", self.lbl_sizes)
        right_layout.addWidget(info_box)

        # Sub-tabs: Table View vs Raw Text
        self.views_tabs = QTabWidget()

        # 1. Structured Table View
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Row filter
        row_filter_layout = QHBoxLayout()
        row_filter_layout.addWidget(QLabel("Search in table:"))
        self.row_filter_input = QLineEdit()
        self.row_filter_input.setPlaceholderText("Filter rows...")
        self.row_filter_input.textChanged.connect(self.on_row_filter_changed)
        row_filter_layout.addWidget(self.row_filter_input)
        table_layout.addLayout(row_filter_layout)

        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table_layout.addWidget(self.table_widget)
        self.views_tabs.addTab(table_container, "📊 Table View")

        # 2. Raw Text View
        self.raw_text_view = QPlainTextEdit()
        self.raw_text_view.setReadOnly(True)
        mono_font = QFont("monospace")
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self.raw_text_view.setFont(mono_font)
        self.views_tabs.addTab(self.raw_text_view, "📝 Raw CSV / Text View")

        right_layout.addWidget(self.views_tabs, stretch=1)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def populate_tables(self):
        self.list_widget.clear()
        self.all_table_names = self.gdm.list_table_names()

        for name in self.all_table_names:
            entry = self.gdm.entries_by_name.get(name)
            if entry:
                display_text = f"[{entry.index:02d}] {name}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, name)
                self.list_widget.addItem(item)

    def on_filter_changed(self, text: str):
        query = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            name = item.data(Qt.ItemDataRole.UserRole)
            item.setHidden(query not in name.lower())

    def on_table_selected(self, row: int):
        if row < 0:
            return
        item = self.list_widget.item(row)
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        self.load_table(name)

    def load_table(self, name: str):
        entry = self.gdm.entries_by_name.get(name)
        if not entry or not entry.raw_data:
            self.clear_display()
            return

        self.current_entry = entry
        raw_text = entry.raw_data.decode("latin1", errors="replace")
        self.raw_text_view.setPlainText(raw_text)

        # Parse CSV
        f = io.StringIO(raw_text)
        reader = csv.reader(f)
        rows = []
        for r in reader:
            if r:
                rows.append(r)

        # Populate table widget
        if rows:
            # Check if first row is header
            headers = rows[0]
            data_rows = rows[1:]

            self.table_widget.clear()
            self.table_widget.setColumnCount(len(headers))
            self.table_widget.setHorizontalHeaderLabels([h.strip() for h in headers])
            self.table_widget.setRowCount(len(data_rows))

            for r_idx, row in enumerate(data_rows):
                for c_idx in range(len(headers)):
                    val = row[c_idx] if c_idx < len(row) else ""
                    cell = QTableWidgetItem(val.strip())
                    cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table_widget.setItem(r_idx, c_idx, cell)

            n_rows = len(data_rows)
            n_cols = len(headers)
        else:
            self.table_widget.clear()
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            n_rows = 0
            n_cols = 0

        # Update Info Box
        self.lbl_name.setText(f"<b>{entry.name}</b> (Index {entry.index})")
        self.lbl_hash.setText(f"<code>0x{entry.hash:016X}</code>")
        self.lbl_dimensions.setText(f"{n_rows} rows, {n_cols} columns")
        self.lbl_sizes.setText(
            f"{entry.compressed_size:,} bytes compressed / {entry.decompressed_size:,} bytes decompressed"
        )

        self.row_filter_input.clear()

    def on_row_filter_changed(self, text: str):
        query = text.strip().lower()
        for r in range(self.table_widget.rowCount()):
            if not query:
                self.table_widget.setRowHidden(r, False)
                continue
            match = False
            for c in range(self.table_widget.columnCount()):
                item = self.table_widget.item(r, c)
                if item and query in item.text().lower():
                    match = True
                    break
            self.table_widget.setRowHidden(r, not match)

    def clear_display(self):
        self.lbl_name.setText("-")
        self.lbl_hash.setText("-")
        self.lbl_dimensions.setText("-")
        self.lbl_sizes.setText("-")
        self.table_widget.clear()
        self.raw_text_view.clear()
        self.current_entry = None

    def on_export_csv(self):
        if not self.current_entry or not self.current_entry.raw_data:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {self.current_entry.name}",
            self.current_entry.name,
            "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            with open(path, "wb") as f:
                f.write(self.current_entry.raw_data)
            QMessageBox.information(self, "Export", f"Successfully exported to:\n{path}")

    def on_export_json(self):
        if not self.current_entry or not self.current_entry.raw_data:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {self.current_entry.name} as JSON",
            os.path.splitext(self.current_entry.name)[0] + ".json",
            "JSON Files (*.json);;All Files (*)"
        )
        if path:
            raw_text = self.current_entry.raw_data.decode("latin1", errors="replace")
            f = io.StringIO(raw_text)
            reader = csv.DictReader(f)
            data = list(reader)
            with open(path, "w", encoding="utf-8") as out:
                json.dump(data, out, indent=4)
            QMessageBox.information(self, "Export", f"Successfully exported {len(data)} items to JSON:\n{path}")

    def on_export_all(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory to Export All Tables")
        if folder:
            count = 0
            for name, entry in self.gdm.entries_by_name.items():
                if entry.raw_data:
                    out_path = os.path.join(folder, entry.name)
                    with open(out_path, "wb") as f:
                        f.write(entry.raw_data)
                    count += 1
            QMessageBox.information(self, "Export All", f"Successfully exported {count} tables to:\n{folder}")
