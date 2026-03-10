"""Application color themes as Qt stylesheets."""

from typing import Final

_PALETTE = {
    "white": {
        "window": "#f0f0f0",
        "pane": "#ffffff",
        "widget": "#ffffff",
        "input": "#ffffff",
        "text": "#1a1a1e",
        "border": "#c4c4c4",
        "tab": "#e8e8e8",
        "tab_selected": "#ffffff",
        "tab_hover": "#f5f5f5",
        "status": "#e8e8e8",
        "muted": "#666666",
    },
    "gray": {
        "window": "#b8b8b8",
        "pane": "#c4c4c4",
        "widget": "#c4c4c4",
        "input": "#e0e0e0",
        "text": "#1e1e1e",
        "border": "#8a8a8a",
        "tab": "#b0b0b0",
        "tab_selected": "#9a9a9a",
        "tab_hover": "#a8a8a8",
        "status": "#a8a8a8",
        "muted": "#555555",
    },
    "dark": {
        "window": "#2b2b2b",
        "pane": "#3a3a3a",
        "widget": "#3a3a3a",
        "input": "#4a4a4a",
        "text": "#ffffff",
        "border": "#555555",
        "tab": "#4a4a4a",
        "tab_selected": "#5a5a5a",
        "tab_hover": "#505050",
        "status": "#2b2b2b",
        "muted": "#aaaaaa",
    },
}


def stylesheet(name: str) -> str:
    colors = _PALETTE[name]
    return f"""QMainWindow {{
    background-color: {colors["window"]};
    color: {colors["text"]};
}}
QTabWidget::pane {{
    border: 1px solid {colors["border"]};
    background-color: {colors["pane"]};
}}
QTabBar::tab {{
    background-color: {colors["tab"]};
    color: {colors["text"]};
    padding: 4px 10px;
}}
QTabBar::tab:selected {{ background-color: {colors["tab_selected"]}; }}
QTabBar::tab:hover {{ background-color: {colors["tab_hover"]}; }}
QWidget {{ background-color: {colors["widget"]}; color: {colors["text"]}; }}
QLabel {{ color: {colors["text"]}; }}
QLineEdit, QTextEdit, QComboBox, QSpinBox {{
    background-color: {colors["input"]};
    color: {colors["text"]};
    border: 1px solid {colors["border"]};
    border-radius: 2px;
    padding: 2px 4px;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 1px solid #0078d4;
}}
QPushButton {{
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    border-radius: 2px;
    padding: 4px 8px;
}}
QPushButton:hover {{ background-color: #106ebe; }}
QPushButton:pressed {{ background-color: #005a9e; }}
QStatusBar {{ background-color: {colors["status"]}; color: {colors["text"]}; }}
QGroupBox {{
    border: 1px solid {colors["border"]};
    border-radius: 3px;
    margin-top: 6px;
    padding: 6px 4px 4px 4px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
}}
QProgressBar {{
    border: 1px solid {colors["border"]};
    border-radius: 2px;
    text-align: center;
    background-color: {colors["input"]};
    max-height: 18px;
    color: {colors["text"]};
}}
QProgressBar::chunk {{ background-color: #0078d4; border-radius: 2px; }}
QSlider::groove:horizontal {{ height: 4px; background: {colors["input"]}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 12px; margin: -4px 0; background: #0078d4; border-radius: 6px; }}
QLabel#label_6 {{ color: {colors["muted"]}; font-style: italic; }}"""


THEMES: Final = frozenset(_PALETTE)
DEFAULT_THEME: Final = "gray"
