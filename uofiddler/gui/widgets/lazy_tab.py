"""
LazyTabWrapper: On-demand tab loader with elegant loading indicator and progress bar.
Defers heavy tab initialization until first activation, keeping startup instantaneous (<1s).
"""

from typing import Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt6.QtCore import Qt


class LazyTabWrapper(QWidget):
    """
    Wrapper widget for deferred (lazy) tab loading.
    Displays a modern dark-themed loading card with progress indicator upon first click,
    constructs the real tab widget, and seamlessly delegates all attribute accesses.
    """

    def __init__(self, tab_name: str, factory: Callable[[QWidget], QWidget], parent=None):
        super().__init__(parent)
        self.tab_name = tab_name
        self.factory = factory
        self.real_tab: Optional[QWidget] = None
        self.is_loaded = False

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)

        # Placeholder loading container
        self.placeholder = QWidget(self)
        p_layout = QVBoxLayout(self.placeholder)
        p_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p_layout.setSpacing(10)

        # Title
        self.lbl_title = QLabel(f"Carregando {tab_name}...")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        self.lbl_sub = QLabel("Lendo e indexando dados do cliente Ultima Online...")
        self.lbl_sub.setStyleSheet("font-size: 12px; color: #9e9eab;")
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Progress bar
        self.pbar = QProgressBar(self.placeholder)
        self.pbar.setRange(0, 0)  # Animated indeterminate marquee pulse
        self.pbar.setFixedWidth(320)
        self.pbar.setFixedHeight(8)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet("""
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

        p_layout.addWidget(self.lbl_title)
        p_layout.addWidget(self.lbl_sub)
        p_layout.addWidget(self.pbar)

        self._main_layout.addWidget(self.placeholder)

    def load(self) -> QWidget:
        """Loads the real tab widget if not already loaded, replacing the placeholder."""
        if self.is_loaded and self.real_tab is not None:
            return self.real_tab

        # Paint the loading placeholder immediately
        QApplication.processEvents()

        # Construct the heavy tab
        self.real_tab = self.factory(self)

        # Swap out placeholder
        self.placeholder.hide()
        self._main_layout.removeWidget(self.placeholder)
        self.placeholder.deleteLater()
        self._main_layout.addWidget(self.real_tab)
        self.is_loaded = True

        return self.real_tab

    def __getattr__(self, name):
        """Transparently forwards any attribute/method calls to the real tab instance."""
        if not self.is_loaded:
            self.load()
        if self.real_tab is not None and hasattr(self.real_tab, name):
            return getattr(self.real_tab, name)
        raise AttributeError(f"'{type(self).__name__}' ({self.tab_name}) has no attribute '{name}'")
