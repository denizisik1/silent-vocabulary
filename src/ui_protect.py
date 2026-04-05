from functools import partial

from PySide6.QtWidgets import QCheckBox, QMainWindow, QStatusBar
from config import AppConfig, save_config
from vocabulary_protect import apply_base_vocabulary_protection

_CHECKBOX_NAME = "checkBox_protect_base_vocabulary"


def _status_bar(window: QMainWindow) -> QStatusBar | None:
    return window.findChild(QStatusBar, "statusbar")


def _set_status(window: QMainWindow, message: str) -> None:
    status = _status_bar(window)
    if status is not None:
        status.showMessage(message)


def apply_protect_setting(config: AppConfig, window: QMainWindow | None = None) -> None:
    try:
        changed = apply_base_vocabulary_protection(config.protect_base_vocabulary)
    except OSError as error:
        if window is not None:
            _set_status(window, f"Vocabulary protect failed: {error}")
        return

    if window is None:
        return
    if config.protect_base_vocabulary:
        _set_status(window, f"Base vocabulary read-only ({changed} updated)")
    else:
        _set_status(window, f"Base vocabulary writable ({changed} updated)")


def _on_protect_toggled(window: QMainWindow, config: AppConfig, checked: bool) -> None:
    config.protect_base_vocabulary = checked
    save_config(config)
    apply_protect_setting(config, window)


def wire_protect_vocabulary(window: QMainWindow, config: AppConfig) -> None:
    checkbox = window.findChild(QCheckBox, _CHECKBOX_NAME)
    if checkbox is None:
        raise RuntimeError(f"Missing protect control: {_CHECKBOX_NAME}")

    checkbox.blockSignals(True)
    checkbox.setChecked(config.protect_base_vocabulary)
    checkbox.blockSignals(False)
    handler = partial(_on_protect_toggled, window, config)
    checkbox.toggled.connect(handler)
