"""
Export Sprites Dialog: Exports all frames of all directions of an animation into a PNG spritesheet.
Supports grid layout (8 directions x frames), horizontal/vertical strips, anchor alignment,
and optional JSON metadata export.
"""

import os
import json
from typing import List, Optional, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QCheckBox, QPushButton, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from uofiddler.core.animations import AnimationsManager
from uofiddler.core.defs import DefsManager, AnimationDef
from PIL import Image

ACTIONS_MONSTER = [
    (0, "Walk"), (1, "Stand / Idle"), (2, "Die 1"), (3, "Die 2"),
    (4, "Attack 1"), (5, "Attack 2"), (6, "Attack 3"),
    (7, "Cast / Special 1"), (8, "Cast / Special 2"), (9, "Get Hit"),
    (10, "Block Right"), (11, "Block Left"), (12, "Idle"),
    (13, "Fidget"), (14, "Fly"), (15, "Take Off"), (16, "Get Hit In Air"),
]

ACTIONS_SEA = [
    (0, "Walk"), (1, "Run"), (2, "Idle 1"), (3, "Idle 2"),
    (4, "Fidget"), (5, "Attack 1"), (6, "Attack 2"), (7, "Get Hit"), (8, "Die 1"),
]

ACTIONS_ANIMAL = [
    (0, "Walk"), (1, "Run"), (2, "Idle 1"), (3, "Eat"), (4, "Alert"),
    (5, "Attack 1"), (6, "Attack 2"), (7, "Get Hit"), (8, "Die 1"),
    (9, "Idle 2"), (10, "Fidget"), (11, "Lie Down"), (12, "Die 2"),
]

ACTIONS_HUMAN = [
    (0, "Walk_01"), (1, "WalkStaff_01"), (2, "Run_01"), (3, "RunStaff_01"),
    (4, "Idle_01"), (5, "Idle_02"), (6, "Fidget_Yawn_Stretch_01"),
    (7, "CombatIdle1H_01"), (8, "CombatIdle2H_01"), (9, "AttackSlash1H_01"),
    (10, "AttackPierce1H_01"), (11, "AttackBash1H_01"), (12, "AttackBash2H_01"),
    (13, "AttackSlash2H_01"), (14, "AttackPierce2H_01"), (15, "CombatAdvance_1H_01"),
    (16, "Spell1"), (17, "Spell2"), (18, "AttackBow_01"), (19, "AttackCrossbow_01"),
    (20, "GetHit_Fr_Hi_01"), (21, "GetHit_Fr_Med_01"), (22, "GetHit_Fr_Low_01"),
    (23, "Block_Shield_01"), (24, "Punch_01"), (25, "Bow_01"), (26, "Salute_01"),
    (27, "Ingest_Eat_01"), (28, "Horse_Walk_01"), (29, "Horse_Run_01"),
    (30, "Horse_Idle_01"), (31, "Horse_Attack1H_01"), (32, "Horse_AttackBow_01"),
    (33, "Horse_AttackCrossbow_01"), (34, "Horse_Spell2_01"),
    (35, "Die_Hard_Fwd_01"), (36, "Die_Hard_Back_01"),
]

DIRECTION_NAMES = {
    0: "0 - South (Sul)",
    1: "1 - South-West (Sudoeste)",
    2: "2 - West (Oeste)",
    3: "3 - North-West (Noroeste)",
    4: "4 - North (Norte)",
    5: "5 - North-East (Nordeste)",
    6: "6 - East (Leste)",
    7: "7 - South-East (Sudeste)",
}


