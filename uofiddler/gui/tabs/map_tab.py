"""
Map Tab: Interactive Google Maps-style world map viewer for Ultima Online.
Allows fluid mouse-drag panning, cursor-centered mouse wheel zooming, coordinate jumping,
preset locations, and real-time cursor coordinate tracking.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from uofiddler.core.maps import MapManager
from uofiddler.gui.widgets.interactive_map_view import InteractiveMapView


# Famous Ultima Online landmark presets: (MapID, Name, X, Y)
PRESET_LOCATIONS = [
    (0, "Britain Bank [Felucca]", 1420, 1690),
    (0, "Lord British's Castle", 1390, 1625),
    (0, "West Britain Bank", 1435, 1680),
    (0, "Moonglow Bank", 4470, 1175),
    (0, "Trinsic Bank", 1815, 2820),
    (0, "Yew Bank", 540, 980),
    (0, "Minoc Bank", 2470, 540),
    (0, "Skara Brae", 630, 2230),
    (0, "Jhelom", 1400, 3810),
    (0, "Magincia", 3730, 2160),
    (0, "Buccaneer's Den", 2705, 2160),
    (0, "Vesper Bank", 2895, 675),
    (0, "Cove", 2240, 1210),
    (0, "Ocllo", 3650, 2520),
    (0, "Nujel'm", 3750, 1270),
    (0, "Delucia [Lost Lands]", 5260, 3990),
    (0, "Papua [Lost Lands]", 5730, 3210),
    (0, "Wind", 5165, 245),
    (1, "Britain Bank [Trammel]", 1420, 1690),
    (2, "Ilshenar Entrance", 845, 640),
    (3, "Luna Bank [Malas]", 990, 520),
    (3, "Umbra Bank [Malas]", 2090, 1340),
    (4, "Zento Bank [Tokuno]", 730, 1245),
    (5, "Royal City [Ter Mur]", 850, 3520),
]


class MapTab(QWidget):
    """
    Google Maps-style interactive Ultima Online world map viewer.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.map_mgr = MapManager.get_instance()
        self.current_map_id = 0
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # 1. Top Control Toolbar (Google Maps Style)
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #1a1a22;
                border: 1px solid #2e2e3d;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        tool_layout = QHBoxLayout(toolbar)
        tool_layout.setContentsMargins(8, 4, 8, 4)
        tool_layout.setSpacing(8)

        # Facet Selector
        lbl_map = QLabel("🌐 Mapa:")
        lbl_map.setStyleSheet("font-weight: bold; color: #ffffff;")
        self.facet_combo = QComboBox()
        for m in self.map_mgr.maps:
            self.facet_combo.addItem(f"{m.name} ({m.width}x{m.height})", m.map_id)
        self.facet_combo.currentIndexChanged.connect(self.on_facet_changed)

        tool_layout.addWidget(lbl_map)
        tool_layout.addWidget(self.facet_combo)

        # Landmarks / Cities Preset Selector
        lbl_preset = QLabel("📍 Localização:")
        lbl_preset.setStyleSheet("font-weight: bold; color: #ffffff;")
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Selecione um local famoso...", None)
        for map_id, name, x, y in PRESET_LOCATIONS:
            self.preset_combo.addItem(f"{name} ({x}, {y})", (map_id, x, y))
        self.preset_combo.currentIndexChanged.connect(self.on_preset_selected)

        tool_layout.addWidget(lbl_preset)
        tool_layout.addWidget(self.preset_combo)

        # Coordinates Jump Inputs
        lbl_coord = QLabel("Coord:")
        lbl_coord.setStyleSheet("color: #b0b0c0;")
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 8192)
        self.spin_x.setValue(1420)
        self.spin_x.setPrefix("X: ")
        self.spin_x.setFixedWidth(85)
        self.spin_x.returnPressed.connect(self.on_goto)

        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 8192)
        self.spin_y.setValue(1690)
        self.spin_y.setPrefix("Y: ")
        self.spin_y.setFixedWidth(85)
        self.spin_y.returnPressed.connect(self.on_goto)

        btn_goto = QPushButton("Ir")
        btn_goto.setFixedWidth(40)
        btn_goto.clicked.connect(self.on_goto)

        tool_layout.addWidget(lbl_coord)
        tool_layout.addWidget(self.spin_x)
        tool_layout.addWidget(self.spin_y)
        tool_layout.addWidget(btn_goto)

        # Statics Toggle
        self.chk_statics = QCheckBox("Statics")
        self.chk_statics.setChecked(True)
        self.chk_statics.toggled.connect(self.on_statics_toggled)
        tool_layout.addWidget(self.chk_statics)

        tool_layout.addStretch()

        # Zoom Controls
        btn_zoom_in = QPushButton("🔍 +")
        btn_zoom_in.setToolTip("Zoom In (Mouse Wheel)")
        btn_zoom_in.clicked.connect(lambda: self.map_view.zoom_in())

        btn_zoom_out = QPushButton("🔍 −")
        btn_zoom_out.setToolTip("Zoom Out (Mouse Wheel)")
        btn_zoom_out.clicked.connect(lambda: self.map_view.zoom_out())

        btn_reset_zoom = QPushButton("100%")
        btn_reset_zoom.setToolTip("Restaurar Zoom para 1:1")
        btn_reset_zoom.clicked.connect(lambda: self.map_view.reset_zoom())

        btn_fit_map = QPushButton("🗺️ Ver Todo o Mapa")
        btn_fit_map.setToolTip("Ajustar todo o continente na tela")
        btn_fit_map.clicked.connect(lambda: self.map_view.fit_whole_map())

        tool_layout.addWidget(btn_zoom_in)
        tool_layout.addWidget(btn_zoom_out)
        tool_layout.addWidget(btn_reset_zoom)
        tool_layout.addWidget(btn_fit_map)

        main_layout.addWidget(toolbar)

        # 2. Main Full Interactive Map Canvas
        self.map_view = InteractiveMapView(self)
        self.map_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.map_view.coordinatesChanged.connect(self.on_cursor_coords_changed)
        self.map_view.centerChanged.connect(self.on_center_coords_changed)
        self.map_view.zoomChanged.connect(self.on_zoom_changed)
        main_layout.addWidget(self.map_view, stretch=1)

        # Alias for backwards compatibility with tests and scripts
        self.canvas = self.map_view

        # 3. Bottom Status Bar / HUD
        hud_frame = QFrame()
        hud_frame.setStyleSheet("""
            QFrame {
                background-color: #14141c;
                border: 1px solid #282835;
                border-radius: 4px;
                padding: 2px 8px;
            }
        """)
        hud_layout = QHBoxLayout(hud_frame)
        hud_layout.setContentsMargins(6, 3, 6, 3)

        self.lbl_cursor = QLabel("Cursor: (1420, 1690)")
        self.lbl_cursor.setStyleSheet("color: #637bfe; font-weight: bold; font-size: 12px;")

        self.lbl_center = QLabel("Centro: (1420, 1690)")
        self.lbl_center.setStyleSheet("color: #ffffff; font-size: 12px;")

        self.lbl_zoom = QLabel("Zoom: 100%")
        self.lbl_zoom.setStyleSheet("color: #b0b0c0; font-size: 12px;")

        lbl_hint = QLabel("💡 Arraste com o mouse para navegar livremente pelo mapa. Use a roda do mouse para dar zoom.")
        lbl_hint.setStyleSheet("color: #727282; font-size: 11px;")

        hud_layout.addWidget(self.lbl_cursor)
        hud_layout.addWidget(self.lbl_center)
        hud_layout.addWidget(self.lbl_zoom)
        hud_layout.addStretch()
        hud_layout.addWidget(lbl_hint)

        main_layout.addWidget(hud_frame)

    def on_facet_changed(self):
        self.current_map_id = self.facet_combo.currentData() or 0
        self.map_view.set_map_id(self.current_map_id)

    def on_preset_selected(self):
        data = self.preset_combo.currentData()
        if not data:
            return
        map_id, x, y = data
        if map_id != self.current_map_id:
            # Switch facet combo
            idx = self.facet_combo.findData(map_id)
            if idx >= 0:
                self.facet_combo.setCurrentIndex(idx)
        self.spin_x.setValue(x)
        self.spin_y.setValue(y)
        self.map_view.go_to(x, y, zoom=1.5)

    def on_goto(self):
        x = self.spin_x.value()
        y = self.spin_y.value()
        self.map_view.go_to(x, y)

    def on_statics_toggled(self, checked: bool):
        self.map_view.set_show_statics(checked)

    def on_cursor_coords_changed(self, wx: int, wy: int):
        self.lbl_cursor.setText(f"Cursor: ({wx}, {wy})")

    def on_center_coords_changed(self, cx: int, cy: int):
        self.lbl_center.setText(f"Centro: ({cx}, {cy})")
        self.spin_x.blockSignals(True)
        self.spin_y.blockSignals(True)
        self.spin_x.setValue(cx)
        self.spin_y.setValue(cy)
        self.spin_x.blockSignals(False)
        self.spin_y.blockSignals(False)

    def on_zoom_changed(self, zoom: float):
        self.lbl_zoom.setText(f"Zoom: {int(zoom * 100)}%")

    def render_map(self):
        """Backwards compatibility helper."""
        self.map_view.update()

    def pan(self, dx: int, dy: int):
        """Backwards compatibility helper."""
        self.map_view.center_x += dx
        self.map_view.center_y += dy
        self.map_view.update()
