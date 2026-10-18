"""
Modern dark theme styling (QSS) for UOFiddlerPy.
Provides crisp, professional dark UI with native look and feel on any Linux distribution.
"""

DARK_THEME_QSS = """
QMainWindow, QDialog {
    background-color: #1e1e24;
    color: #e0e0e0;
}

QWidget {
    background-color: #1e1e24;
    color: #e0e0e0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #33333d;
    background-color: #23232b;
    top: -1px;
}

QTabBar::tab {
    background-color: #18181d;
    color: #9e9eab;
    padding: 7px 14px;
    border: 1px solid #282832;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #23232b;
    color: #ffffff;
    border-color: #3f51b5;
    border-bottom: 2px solid #3f51b5;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #2a2a35;
    color: #d0d0d8;
}

QMenuBar {
    background-color: #18181d;
    color: #e0e0e0;
    border-bottom: 1px solid #2b2b35;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
}

QMenuBar::item:selected {
    background-color: #2d2d38;
}

QMenu {
    background-color: #23232b;
    color: #e0e0e0;
    border: 1px solid #383845;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #3f51b5;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #383845;
    margin: 4px 0px;
}

QToolBar {
    background-color: #1e1e24;
    border-bottom: 1px solid #2b2b35;
    padding: 4px;
    spacing: 4px;
}

QPushButton {
    background-color: #2c2c36;
    color: #ffffff;
    border: 1px solid #40404f;
    border-radius: 4px;
    padding: 6px 14px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #383846;
    border-color: #525266;
}

QPushButton:pressed, QPushButton:checked {
    background-color: #3f51b5;
    border-color: #5c6bc0;
    font-weight: bold;
}

QPushButton:disabled {
    background-color: #1f1f26;
    color: #656573;
    border-color: #2b2b35;
}

QLineEdit, QSpinBox, QComboBox {
    background-color: #141418;
    color: #ffffff;
    border: 1px solid #383845;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #3f51b5;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #5c6bc0;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #383845;
}

QListView, QTableView, QTreeView {
    background-color: #141418;
    color: #e0e0e0;
    border: 1px solid #30303c;
    border-radius: 4px;
    alternate-background-color: #18181f;
    selection-background-color: #3f51b5;
    selection-color: #ffffff;
}

QListView::item {
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 2px;
}

QListView::item:hover {
    background-color: #272733;
    border: 1px solid #454559;
}

QListView::item:selected {
    background-color: #3f51b5;
    color: #ffffff;
    border: 1px solid #637bfe;
}

QHeaderView::section {
    background-color: #1b1b22;
    color: #bbbbcc;
    padding: 5px;
    border: 1px solid #2b2b35;
    font-weight: bold;
}

QScrollBar:vertical {
    background: #141418;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #333340;
    min-height: 24px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: #454556;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #141418;
    height: 12px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #333340;
    min-width: 24px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background: #454556;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QGroupBox {
    border: 1px solid #333340;
    border-radius: 6px;
    margin-top: 18px;
    padding-top: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #8c9eff;
}

QCheckBox {
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    background-color: #141418;
    border: 1px solid #404050;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    background-color: #3f51b5;
    border-color: #5c6bc0;
}

QStatusBar {
    background-color: #141418;
    color: #9090a0;
    border-top: 1px solid #282833;
}

QSplitter::handle {
    background-color: #2b2b35;
}

QSplitter::handle:hover {
    background-color: #3f51b5;
}
"""
