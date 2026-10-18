"""
Skills Tab: Skills list, action button editor, skill groups, and skills.mul saver.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView, QListWidget
)
from PyQt6.QtCore import Qt
from uofiddler.core.skills import SkillsManager, SkillEntry


class SkillsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.skills_mgr = SkillsManager.get_instance()
        self.current_skill: Optional[SkillEntry] = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Skills table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Skills List (skills.mul):"))
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Skill Name", "Action Button"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.populate_table()
        self.table.currentCellChanged.connect(lambda r, c, pr, pc: self.on_skill_selected(r))
        left_layout.addWidget(self.table)

        splitter.addWidget(left_widget)

        # Right panel: Editor and Skill Groups
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        edit_box = QGroupBox("Edit Skill")
        form = QFormLayout(edit_box)

        self.lbl_id = QLabel("-")
        self.txt_name = QLineEdit()
        self.chk_action = QCheckBox("Has Action Button (Use Skill)")

        form.addRow("Skill ID:", self.lbl_id)
        form.addRow("Name:", self.txt_name)
        form.addRow("Action:", self.chk_action)

        apply_btn = QPushButton("Apply Edit")
        apply_btn.clicked.connect(self.on_apply_edit)
        form.addRow("", apply_btn)
        right_layout.addWidget(edit_box)

        # Skill Groups
        grp_box = QGroupBox("Skill Groups (skillgrp.mul)")
        grp_layout = QVBoxLayout(grp_box)
        self.grp_list = QListWidget()
        for g in self.skills_mgr.groups:
            self.grp_list.addItem(f"Group {g.index}: {g.name}")
        grp_layout.addWidget(self.grp_list)
        right_layout.addWidget(grp_box)

        save_btn = QPushButton("Save skills.mul")
        save_btn.clicked.connect(self.on_save)
        right_layout.addWidget(save_btn)
        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def populate_table(self):
        self.table.setRowCount(len(self.skills_mgr.skills))
        for r, s in enumerate(self.skills_mgr.skills):
            self.table.setItem(r, 0, QTableWidgetItem(str(s.index)))
            self.table.setItem(r, 1, QTableWidgetItem(s.name))
            self.table.setItem(r, 2, QTableWidgetItem("Yes" if s.has_action else "No"))

    def on_skill_selected(self, row: int):
        if 0 <= row < len(self.skills_mgr.skills):
            s = self.skills_mgr.skills[row]
            self.current_skill = s
            self.lbl_id.setText(str(s.index))
            self.txt_name.setText(s.name)
            self.chk_action.setChecked(s.has_action)

    def on_apply_edit(self):
        if not self.current_skill:
            return
        self.current_skill.name = self.txt_name.text()
        self.current_skill.has_action = self.chk_action.isChecked()
        row = self.table.currentRow()
        if row >= 0:
            self.table.setItem(row, 1, QTableWidgetItem(self.current_skill.name))
            self.table.setItem(row, 2, QTableWidgetItem("Yes" if self.current_skill.has_action else "No"))
        QMessageBox.information(self, "Applied", "Skill updated.")

    def on_save(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory to Save skills.mul & skills.idx")
        if dir_path:
            try:
                self.skills_mgr.save(dir_path)
                QMessageBox.information(self, "Saved", f"Saved skills files to {dir_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save skills: {e}")
