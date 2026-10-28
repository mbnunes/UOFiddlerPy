"""
Animations Tab: Monster, Animal, Human, and Equipment animation player.
Supports anim.mul through anim6.mul, AnimationFrame1.uop through AnimationFrame6.uop,
AnimationSequence.uop, category filtering, search, and frame inspection.
"""

from typing import List, Dict, Tuple, Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QComboBox, QSlider, QSpinBox,
    QScrollArea, QFrame, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from uofiddler.core.animations import AnimationsManager, AnimationFrame
from uofiddler.core.defs import DefsManager, AnimationDef
from uofiddler.gui.widgets.image_canvas import ImageCanvas
from uofiddler.gui.tabs.export_sprites_dialog import ExportSpritesDialog

ACTIONS_MONSTER = [
    (0, "Walk"),
    (1, "Stand / Idle"),
    (2, "Die 1"),
    (3, "Die 2"),
    (4, "Attack 1"),
    (5, "Attack 2"),
    (6, "Attack 3"),
    (7, "Cast / Special 1"),
    (8, "Cast / Special 2"),
    (9, "Get Hit"),
    (10, "Block Right"),
    (11, "Block Left"),
    (12, "Idle"),
    (13, "Fidget"),
    (14, "Fly"),
    (15, "Take Off"),
    (16, "Get Hit In Air"),
]

ACTIONS_SEA = [
    (0, "Walk"),
    (1, "Run"),
    (2, "Idle 1"),
    (3, "Idle 2"),
    (4, "Fidget"),
    (5, "Attack 1"),
    (6, "Attack 2"),
    (7, "Get Hit"),
    (8, "Die 1"),
]

ACTIONS_ANIMAL = [
    (0, "Walk"),
    (1, "Run"),
    (2, "Idle 1"),
    (3, "Eat"),
    (4, "Alert"),
    (5, "Attack 1"),
    (6, "Attack 2"),
    (7, "Get Hit"),
    (8, "Die 1"),
    (9, "Idle 2"),
    (10, "Fidget"),
    (11, "Lie Down"),
    (12, "Die 2"),
]

ACTIONS_HUMAN = [
    (0, "Walk_01"),
    (1, "WalkStaff_01"),
    (2, "Run_01"),
    (3, "RunStaff_01"),
    (4, "Idle_01"),
    (5, "Idle_02"),
    (6, "Fidget_Yawn_Stretch_01"),
    (7, "CombatIdle1H_01"),
    (8, "CombatIdle2H_01"),
    (9, "AttackSlash1H_01"),
    (10, "AttackPierce1H_01"),
    (11, "AttackBash1H_01"),
    (12, "AttackBash2H_01"),
    (13, "AttackSlash2H_01"),
    (14, "AttackPierce2H_01"),
    (15, "CombatAdvance_1H_01"),
    (16, "Spell1"),
    (17, "Spell2"),
    (18, "AttackBow_01"),
    (19, "AttackCrossbow_01"),
    (20, "GetHit_Fr_Hi_01"),
    (21, "GetHit_Fr_Med_01"),
    (22, "GetHit_Fr_Low_01"),
    (23, "Block_Shield_01"),
    (24, "Punch_01"),
    (25, "Bow_01"),
    (26, "Salute_01"),
    (27, "Ingest_Eat_01"),
    (28, "Horse_Walk_01"),
    (29, "Horse_Run_01"),
    (30, "Horse_Idle_01"),
    (31, "Horse_Attack1H_01"),
    (32, "Horse_AttackBow_01"),
    (33, "Horse_AttackCrossbow_01"),
    (34, "Horse_Spell2_01"),
    (35, "Die_Hard_Fwd_01"),
    (36, "Die_Hard_Back_01"),
]

DIRECTIONS = [
    (0, "0 - South (Sul)"),
    (1, "1 - South-West (Sudoeste)"),
    (2, "2 - West (Oeste)"),
    (3, "3 - North-West (Noroeste)"),
    (4, "4 - North (Norte)"),
    (5, "5 - North-East (Nordeste - Espelhado)"),
    (6, "6 - East (Leste - Espelhado)"),
    (7, "7 - South-East (Sudeste - Espelhado)"),
]


class AnimationsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.anim_mgr = AnimationsManager.get_instance()
        self.defs_mgr = DefsManager.get_instance()
        self.frames: List[AnimationFrame] = []
        self.current_frame_idx = 0
        self._all_entries: List[AnimationDef] = []

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_tick)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # ----------------- Left panel: Search & Selection Controls -----------------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        # Category Filter & Search Box
        filter_box = QGroupBox("Filtrar Criaturas / Animações")
        filter_layout = QVBoxLayout(filter_box)
        filter_layout.setSpacing(4)

        cat_row = QHBoxLayout()
        cat_row.addWidget(QLabel("Categoria:"))
        self.combo_category = QComboBox()
        self.combo_category.addItem("Todos", None)
        self.combo_category.addItem("Monstros", 0)
        self.combo_category.addItem("Criaturas Marinhas", 1)
        self.combo_category.addItem("Animais", 2)
        self.combo_category.addItem("Humanos / Elfos / Gargoyles", 3)
        self.combo_category.addItem("Equipamentos / Armaduras", "equip")
        self.combo_category.addItem("UOP Modernos (Stygian/TOL)", "uop")
        self.combo_category.currentIndexChanged.connect(self.on_filter_changed)
        cat_row.addWidget(self.combo_category)
        filter_layout.addLayout(cat_row)

        search_row = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Filtrar por nome ou ID (ex: dragon, 713, gargoyle)...")
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.textChanged.connect(self.on_filter_changed)
        search_row.addWidget(self.txt_search)
        filter_layout.addLayout(search_row)

        left_layout.addWidget(filter_box)

        # Body selection
        ctrl_box = QGroupBox("Seleção de Corpo e Ação")
        form = QFormLayout(ctrl_box)
        form.setSpacing(6)

        self.body_combo = QComboBox()
        self.body_combo.currentIndexChanged.connect(self.on_body_combo_changed)

        body_id_row = QHBoxLayout()
        self.body_spin = QSpinBox()
        self.body_spin.setRange(0, 65535)
        self.body_spin.setValue(400)
        self.body_spin.valueChanged.connect(self.on_body_spin_changed)
        body_id_row.addWidget(self.body_spin)

        self.lbl_format = QLabel("[MUL]")
        self.lbl_format.setStyleSheet("font-weight: bold; color: #4caf50;")
        body_id_row.addWidget(self.lbl_format)

        self.action_combo = QComboBox()
        self.action_combo.currentIndexChanged.connect(self.reload_frames)

        self.dir_combo = QComboBox()
        for d_id, d_name in DIRECTIONS:
            self.dir_combo.addItem(d_name, d_id)
        self.dir_combo.currentIndexChanged.connect(self.reload_frames)

        form.addRow("Corpo:", self.body_combo)
        form.addRow("Body ID:", body_id_row)
        form.addRow("Ação:", self.action_combo)
        form.addRow("Direção:", self.dir_combo)
        left_layout.addWidget(ctrl_box)

        # Playback Controls
        play_box = QGroupBox("Controles de Reprodução")
        play_layout = QVBoxLayout(play_box)
        play_layout.setSpacing(6)

        btn_row = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Anterior")
        self.prev_btn.clicked.connect(self.on_prev_frame)
        self.play_btn = QPushButton("▶ Reproduzir")
        self.play_btn.clicked.connect(self.toggle_play)
        self.next_btn = QPushButton("Próximo ▶")
        self.next_btn.clicked.connect(self.on_next_frame)

        btn_row.addWidget(self.prev_btn)
        btn_row.addWidget(self.play_btn)
        btn_row.addWidget(self.next_btn)
        play_layout.addLayout(btn_row)

        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Velocidade:"))
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(2, 30)
        self.fps_slider.setValue(10)
        self.fps_slider.valueChanged.connect(self.on_speed_changed)
        speed_row.addWidget(self.fps_slider)
        self.lbl_fps = QLabel("10 fps")
        self.lbl_fps.setFixedWidth(45)
        speed_row.addWidget(self.lbl_fps)
        play_layout.addLayout(speed_row)

        self.lbl_frame_info = QLabel("Quadro: 0 / 0")
        self.lbl_frame_info.setStyleSheet("color: #9fa8da; font-weight: bold;")
        play_layout.addWidget(self.lbl_frame_info)

        left_layout.addWidget(play_box)

        # Details box
        details_box = QGroupBox("Informações Técnicas")
        det_layout = QFormLayout(details_box)
        self.lbl_det_name = QLabel("-")
        self.lbl_det_type = QLabel("-")
        self.lbl_det_storage = QLabel("-")
        self.lbl_det_res = QLabel("-")
        det_layout.addRow("Nome:", self.lbl_det_name)
        det_layout.addRow("Tipo:", self.lbl_det_type)
        det_layout.addRow("Origem:", self.lbl_det_storage)
        det_layout.addRow("Dimensões:", self.lbl_det_res)
        left_layout.addWidget(details_box)

        # Export box
        export_box = QGroupBox("Exportação")
        export_layout = QVBoxLayout(export_box)
        export_layout.setSpacing(6)
        self.btn_export_sprites = QPushButton("Exportar sprites")
        self.btn_export_sprites.setStyleSheet("font-weight: bold; padding: 6px;")
        self.btn_export_sprites.setToolTip("Exportar todos os frames de todas as direções da animação em um arquivo PNG")
        self.btn_export_sprites.clicked.connect(self.on_export_sprites)
        export_layout.addWidget(self.btn_export_sprites)
        left_layout.addWidget(export_box)

        left_layout.addStretch()
        splitter.addWidget(left_widget)

        # ----------------- Right panel: Big Image Canvas -----------------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        self.canvas = ImageCanvas(self)
        self.canvas.setMinimumSize(450, 450)
        right_layout.addWidget(self.canvas)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        # Load all entries from DefsManager
        self._all_entries = list(self.defs_mgr.anim_entries)
        self.populate_body_combo()

    def on_filter_changed(self):
        self.populate_body_combo()

    def populate_body_combo(self):
        cat_filter = self.combo_category.currentData()
        search_txt = self.txt_search.text().strip().lower()

        self.body_combo.blockSignals(True)
        self.body_combo.clear()

        matched_count = 0
        for entry in self._all_entries:
            # Filter by category
            if cat_filter is not None:
                if cat_filter == "equip":
                    if not entry.is_equip:
                        continue
                elif cat_filter == "uop":
                    if not entry.is_uop:
                        continue
                elif isinstance(cat_filter, int):
                    if entry.mob_type != cat_filter:
                        continue

            # Filter by search text
            if search_txt:
                s_id = str(entry.body)
                h_id = f"0x{entry.body:x}"
                if search_txt not in entry.name.lower() and search_txt not in s_id and search_txt not in h_id:
                    continue

            tag = "[UOP]" if entry.is_uop else "[MUL]"
            display = f"{tag} {entry.body} - {entry.name}"
            self.body_combo.addItem(display, entry.body)
            matched_count += 1

        self.body_combo.blockSignals(False)

        # Re-select current body if present, else first
        cur_body = self.body_spin.value()
        idx = self.body_combo.findData(cur_body)
        if idx >= 0:
            self.body_combo.setCurrentIndex(idx)
        elif self.body_combo.count() > 0:
            self.body_combo.setCurrentIndex(0)
            b = self.body_combo.currentData()
            if b is not None:
                self.body_spin.blockSignals(True)
                self.body_spin.setValue(b)
                self.body_spin.blockSignals(False)
                self.populate_actions_for_body(b)
                self.reload_frames()

    def on_body_combo_changed(self, idx: int):
        b_id = self.body_combo.currentData()
        if b_id is not None and b_id != self.body_spin.value():
            self.body_spin.blockSignals(True)
            self.body_spin.setValue(b_id)
            self.body_spin.blockSignals(False)
            self.populate_actions_for_body(b_id)
            self.reload_frames()

    def on_body_spin_changed(self, val: int):
        # Sync combo if present
        idx = self.body_combo.findData(val)
        if idx >= 0:
            self.body_combo.blockSignals(True)
            self.body_combo.setCurrentIndex(idx)
            self.body_combo.blockSignals(False)

        self.populate_actions_for_body(val)
        self.reload_frames()

    def populate_actions_for_body(self, body: int):
        entry = self.defs_mgr.get_animation_def(body)
        mob_type = entry.mob_type if entry else 0
        is_uop = self.defs_mgr.is_uop_body(body)

        if is_uop:
            self.lbl_format.setText("[UOP]")
            self.lbl_format.setStyleSheet("font-weight: bold; color: #29b6f6;")
        else:
            self.lbl_format.setText("[MUL]")
            self.lbl_format.setStyleSheet("font-weight: bold; color: #66bb6a;")

        if mob_type == 1:
            base_actions = ACTIONS_SEA
            type_str = "Criatura Marinha"
        elif mob_type == 2:
            base_actions = ACTIONS_ANIMAL
            type_str = "Animal"
        elif mob_type == 3:
            base_actions = ACTIONS_HUMAN
            type_str = "Equipamento / Humano" if (entry and entry.is_equip) else "Humano / Humanoide"
        else:
            base_actions = ACTIONS_MONSTER
            type_str = "Monstro"

        self.lbl_det_name.setText(entry.name if entry else f"Corpo {body}")
        self.lbl_det_type.setText(type_str)
        self.lbl_det_storage.setText("AnimationFrame*.uop" if is_uop else "Anim*.mul / Anim*.idx")

        # Remember currently selected action
        prev_act = self.action_combo.currentData() or 0

        self.action_combo.blockSignals(True)
        self.action_combo.clear()

        # Add base actions
        for act_id, act_name in base_actions:
            defined = self.anim_mgr.is_action_defined(body, act_id)
            check = "✓ " if defined else "   "
            self.action_combo.addItem(f"{check}{act_id} - {act_name}", act_id)

        # For UOP or special bodies that have extra actions beyond the base table
        if is_uop:
            max_act = len(base_actions)
            for act_id in range(max_act, 80):
                if self.anim_mgr.is_action_defined(body, act_id):
                    self.action_combo.addItem(f"✓ {act_id} - Action {act_id}", act_id)

        # Restore action or pick first defined
        sel_idx = self.action_combo.findData(prev_act)
        if sel_idx >= 0:
            self.action_combo.setCurrentIndex(sel_idx)
        else:
            # Pick first with a checkmark if available
            picked = False
            for i in range(self.action_combo.count()):
                if self.action_combo.itemText(i).startswith("✓"):
                    self.action_combo.setCurrentIndex(i)
                    picked = True
                    break
            if not picked and self.action_combo.count() > 0:
                self.action_combo.setCurrentIndex(0)

        self.action_combo.blockSignals(False)

    def reload_frames(self):
        body = self.body_spin.value()
        action = self.action_combo.currentData()
        if action is None:
            action = 0
        direction = self.dir_combo.currentData()
        if direction is None:
            direction = 0

        self.frames = self.anim_mgr.get_animation_frames(body=body, action=action, direction=direction)
        self.current_frame_idx = 0
        self.show_current_frame()

    def show_current_frame(self):
        if not self.frames:
            self.canvas.set_pil_image(None)
            self.lbl_frame_info.setText("Quadro: 0 / 0 (Sem animação encontrada)")
            self.lbl_det_res.setText("-")
            return

        idx = self.current_frame_idx % len(self.frames)
        frame = self.frames[idx]
        self.canvas.set_pil_image(frame.image)
        self.lbl_frame_info.setText(
            f"Quadro: {idx + 1} / {len(self.frames)}  (Centro: X={frame.center_x}, Y={frame.center_y})"
        )
        if frame.image:
            self.lbl_det_res.setText(f"{frame.image.width} x {frame.image.height} px")

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
            self.play_btn.setText("▶ Reproduzir")
        else:
            if not self.frames:
                return
            fps = self.fps_slider.value()
            self.timer.start(int(1000 / fps))
            self.play_btn.setText("⏸ Pausar")

    def on_timer_tick(self):
        if not self.frames:
            return
        self.current_frame_idx = (self.current_frame_idx + 1) % len(self.frames)
        self.show_current_frame()

    def on_prev_frame(self):
        if not self.frames:
            return
        self.current_frame_idx = (self.current_frame_idx - 1) % len(self.frames)
        self.show_current_frame()

    def on_next_frame(self):
        if not self.frames:
            return
        self.current_frame_idx = (self.current_frame_idx + 1) % len(self.frames)
        self.show_current_frame()

    def on_speed_changed(self, value: int):
        self.lbl_fps.setText(f"{value} fps")
        if self.timer.isActive():
            self.timer.setInterval(int(1000 / value))

    def on_export_sprites(self):
        body = self.body_spin.value()
        action = self.action_combo.currentData()
        if action is None:
            action = 0
        dlg = ExportSpritesDialog(self, initial_body=body, initial_action=action)
        dlg.exec()
