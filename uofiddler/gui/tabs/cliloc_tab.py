"""
Cliloc Tab: Localization string table search, editor, entry creator, and cliloc.* saver.
"""

from typing import List
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFileDialog, QMessageBox, QTableView,
    QHeaderView, QTextEdit
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from uofiddler.core.cliloc import ClilocManager, ClilocEntry


class ClilocTableModel(QAbstractTableModel):
    def __init__(self, entries: List[ClilocEntry], parent=None):
        super().__init__(parent)
        self.entries = entries
        self.columns = ["Number", "Flag", "Text"]

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.entries)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.columns[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.entries):
            return None

        e = self.entries[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return str(e.number)
            elif col == 1:
                return str(e.flag)
            elif col == 2:
                return e.text
        elif role == Qt.ItemDataRole.TextAlignmentRole and col in (0, 1):
            return Qt.AlignmentFlag.AlignCenter

        return None


class ClilocTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cliloc_mgr = ClilocManager.get_instance()
        self.filtered_entries: List[ClilocEntry] = []
        self.current_entry: Optional[ClilocEntry] = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search Cliloc:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Number or Text...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.search_input.clear())
        search_layout.addWidget(clear_btn)
        main_layout.addLayout(search_layout)

        # Splitter: Table View on top, Editor on bottom
        splitter = QSplitter(Qt.Orientation.Vertical, self)

        # Table
        self.table_view = QTableView(self)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setVisible(False)

        self.apply_filter("")
        self.table_view.selectionModel().currentRowChanged.connect(self.on_row_selected)
        splitter.addWidget(self.table_view)

        # Editor Panel
        edit_box = QGroupBox("Edit Selected Entry")
        edit_layout = QVBoxLayout(edit_box)

        info_row = QHBoxLayout()
        self.lbl_num = QLabel("Number: -")
        self.lbl_flag = QLabel("Flag: -")
        info_row.addWidget(self.lbl_num)
        info_row.addWidget(self.lbl_flag)
        info_row.addStretch()
        edit_layout.addLayout(info_row)

        self.txt_edit = QTextEdit()
        self.txt_edit.setMaximumHeight(100)
        edit_layout.addWidget(self.txt_edit)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply Edit")
        apply_btn.clicked.connect(self.on_apply_edit)
        add_btn = QPushButton("Add New Entry...")
        add_btn.clicked.connect(self.on_add_entry)
        del_btn = QPushButton("Delete Entry")
        del_btn.clicked.connect(self.on_delete_entry)
        save_btn = QPushButton("Save cliloc file")
        save_btn.clicked.connect(self.on_save)

        btn_row.addWidget(apply_btn)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        edit_layout.addLayout(btn_row)

        splitter.addWidget(edit_box)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def apply_filter(self, query: str):
        if not query:
            self.filtered_entries = list(self.cliloc_mgr.entries)
        else:
            self.filtered_entries = self.cliloc_mgr.search(query)

        self.model = ClilocTableModel(self.filtered_entries, parent=self)
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_view.selectionModel().currentRowChanged.connect(self.on_row_selected)

    def on_search(self, text: str):
        self.apply_filter(text.strip())

    def on_row_selected(self, current: QModelIndex, previous: QModelIndex):
        if current.isValid() and current.row() < len(self.filtered_entries):
            e = self.filtered_entries[current.row()]
            self.current_entry = e
            self.lbl_num.setText(f"Number: {e.number}")
            self.lbl_flag.setText(f"Flag: {e.flag}")
            self.txt_edit.setPlainText(e.text)
        else:
            self.current_entry = None
            self.lbl_num.setText("Number: -")
            self.lbl_flag.setText("Flag: -")
            self.txt_edit.clear()

    def on_apply_edit(self):
        if not self.current_entry:
            return
        new_text = self.txt_edit.toPlainText()
        self.current_entry.text = new_text
        self.cliloc_mgr.set_entry(self.current_entry.number, new_text, self.current_entry.flag)
        self.model.layoutChanged.emit()
        QMessageBox.information(self, "Applied", "Entry updated.")

    def on_add_entry(self):
        # Find next free number
        max_num = max((e.number for e in self.cliloc_mgr.entries), default=1000000)
        new_num = max_num + 1
        self.cliloc_mgr.set_entry(new_num, "New string", 0)
        self.apply_filter(self.search_input.text())
        QMessageBox.information(self, "Added", f"Added new entry #{new_num}")

    def on_delete_entry(self):
        if not self.current_entry:
            return
        num = self.current_entry.number
        self.cliloc_mgr.remove_entry(num)
        self.apply_filter(self.search_input.text())
        QMessageBox.information(self, "Deleted", f"Deleted entry #{num}")

    def on_save(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save Cliloc", f"cliloc.{self.cliloc_mgr.lang}", "Cliloc Files (cliloc.*)")
        if fn:
            try:
                self.cliloc_mgr.save(fn)
                QMessageBox.information(self, "Saved", f"Saved cliloc to {fn}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save cliloc: {e}")
