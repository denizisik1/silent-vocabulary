from functools import partial

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QToolButton,
    QWidget,
)
from config import AppConfig, save_config
from theme_icons import THEME_BUTTON, next_theme, theme_icon, theme_tooltip
from themes import stylesheet, theme_color
from ui_words import style_language_combo
from zoom import (
    MAX_ZOOM_PERCENT,
    MIN_ZOOM_PERCENT,
    ZOOM_STEP_PERCENT,
    clamp_zoom_percent,
    scale_px,
)

_HEADER_WIDGET = "headerWidget"
_THEME_ICON_BASE = 22
_ZOOM_OUT = "pushButton_zoom_out"
_ZOOM_IN = "pushButton_zoom_in"
_MONO_ZOOM_OUT = "pushButton_mono_zoom_out"
_MONO_ZOOM_IN = "pushButton_mono_zoom_in"


def apply_theme_button(window: QMainWindow, config: AppConfig) -> None:
    button = window.findChild(QToolButton, THEME_BUTTON)
    if button is None:
        raise RuntimeError(f"Missing theme control: {THEME_BUTTON}")
    icon_size = scale_px(_THEME_ICON_BASE, config.zoom_percent)
    button.setText("")
    button.setIcon(theme_icon(config.theme, icon_size))
    button.setIconSize(QSize(icon_size, icon_size))
    button.setToolTip(theme_tooltip(config.theme))


def _apply_pair_enabled(
    window: QMainWindow,
    zoom_out_name: str,
    zoom_in_name: str,
    zoom_percent: int,
) -> None:
    zoom = clamp_zoom_percent(zoom_percent)
    zoom_out = window.findChild(QPushButton, zoom_out_name)
    zoom_in = window.findChild(QPushButton, zoom_in_name)
    if zoom_out is None or zoom_in is None:
        raise RuntimeError(f"Missing zoom controls: {zoom_out_name}, {zoom_in_name}")
    zoom_out.setEnabled(zoom > MIN_ZOOM_PERCENT)
    zoom_in.setEnabled(zoom < MAX_ZOOM_PERCENT)


def apply_zoom_controls(window: QMainWindow, zoom_percent: int) -> None:
    _apply_pair_enabled(window, _ZOOM_OUT, _ZOOM_IN, zoom_percent)


def apply_mono_zoom_controls(window: QMainWindow, mono_zoom_percent: int) -> None:
    _apply_pair_enabled(window, _MONO_ZOOM_OUT, _MONO_ZOOM_IN, mono_zoom_percent)


def apply_header_controls(window: QMainWindow, config: AppConfig) -> None:
    header = window.findChild(QWidget, _HEADER_WIDGET)
    if header is not None:
        layout = header.layout()
        if isinstance(layout, QHBoxLayout):
            layout.setSpacing(scale_px(18, config.zoom_percent))
    apply_zoom_controls(window, config.zoom_percent)
    apply_mono_zoom_controls(window, config.mono_zoom_percent)


def apply_appearance(window: QMainWindow, config: AppConfig) -> None:
    window.setStyleSheet(
        stylesheet(config.theme, config.zoom_percent, config.mono_zoom_percent)
    )
    apply_header_controls(window, config)
    apply_theme_button(window, config)
    style_language_combo(window, theme_color(config.theme, "faint"))


def _on_theme_clicked(window: QMainWindow, config: AppConfig) -> None:
    config.theme = next_theme(config.theme)
    apply_appearance(window, config)
    save_config(config)


def wire_theme(window: QMainWindow, config: AppConfig) -> None:
    button = window.findChild(QToolButton, THEME_BUTTON)
    if button is None:
        raise RuntimeError(f"Missing theme control: {THEME_BUTTON}")
    button.setAutoRaise(True)
    button.clicked.connect(partial(_on_theme_clicked, window, config))
    apply_theme_button(window, config)


def _set_zoom(window: QMainWindow, config: AppConfig, zoom_percent: int) -> None:
    config.zoom_percent = clamp_zoom_percent(zoom_percent)
    apply_appearance(window, config)
    save_config(config)


def _set_mono_zoom(window: QMainWindow, config: AppConfig, mono_zoom_percent: int) -> None:
    config.mono_zoom_percent = clamp_zoom_percent(mono_zoom_percent)
    apply_appearance(window, config)
    save_config(config)


def _on_zoom_out(window: QMainWindow, config: AppConfig) -> None:
    _set_zoom(window, config, config.zoom_percent - ZOOM_STEP_PERCENT)


def _on_zoom_in(window: QMainWindow, config: AppConfig) -> None:
    _set_zoom(window, config, config.zoom_percent + ZOOM_STEP_PERCENT)


def _on_mono_zoom_out(window: QMainWindow, config: AppConfig) -> None:
    _set_mono_zoom(window, config, config.mono_zoom_percent - ZOOM_STEP_PERCENT)


def _on_mono_zoom_in(window: QMainWindow, config: AppConfig) -> None:
    _set_mono_zoom(window, config, config.mono_zoom_percent + ZOOM_STEP_PERCENT)


def _wire_zoom_pair(
    window: QMainWindow,
    zoom_out_name: str,
    zoom_in_name: str,
    on_out,
    on_in,
) -> tuple[QPushButton, QPushButton]:
    zoom_out = window.findChild(QPushButton, zoom_out_name)
    zoom_in = window.findChild(QPushButton, zoom_in_name)
    if zoom_out is None or zoom_in is None:
        raise RuntimeError(f"Missing zoom controls: {zoom_out_name}, {zoom_in_name}")

    for button in (zoom_out, zoom_in):
        button.setAutoDefault(False)
        button.setDefault(False)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    zoom_out.clicked.connect(on_out)
    zoom_in.clicked.connect(on_in)
    return zoom_out, zoom_in


def wire_zoom(window: QMainWindow, config: AppConfig) -> None:
    _wire_zoom_pair(
        window,
        _ZOOM_OUT,
        _ZOOM_IN,
        partial(_on_zoom_out, window, config),
        partial(_on_zoom_in, window, config),
    )
    _wire_zoom_pair(
        window,
        _MONO_ZOOM_OUT,
        _MONO_ZOOM_IN,
        partial(_on_mono_zoom_out, window, config),
        partial(_on_mono_zoom_in, window, config),
    )
    apply_zoom_controls(window, config.zoom_percent)
    apply_mono_zoom_controls(window, config.mono_zoom_percent)
