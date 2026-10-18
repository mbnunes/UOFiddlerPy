"""
Modern splash screen for UOFiddlerPy with styled dark theme and dynamic loading progress bar.
"""

import time
from PyQt6.QtWidgets import QSplashScreen, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor, QFont
from PyQt6.QtWidgets import QApplication


class SplashScreen(QSplashScreen):
    """
    Polished dark-themed splash screen with progress bar and dynamic status updates.
    """

    def __init__(self, width: int = 540, height: int = 280):
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("#181820"))
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)

        # Central container widget with rounded border
        container = QWidget(self)
        container.setGeometry(0, 0, width, height)
        container.setStyleSheet("""
            QWidget {
                background-color: #181820;
                color: #e0e0e0;
                border: 1px solid #3f51b5;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(8)

        # Title
        title_lbl = QLabel("⚔️  UOFiddlerPy")
        title_lbl.setStyleSheet("border: none; color: #ffffff; font-size: 26px; font-weight: bold;")
        layout.addWidget(title_lbl)

        # Subtitle
        sub_lbl = QLabel("Ultima Online Native Linux Asset Editor")
        sub_lbl.setStyleSheet("border: none; color: #9e9eab; font-size: 13px;")
        layout.addWidget(sub_lbl)

        # Badges row
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(6)
        badges_layout.setContentsMargins(0, 4, 0, 0)
        for badge_text in ["100% Python", "PyQt6", "No .NET / Wine", "Cross-Distro"]:
            badge = QLabel(f" {badge_text} ")
            badge.setStyleSheet("""
                border: 1px solid #38384d;
                background-color: #232330;
                color: #b0b0c8;
                border-radius: 4px;
                font-size: 11px;
                padding: 2px 6px;
            """)
            badges_layout.addWidget(badge)
        badges_layout.addStretch()
        layout.addLayout(badges_layout)

        layout.addStretch()

        # Dynamic Status Label
        self.lbl_msg = QLabel("Inicializando aplicação...")
        self.lbl_msg.setStyleSheet("border: none; color: #d0d0dc; font-size: 12px; font-weight: 500;")
        layout.addWidget(self.lbl_msg)

        # Styled Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #262633;
                border: 1px solid #38384a;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #3f51b5;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)

        # Footer version label
        footer_lbl = QLabel("v1.0.0 — Native Linux Edition")
        footer_lbl.setStyleSheet("border: none; color: #6a6a7c; font-size: 11px;")
        layout.addWidget(footer_lbl)

    def set_progress(self, val: int, msg: str, pause_ms: int = 80):
        """Updates progress bar value, status message, and processes Qt events."""
        self.progress.setValue(val)
        self.lbl_msg.setText(msg)
        QApplication.processEvents()
        if pause_ms > 0:
            time.sleep(pause_ms / 1000.0)
            QApplication.processEvents()
