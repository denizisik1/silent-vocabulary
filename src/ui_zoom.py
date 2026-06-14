from functools import partial

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QSlider, QToolButton, QWidget
from config import AppConfig, save_config
from theme_icons import THEME_BUTTON, next_theme, theme_icon, theme_tooltip
from themes import stylesheet
from zoom import MAX_ZOOM_PERCENT, MIN_ZOOM_PERCENT, clamp_zoom_percent, scale_px

_HEADER_WIDGET = "headerWidget"
_THEME_ICON_BASE = 22
_SLIDER_HANDLE_BASE = 14


def apply_theme_button(window: QMainWindow, config: AppConfig) -> None:
    button = window.findChild(QToolButton, THEME_BUTTON)
    if button is None:
        raise RuntimeError(f"Missing theme control: {THEME_BUTTON}")
    icon_size = scale_px(_THEME_ICON_BASE, config.zoom_percent)
    button.setText("")
    button.setIcon(theme_icon(config.theme, icon_size))
    button.setIconSize(QSize(icon_size, icon_size))
    button.setToolTip(theme_tooltip(config.theme))


def apply_header_controls(window: QMainWindow, zoom_percent: int) -> None:
    header = window.findChild(QWidget, _HEADER_WIDGET)
    if header is not None:
        layout = header.layout()
        if isinstance(layout, QHBoxLayout):
            layout.setSpacing(scale_px(18, zoom_percent))
    slider = window.findChild(QSlider, "horizontalSlider")
    if slider is not None:
        handle = scale_px(_SLIDER_HANDLE_BASE, zoom_percent)
        slider.setMinimumHeight(handle + scale_px(4, zoom_percent))


def apply_appearance(window: QMainWindow, config: AppConfig) -> None:
    window.setStyleSheet(stylesheet(config.theme, config.zoom_percent))
    apply_header_controls(window, config.zoom_percent)
    apply_theme_button(window, config)


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


def _zoom_slider(window: QMainWindow) -> QSlider:
    slider = window.findChild(QSlider, "horizontalSlider")
    if slider is None:
        raise RuntimeError("Missing zoom control: horizontalSlider")
    return slider


def _on_zoom_changed(window: QMainWindow, config: AppConfig, value: int) -> None:
    config.zoom_percent = clamp_zoom_percent(value)
    apply_appearance(window, config)
    save_config(config)


def wire_zoom(window: QMainWindow, config: AppConfig) -> None:
    slider = _zoom_slider(window)
    slider.setMinimum(MIN_ZOOM_PERCENT)
    slider.setMaximum(MAX_ZOOM_PERCENT)
    slider.setSingleStep(5)
    slider.setPageStep(10)
    slider.setValue(clamp_zoom_percent(config.zoom_percent))
    slider.setToolTip("Zoom")
    handler = partial(_on_zoom_changed, window, config)
    slider.valueChanged.connect(handler)
