from functools import partial

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
)

from config import AppConfig, save_config
from browser_config import BrowserConfig
from browser_support import find_browser_path
from ui_browser import (
    install_chromium_with_prompt,
    remove_chromium_with_prompt,
)


def _checkbox(window: QMainWindow, object_name: str) -> QCheckBox:
    widget = window.findChild(QCheckBox, object_name)
    if widget is None:
        raise RuntimeError(f"Missing settings control: {object_name}")
    return widget


def _spin(window: QMainWindow, object_name: str) -> QSpinBox:
    widget = window.findChild(QSpinBox, object_name)
    if widget is None:
        raise RuntimeError(f"Missing settings control: {object_name}")
    return widget


def _double_spin(window: QMainWindow, object_name: str) -> QDoubleSpinBox:
    widget = window.findChild(QDoubleSpinBox, object_name)
    if widget is None:
        raise RuntimeError(f"Missing settings control: {object_name}")
    return widget


def _line(window: QMainWindow, object_name: str) -> QLineEdit:
    widget = window.findChild(QLineEdit, object_name)
    if widget is None:
        raise RuntimeError(f"Missing settings control: {object_name}")
    return widget


def _label(window: QMainWindow, object_name: str) -> QLabel:
    widget = window.findChild(QLabel, object_name)
    if widget is None:
        raise RuntimeError(f"Missing settings control: {object_name}")
    return widget


def refresh_browser_status(window: QMainWindow) -> None:
    path = find_browser_path()
    status = _label(window, "label_settings_browser_status")
    if path is None:
        status.setText("Browser: not found")
    else:
        status.setText(f"Browser: {path}")


def apply_settings_to_form(window: QMainWindow, config: AppConfig) -> None:
    browser = config.browser
    _checkbox(window, "checkBox_browser_headless").setChecked(browser.headless)
    _checkbox(window, "checkBox_browser_sandbox").setChecked(browser.sandbox)
    _spin(window, "spinBox_browser_wait_seconds").setValue(int(browser.wait_seconds))
    _double_spin(window, "doubleSpinBox_browser_extra_timeout").setValue(
        browser.extra_timeout_seconds
    )
    _double_spin(window, "doubleSpinBox_browser_connect_timeout").setValue(
        browser.connect_timeout_seconds
    )
    _spin(window, "spinBox_browser_connect_tries").setValue(browser.connect_tries)
    _double_spin(window, "doubleSpinBox_fetch_timeout").setValue(
        browser.fetch_timeout_seconds
    )
    _double_spin(window, "doubleSpinBox_probe_timeout").setValue(
        browser.probe_timeout_seconds
    )
    _line(window, "lineEdit_browser_path").setText(browser.browser_path)
    refresh_browser_status(window)


def _read_browser_from_form(window: QMainWindow) -> BrowserConfig:
    return BrowserConfig(
        headless=_checkbox(window, "checkBox_browser_headless").isChecked(),
        sandbox=_checkbox(window, "checkBox_browser_sandbox").isChecked(),
        wait_seconds=float(_spin(window, "spinBox_browser_wait_seconds").value()),
        extra_timeout_seconds=_double_spin(
            window, "doubleSpinBox_browser_extra_timeout"
        ).value(),
        connect_timeout_seconds=_double_spin(
            window, "doubleSpinBox_browser_connect_timeout"
        ).value(),
        connect_tries=_spin(window, "spinBox_browser_connect_tries").value(),
        browser_path=_line(window, "lineEdit_browser_path").text().strip(),
        fetch_timeout_seconds=_double_spin(
            window, "doubleSpinBox_fetch_timeout"
        ).value(),
        probe_timeout_seconds=_double_spin(
            window, "doubleSpinBox_probe_timeout"
        ).value(),
    )


def _save_settings(window: QMainWindow, config: AppConfig) -> None:
    config.browser = _read_browser_from_form(window)
    save_config(config)
    refresh_browser_status(window)


def _on_install_chromium(window: QMainWindow) -> None:
    install_chromium_with_prompt(window)
    refresh_browser_status(window)


def _on_remove_chromium(window: QMainWindow) -> None:
    remove_chromium_with_prompt(window)
    refresh_browser_status(window)


def wire_settings(window: QMainWindow, config: AppConfig) -> None:
    apply_settings_to_form(window, config)
    save_button = window.findChild(QPushButton, "pushButton_settings_save")
    install_button = window.findChild(QPushButton, "pushButton_settings_install_chromium")
    remove_button = window.findChild(QPushButton, "pushButton_settings_remove_chromium")
    if save_button is None or install_button is None or remove_button is None:
        raise RuntimeError("Missing Settings controls")
    save_button.clicked.connect(partial(_save_settings, window, config))
    install_button.clicked.connect(partial(_on_install_chromium, window))
    remove_button.clicked.connect(partial(_on_remove_chromium, window))
