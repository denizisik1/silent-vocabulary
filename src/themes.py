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
        "indicator": "#6a706c",
        "faint": "#a8ada9",
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
        "window": "#a8a8a8",
        "pane": "#b6b6b6",
        "widget": "#b6b6b6",
        "input": "#c2c2c2",
        "text": "#1a1a1a",
        "border": "#808080",
        "tab": "#9c9c9c",
        "tab_selected": "#b6b6b6",
        "tab_hover": "#aaaaaa",
        "status": "#9c9c9c",
        "muted": "#4a4a4a",
        "indicator": "#555555",
        "faint": "#7a7a7a",
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
        "window": "#1e1e1e",
        "pane": "#2a2a2a",
        "widget": "#2a2a2a",
        "input": "#383838",
        "text": "#eeeeee",
        "border": "#6e6e6e",
        "tab": "#383838",
        "tab_selected": "#2a2a2a",
        "tab_hover": "#424242",
        "status": "#1e1e1e",
        "muted": "#9a9a9a",
        "indicator": "#b8b8b8",
        "faint": "#555555",
        "accent": "#5b8fd4",
        "accent_hover": "#6ba0e0",
        "accent_pressed": "#4a7bc0",
        "brand": "#c8daf0",
        "running": "#d4a017",
        "running_text": "#1e1e1e",
        "ok": "#3d9b6a",
        "ok_text": "#1e1e1e",
        "error": "#c45c5c",
        "error_text": "#1e1e1e",
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
    input_min = scale_px(24, zoom)
    button_min = scale_px(28, zoom)
    header_control_min = scale_px(28, zoom)
    theme_button_pad = scale_px(4, zoom)
    spin_step_width = scale_px(28, zoom)
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
QLabel#label_vocab_hint,
QLabel#label_6,
QLabel#label_tray_unavailable {{
    color: {colors["muted"]};
    font-size: {hint_size}px;
    font-style: italic;
}}
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {colors["input"]};
    color: {colors["text"]};
    border: 1px solid {colors["border"]};
    border-radius: 3px;
    padding: 4px 6px;
    min-height: {input_min}px;
    font-size: {body_size}px;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {colors["accent"]};
}}
QTextEdit#textEdit_3,
QTextEdit#textEdit_retrieve_results,
QTextEdit#textEdit_vocab_retrieve_results {{
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
QPushButton#spinStepButton {{
    min-width: {spin_step_width}px;
    max-width: {spin_step_width}px;
    min-height: {button_min}px;
    padding: 6px 0;
}}
QPushButton#pushButton_zoom_out,
QPushButton#pushButton_zoom_in {{
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 4px 0;
    font-size: 13px;
}}
QSpinBox#spinBox {{
    min-height: {button_min}px;
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
QCheckBox, QRadioButton {{
    spacing: 6px;
    padding: 2px 0;
    font-size: {body_size}px;
}}
QCheckBox:disabled, QRadioButton:disabled {{
    color: {colors["muted"]};
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: {scale_px(14, zoom)}px;
    height: {scale_px(14, zoom)}px;
    border: 1px solid {colors["indicator"]};
    background-color: {colors["input"]};
}}
QCheckBox::indicator {{
    border-radius: 3px;
}}
QRadioButton::indicator {{
    border-radius: {scale_px(7, zoom)}px;
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {colors["accent"]};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {colors["accent"]};
    border-color: {colors["accent"]};
}}
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {{
    border-color: {colors["border"]};
    background-color: {colors["tab"]};
}}
QCheckBox::indicator:checked:disabled, QRadioButton::indicator:checked:disabled {{
    background-color: {colors["border"]};
    border-color: {colors["border"]};
}}
QComboBox {{
    padding-right: {scale_px(22, zoom)}px;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: {scale_px(20, zoom)}px;
    border: none;
    background: transparent;
}}
QComboBox QAbstractItemView {{
    background-color: {colors["input"]};
    color: {colors["text"]};
    border: 1px solid {colors["border"]};
    selection-background-color: {colors["accent"]};
    selection-color: #ffffff;
    outline: 0;
}}
QComboBox#comboBox {{
    min-height: {header_control_min}px;
    min-width: {scale_px(148, zoom)}px;
}}
QComboBox#comboBox QAbstractItemView::item {{
    min-height: {scale_px(26, zoom)}px;
    padding: 3px 8px;
    color: {colors["text"]};
}}
QComboBox#comboBox QAbstractItemView::item:disabled {{
    color: {colors["faint"]};
    background-color: {colors["input"]};
}}
QComboBox#comboBox QAbstractItemView::item:selected:enabled {{
    background-color: {colors["accent"]};
    color: #ffffff;
}}
QToolButton#toolButton_theme {{
    background-color: transparent;
    border: none;
    padding: {theme_button_pad}px;
    min-height: {header_control_min}px;
    min-width: {header_control_min}px;
}}
QToolButton#toolButton_theme:hover {{
    background-color: {colors["tab_hover"]};
    border-radius: 3px;
}}"""


THEMES = frozenset(_PALETTE)
DEFAULT_THEME = os.environ.get("VIPA_DEFAULT_THEME", "white")


def theme_color(name: str, key: str) -> str:
    return _PALETTE[name][key]