class ExportSpritesDialog(QDialog):
    def __init__(self, parent=None, initial_body: int = 400, initial_action: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Exportar sprites da Animação")
        self.resize(580, 520)

        self.anim_mgr = AnimationsManager.get_instance()
        self.defs_mgr = DefsManager.get_instance()

        self.initial_body = initial_body
        self.initial_action = initial_action

        self._cached_sheet: Optional[Image.Image] = None
        self._cached_meta: dict = {}

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # 1. Animation Selection Group
        sel_box = QGroupBox("Seleção da Animação")
        form_sel = QFormLayout(sel_box)
        form_sel.setSpacing(6)

        self.combo_body = QComboBox()
        self.combo_body.currentIndexChanged.connect(self.on_body_combo_changed)

        body_spin_row = QHBoxLayout()
        self.spin_body = QSpinBox()
        self.spin_body.setRange(0, 65535)
        self.spin_body.setValue(self.initial_body)
        self.spin_body.valueChanged.connect(self.on_body_spin_changed)
        body_spin_row.addWidget(self.spin_body)

        self.lbl_storage_tag = QLabel("[MUL]")
        self.lbl_storage_tag.setStyleSheet("font-weight: bold; color: #4caf50;")
        body_spin_row.addWidget(self.lbl_storage_tag)

        self.combo_action = QComboBox()
        self.combo_action.currentIndexChanged.connect(self.update_preview_info)

        form_sel.addRow("Corpo:", self.combo_body)
        form_sel.addRow("Body ID:", body_spin_row)
        form_sel.addRow("Ação:", self.combo_action)
        main_layout.addWidget(sel_box)

        # 2. Spritesheet Format Options
        opt_box = QGroupBox("Formato e Alinhamento do Spritesheet")
        form_opt = QFormLayout(opt_box)
        form_opt.setSpacing(6)

        self.combo_layout = QComboBox()
        self.combo_layout.addItem("Grade (8 Linhas: 1 linha por direção) [Recomendado]", "grid")
        self.combo_layout.addItem("Faixa Horizontal (Linha única contínua)", "horizontal")
        self.combo_layout.addItem("Faixa Vertical (Coluna única contínua)", "vertical")
        self.combo_layout.currentIndexChanged.connect(self.update_preview_info)
        form_opt.addRow("Disposição:", self.combo_layout)

        self.chk_align = QCheckBox("Alinhar pelo ponto de ancoragem/centro original (evita oscilação de quadros)")
        self.chk_align.setChecked(True)
        self.chk_align.stateChanged.connect(self.update_preview_info)
        form_opt.addRow("Ancoragem:", self.chk_align)

        padding_row = QHBoxLayout()
        self.spin_padding = QSpinBox()
        self.spin_padding.setRange(0, 32)
        self.spin_padding.setValue(0)
        self.spin_padding.valueChanged.connect(self.update_preview_info)
        padding_row.addWidget(self.spin_padding)
        padding_row.addWidget(QLabel("px entre células"))
        padding_row.addStretch()
        form_opt.addRow("Espaçamento:", padding_row)

        self.chk_json = QCheckBox("Salvar metadados (.json) com mapeamento dos frames e dimensões")
        self.chk_json.setChecked(True)
        form_opt.addRow("Metadados:", self.chk_json)

        main_layout.addWidget(opt_box)

        # 3. Preview and Summary Box
        summary_box = QGroupBox("Resumo dos Sprites")
        sum_layout = QVBoxLayout(summary_box)
        sum_layout.setSpacing(4)

        self.lbl_status = QLabel("Carregando...")
        self.lbl_status.setStyleSheet("font-weight: bold; font-size: 13px;")
        sum_layout.addWidget(self.lbl_status)

        self.lbl_details = QLabel("-")
        self.lbl_details.setStyleSheet("color: #b0bec5; font-size: 12px; line-height: 140%;")
        sum_layout.addWidget(self.lbl_details)

        main_layout.addWidget(summary_box)

        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_export = QPushButton("Exportar PNG...")
        self.btn_export.setStyleSheet("font-weight: bold; padding: 6px 16px; background-color: #2e7d32; color: white;")
        self.btn_export.clicked.connect(self.on_export_clicked)
        btn_layout.addWidget(self.btn_export)

        main_layout.addLayout(btn_layout)

        # Populate initial bodies and actions
        self.populate_bodies()

    def populate_bodies(self):
        self.combo_body.blockSignals(True)
        self.combo_body.clear()

        all_entries = list(self.defs_mgr.anim_entries)
        for entry in all_entries:
            tag = "[UOP]" if entry.is_uop else "[MUL]"
            self.combo_body.addItem(f"{tag} {entry.body} - {entry.name}", entry.body)

        self.combo_body.blockSignals(False)

        idx = self.combo_body.findData(self.initial_body)
        if idx >= 0:
            self.combo_body.setCurrentIndex(idx)
        elif self.combo_body.count() > 0:
            self.combo_body.setCurrentIndex(0)

        cur_body = self.combo_body.currentData() or self.initial_body
        self.spin_body.blockSignals(True)
        self.spin_body.setValue(cur_body)
        self.spin_body.blockSignals(False)

        self.populate_actions_for_body(cur_body, select_action=self.initial_action)
        self.update_preview_info()

    def on_body_combo_changed(self, idx: int):
        b_id = self.combo_body.currentData()
        if b_id is not None and b_id != self.spin_body.value():
            self.spin_body.blockSignals(True)
            self.spin_body.setValue(b_id)
            self.spin_body.blockSignals(False)
            self.populate_actions_for_body(b_id)
            self.update_preview_info()

    def on_body_spin_changed(self, val: int):
        idx = self.combo_body.findData(val)
        if idx >= 0:
            self.combo_body.blockSignals(True)
            self.combo_body.setCurrentIndex(idx)
            self.combo_body.blockSignals(False)
        self.populate_actions_for_body(val)
        self.update_preview_info()

    def populate_actions_for_body(self, body: int, select_action: Optional[int] = None):
        entry = self.defs_mgr.get_animation_def(body)
        mob_type = entry.mob_type if entry else 0
        is_uop = self.defs_mgr.is_uop_body(body)

        if is_uop:
            self.lbl_storage_tag.setText("[UOP]")
            self.lbl_storage_tag.setStyleSheet("font-weight: bold; color: #29b6f6;")
        else:
            self.lbl_storage_tag.setText("[MUL]")
            self.lbl_storage_tag.setStyleSheet("font-weight: bold; color: #66bb6a;")

        if mob_type == 1:
            base_actions = ACTIONS_SEA
        elif mob_type == 2:
            base_actions = ACTIONS_ANIMAL
        elif mob_type == 3:
            base_actions = ACTIONS_HUMAN
        else:
            base_actions = ACTIONS_MONSTER

        prev_act = select_action if select_action is not None else self.combo_action.currentData()
        if prev_act is None:
            prev_act = 0

        self.combo_action.blockSignals(True)
        self.combo_action.clear()

        for act_id, act_name in base_actions:
            defined = self.anim_mgr.is_action_defined(body, act_id)
            check = "✓ " if defined else "   "
            self.combo_action.addItem(f"{check}{act_id} - {act_name}", act_id)

        if is_uop:
            max_act = len(base_actions)
            for act_id in range(max_act, 80):
                if self.anim_mgr.is_action_defined(body, act_id):
                    self.combo_action.addItem(f"✓ {act_id} - Action {act_id}", act_id)

        sel_idx = self.combo_action.findData(prev_act)
        if sel_idx >= 0:
            self.combo_action.setCurrentIndex(sel_idx)
        else:
            picked = False
            for i in range(self.combo_action.count()):
                if self.combo_action.itemText(i).startswith("✓"):
                    self.combo_action.setCurrentIndex(i)
                    picked = True
                    break
            if not picked and self.combo_action.count() > 0:
                self.combo_action.setCurrentIndex(0)

        self.combo_action.blockSignals(False)

    def update_preview_info(self):
        body = self.spin_body.value()
        action = self.combo_action.currentData()
        if action is None:
            action = 0

        layout_mode = self.combo_layout.currentData() or "grid"
        align_anchor = self.chk_align.isChecked()
        padding = self.spin_padding.value()

        sheet, meta = self.anim_mgr.create_spritesheet(
            body=body,
            action=action,
            directions=list(range(8)),
            layout=layout_mode,
            align_anchor=align_anchor,
            padding=padding,
        )

        self._cached_sheet = sheet
        self._cached_meta = meta

        if sheet is None or not meta:
            self.lbl_status.setText("⚠️ Nenhum frame encontrado para esta animação.")
            self.lbl_status.setStyleSheet("font-weight: bold; color: #ffb74d;")
            self.lbl_details.setText(
                "A animação selecionada não contém sprites nos arquivos MUL ou UOP.\n"
                "Tente selecionar outra ação identificada com '✓'."
            )
            self.btn_export.setEnabled(False)
            return

        self.btn_export.setEnabled(True)
        self.lbl_status.setText("✅ Animação pronta para exportação")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #4caf50;")

        layout_desc = {
            "grid": f"Grade de 8 Linhas x {meta['cols']} Colunas",
            "horizontal": f"Faixa Horizontal (1 linha x {meta['cols']} frames)",
            "vertical": f"Faixa Vertical ({meta['rows']} linhas x 1 coluna)",
        }.get(layout_mode, layout_mode)

        self.lbl_details.setText(
            f"• <b>Direções:</b> 8 direções (0: Sul até 7: Sudeste)\n"
            f"• <b>Quadros por direção:</b> {meta['max_frames']} quadros (Total de {meta['total_frames']} sprites)\n"
            f"• <b>Dimensão por célula:</b> {meta['cell_width']} x {meta['cell_height']} px (Âncora: X={meta['anchor_x']}, Y={meta['anchor_y']})\n"
            f"• <b>Dimensões finais da imagem:</b> {meta['total_width']} x {meta['total_height']} px\n"
            f"• <b>Disposição:</b> {layout_desc}"
        )

    def on_export_clicked(self):
        if not self._cached_sheet or not self._cached_meta:
            QMessageBox.warning(self, "Exportar sprites", "Nenhum frame disponível para exportar.")
            return

        body = self.spin_body.value()
        action = self.combo_action.currentData() or 0
        action_text = self.combo_action.currentText().replace("✓", "").strip()
        safe_action = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in action_text)
        default_filename = f"spritesheet_body_{body}_act_{action}_{safe_action}.png"

        fn, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar sprites da Animação",
            default_filename,
            "PNG Files (*.png)"
        )
        if not fn:
            return

        try:
            self._cached_sheet.save(fn, "PNG")

            if self.chk_json.isChecked():
                json_path = os.path.splitext(fn)[0] + ".json"
                entry = self.defs_mgr.get_animation_def(body)
                body_name = entry.name if entry else f"Corpo {body}"

                meta_export = dict(self._cached_meta)
                meta_export["body_name"] = body_name
                meta_export["action_name"] = action_text
                meta_export["directions_map"] = DIRECTION_NAMES

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(meta_export, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self,
                "Exportar sprites",
                f"Spritesheet exportada com sucesso!\n\n"
                f"Arquivo: {fn}\n"
                f"Dimensões: {self._cached_meta['total_width']} x {self._cached_meta['total_height']} px\n"
                f"Total de sprites: {self._cached_meta['total_frames']}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar", f"Falha ao salvar spritesheet:\n{e}")
