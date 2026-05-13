import os

from zoom import DEFAULT_ZOOM_PERCENT, clamp_zoom_percent, scale_px

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
        "accent": "#2b5ea7",
        "accent_hover": "#234d8a",
        "accent_pressed": "#1b3c6c",
        "brand": "#1a3a6e",
        "running": "#b8860b",
        "running_text": "#ffffff",
        "ok": "#2e7d4f",
        "ok_text": "#ffffff",
        "error": "#a33b3b",
        "error_text": "#ffffff",
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
        "accent": "#2b5ea7",
        "accent_hover": "#234d8a",
        "accent_pressed": "#1b3c6c",
        "brand": "#1a3a6e",
        "running": "#b8860b",
        "running_text": "#ffffff",
        "ok": "#2e7d4f",
        "ok_text": "#ffffff",
        "error": "#a33b3b",
        "error_text": "#ffffff",
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
        "accent": "#5b8fd4",
        "accent_hover": "#6ba0e0",
        "accent_pressed": "#4a7bc0",
        "brand": "#c8daf0",
        "running": "#d4a017",
        "running_text": "#1e2322",
        "ok": "#3d9b6a",
        "ok_text": "#1e2322",
        "error": "#c45c5c",
        "error_text": "#1e2322",
    },
}


def stylesheet(name: str, zoom_percent: int = DEFAULT_ZOOM_PERCENT) -> str:
    colors = _PALETTE[name]
    zoom = clamp_zoom_percent(zoom_percent)
    brand_size = scale_px(20, zoom)
    body_size = scale_px(13, zoom)
    hint_size = scale_px(11, zoom)
    results_size = scale_px(14, zoom)
    tab_pad_y = scale_px(7, zoom)
    tab_pad_x = scale_px(14, zoom)
    input_min = scale_px(22, zoom)
    button_min = scale_px(24, zoom)
    return f"""QMainWindow {{
    background-color: {colors["window"]};
    color: {colors["text"]};
    font-size: {body_size}px;
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
    padding: {tab_pad_y}px {tab_pad_x}px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size: {body_size}px;
}}
QTabBar::tab:selected {{
    background-color: {colors["tab_selected"]};
    font-weight: 600;
}}
QTabBar::tab:hover {{ background-color: {colors["tab_hover"]}; }}
QWidget {{
    background-color: {colors["widget"]};
    color: {colors["text"]};
    font-size: {body_size}px;
}}
QLabel {{ color: {colors["text"]}; font-size: {body_size}px; }}
QLabel#label_brand {{
    color: {colors["brand"]};
    font-size: {brand_size}px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QLabel#label_tagline,
QLabel#label_vocab_hint,
QLabel#label_6,
QLabel#label_tray_unavailable {{
    color: {colors["muted"]};
    font-size: {hint_size}px;
    font-style: italic;
}}
QLineEdit, QTextEdit, QComboBox, QSpinBox {{
    background-color: {colors["input"]};
    color: {colors["text"]};
    border: 1px solid {colors["border"]};
    border-radius: 3px;
    padding: 4px 6px;
    min-height: {input_min}px;
    font-size: {body_size}px;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 1px solid {colors["accent"]};
}}
QTextEdit#textEdit_3,
QTextEdit#textEdit_retrieve_results {{
    font-size: {results_size}px;
    padding: 8px;
}}
QPushButton {{
    background-color: {colors["accent"]};
    color: #ffffff;
    border: none;
    border-radius: 3px;
    padding: 6px 12px;
    min-height: {button_min}px;
    font-size: {body_size}px;
}}
QPushButton:hover {{ background-color: {colors["accent_hover"]}; }}
QPushButton:pressed {{ background-color: {colors["accent_pressed"]}; }}
QPushButton:disabled {{
    background-color: {colors["border"]};
    color: {colors["muted"]};
}}
QPushButton[retrieveState="running"],
QPushButton[retrieveState="running"]:disabled {{
    background-color: {colors["running"]};
    color: {colors["running_text"]};
}}
QPushButton[retrieveState="ok"],
QPushButton[retrieveState="ok"]:disabled {{
    background-color: {colors["ok"]};
    color: {colors["ok_text"]};
}}
QPushButton[retrieveState="error"],
QPushButton[retrieveState="error"]:disabled {{
    background-color: {colors["error"]};
    color: {colors["error_text"]};
}}
QStatusBar {{ background-color: {colors["status"]}; color: {colors["text"]}; }}
QGroupBox {{
    border: 1px solid {colors["border"]};
    border-radius: 4px;
    margin-top: 10px;
    padding: 10px 8px 8px 8px;
    font-weight: 600;
    font-size: {body_size}px;
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
    font-size: {body_size}px;
}}"""


THEMES = frozenset(_PALETTE)
DEFAULT_THEME = os.environ.get("VIPA_DEFAULT_THEME", "white")
