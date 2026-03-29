_PALETTE = {
    "white": {
        "window": "#f4f5f3",
        "pane": "#ffffff",
        "widget": "#ffffff",
        "input": "#ffffff",
        "text": "#1c1f1e",
        "border": "#d0d4d1",
        "tab": "#e8ebe8",
        "tab_selected": "#ffffff",
        "tab_hover": "#f0f2f0",
        "status": "#e8ebe8",
        "muted": "#5f6763",
        "accent": "#1f6f6a",
        "accent_hover": "#185853",
        "accent_pressed": "#124540",
        "brand": "#143d3a",
    },
    "gray": {
        "window": "#c8cbc8",
        "pane": "#d6d9d6",
        "widget": "#d6d9d6",
        "input": "#ecefec",
        "text": "#1c1f1e",
        "border": "#9aa19c",
        "tab": "#b8bcb8",
        "tab_selected": "#d6d9d6",
        "tab_hover": "#c4c8c4",
        "status": "#b8bcb8",
        "muted": "#4f5652",
        "accent": "#1f6f6a",
        "accent_hover": "#185853",
        "accent_pressed": "#124540",
        "brand": "#143d3a",
    },
    "dark": {
        "window": "#1e2322",
        "pane": "#2a302e",
        "widget": "#2a302e",
        "input": "#353c3a",
        "text": "#eef2f0",
        "border": "#4a524f",
        "tab": "#353c3a",
        "tab_selected": "#2a302e",
        "tab_hover": "#3c4441",
        "status": "#1e2322",
        "muted": "#9aa5a0",
        "accent": "#3d9b94",
        "accent_hover": "#4aada5",
        "accent_pressed": "#2f7f79",
        "brand": "#d7ebe8",
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
    border-radius: 4px;
    top: -1px;
}}
QTabBar::tab {{
    background-color: {colors["tab"]};
    color: {colors["text"]};
    padding: 7px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}
QTabBar::tab:selected {{
    background-color: {colors["tab_selected"]};
    font-weight: 600;
}}
QTabBar::tab:hover {{ background-color: {colors["tab_hover"]}; }}
QWidget {{ background-color: {colors["widget"]}; color: {colors["text"]}; }}
QLabel {{ color: {colors["text"]}; }}
QLabel#label_brand {{
    color: {colors["brand"]};
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QLabel#label_tagline,
QLabel#label_vocab_hint,
QLabel#label_6 {{
    color: {colors["muted"]};
}}
QLineEdit, QTextEdit, QComboBox, QSpinBox {{
    background-color: {colors["input"]};
    color: {colors["text"]};
    border: 1px solid {colors["border"]};
    border-radius: 3px;
    padding: 4px 6px;
    min-height: 22px;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 1px solid {colors["accent"]};
}}
QTextEdit#textEdit_3 {{
    font-size: 14px;
    padding: 8px;
}}
QPushButton {{
    background-color: {colors["accent"]};
    color: #ffffff;
    border: none;
    border-radius: 3px;
    padding: 6px 12px;
    min-height: 24px;
}}
QPushButton:hover {{ background-color: {colors["accent_hover"]}; }}
QPushButton:pressed {{ background-color: {colors["accent_pressed"]}; }}
QPushButton:disabled {{
    background-color: {colors["border"]};
    color: {colors["muted"]};
}}
QStatusBar {{ background-color: {colors["status"]}; color: {colors["text"]}; }}
QGroupBox {{
    border: 1px solid {colors["border"]};
    border-radius: 4px;
    margin-top: 10px;
    padding: 10px 8px 8px 8px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
}}
QGroupBox[flat="true"] {{
    border: none;
    margin-top: 8px;
    padding: 8px 0 0 0;
    font-weight: 600;
}}
QProgressBar {{
    border: 1px solid {colors["border"]};
    border-radius: 3px;
    text-align: center;
    background-color: {colors["input"]};
    max-height: 16px;
    color: {colors["text"]};
}}
QProgressBar::chunk {{ background-color: {colors["accent"]}; border-radius: 2px; }}
QSlider::groove:horizontal {{
    height: 4px;
    background: {colors["input"]};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 12px;
    margin: -4px 0;
    background: {colors["accent"]};
    border-radius: 6px;
}}
QCheckBox, QRadioButton {{
    spacing: 6px;
    padding: 2px 0;
}}"""


THEMES = frozenset(_PALETTE)
DEFAULT_THEME = "white"
