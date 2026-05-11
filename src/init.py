import sys
from functools import partial
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from universal.env_check import check_env_files  # noqa: E402

check_env_files(PROJECT_ROOT)
load_dotenv(PROJECT_ROOT / ".env")

from PySide6.QtCore import QFile, QIODevice  # noqa: E402
from PySide6.QtUiTools import QUiLoader  # noqa: E402
from PySide6.QtWidgets import QApplication, QMainWindow, QRadioButton, QTextEdit  # noqa: E402
from config import AppConfig, load_config, save_config  # noqa: E402
from themes import DEFAULT_THEME  # noqa: E402
from ui_daemon import stop_daemon, wire_daemon  # noqa: E402
from ui_export import wire_export_overlay  # noqa: E402
from ui_protect import apply_protect_setting, wire_protect_vocabulary  # noqa: E402
from ui_tray import wire_tray  # noqa: E402
from ui_retrieve import wire_retrieve  # noqa: E402
from ui_words import (  # noqa: E402
    apply_session_config,
    wire_add_remove_word,
    wire_get_words,
    wire_session_config,
)
from ui_zoom import apply_appearance, wire_zoom  # noqa: E402

UI_PATH = PROJECT_ROOT / "ui" / "main_window.ui"
REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"

_REFERENCE_VIEWS = {
    "textEdit": "consonants.html",
    "textEdit_2": "vowels.html",
}

_THEME_RADIOS = {
    "white": "radioButton_themeWhite",
    "gray": "radioButton_themeGray",
    "dark": "radioButton_themeDark",
}


def _load_window() -> QMainWindow:
    loader = QUiLoader()
    ui_file = QFile(str(UI_PATH))
    if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
        raise RuntimeError(f"Cannot open {UI_PATH}")
    window = loader.load(ui_file)
    ui_file.close()
    if window is None:
        raise RuntimeError(f"Cannot load {UI_PATH}")
    if not isinstance(window, QMainWindow):
        raise RuntimeError(f"Loaded UI is not a main window: {UI_PATH}")
    return window


def _select_theme(window: QMainWindow, name: str) -> None:
    object_name = _THEME_RADIOS.get(name, _THEME_RADIOS[DEFAULT_THEME])
    button = window.findChild(QRadioButton, object_name)
    if button is None:
        raise RuntimeError(f"Missing theme control: {object_name}")
    button.setChecked(True)


def _on_theme_selected(window: QMainWindow, config: AppConfig, theme_name: str) -> None:
    config.theme = theme_name
    apply_appearance(window, config)
    save_config(config)


def _handle_theme_toggle(
    window: QMainWindow,
    config: AppConfig,
    theme_name: str,
    checked: bool,
) -> None:
    if not checked:
        return
    _on_theme_selected(window, config, theme_name)


def _wire_themes(window: QMainWindow, config: AppConfig) -> None:
    for theme_name, object_name in _THEME_RADIOS.items():
        button = window.findChild(QRadioButton, object_name)
        if button is None:
            raise RuntimeError(f"Missing theme control: {object_name}")
        handler = partial(_handle_theme_toggle, window, config, theme_name)
        button.toggled.connect(handler)


def _load_reference(window: QMainWindow) -> None:
    for widget_name, filename in _REFERENCE_VIEWS.items():
        editor = window.findChild(QTextEdit, widget_name)
        if editor is None:
            raise RuntimeError(f"Missing reference view: {widget_name}")
        path = REFERENCE_DIR / filename
        editor.setHtml(path.read_text(encoding="utf-8"))


def _apply_window_config(window: QMainWindow, config: AppConfig) -> None:
    window.resize(config.window.width, config.window.height)


def _persist_window_config(window: QMainWindow, config: AppConfig) -> None:
    config.window.width = window.width()
    config.window.height = window.height()
    save_config(config)


def _on_about_to_quit(
    window: QMainWindow,
    application: QApplication,
    config: AppConfig,
) -> None:
    stop_daemon(window, application)
    _persist_window_config(window, config)


def main() -> None:
    application = QApplication(sys.argv)
    config = load_config()
    apply_protect_setting(config)
    window = _load_window()
    _apply_window_config(window, config)
    wire_zoom(window, config)
    _wire_themes(window, config)
    wire_get_words(window)
    wire_add_remove_word(window)
    apply_session_config(window, config)
    wire_session_config(window, config)
    wire_tray(window, application, config)
    wire_daemon(window, application, config)
    wire_retrieve(window)
    wire_protect_vocabulary(window, config)
    wire_export_overlay(window)
    _load_reference(window)
    _select_theme(window, config.theme)
    apply_appearance(window, config)
    quit_handler = partial(_on_about_to_quit, window, application, config)
    application.aboutToQuit.connect(quit_handler)
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()
