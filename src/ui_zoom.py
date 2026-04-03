from functools import partial

from PySide6.QtWidgets import QMainWindow, QSlider
from config import AppConfig, save_config
from themes import stylesheet
from zoom import MAX_ZOOM_PERCENT, MIN_ZOOM_PERCENT, clamp_zoom_percent


def apply_appearance(window: QMainWindow, config: AppConfig) -> None:
    window.setStyleSheet(stylesheet(config.theme, config.zoom_percent))


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
    slider.setToolTip("Zoom UI text size")
    handler = partial(_on_zoom_changed, window, config)
    slider.valueChanged.connect(handler)
