import sys
from functools import partial
from pathlib import Path

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTextEdit,
)
from config import AppConfig, load_config, save_config
from themes import DEFAULT_THEME, stylesheet
from words import DEFAULT_INCLUDE, format_word_row, get_random_words

PROJECT_ROOT = Path(__file__).resolve().parent.parent
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

_INCLUDE_CHECKBOXES = {
    "article": "checkBox",
    "word": "checkBox_2",
    "meaning": "checkBox_3",
    "pronunciation": "checkBox_4",
    "example": "checkBox_5",
    "translation": "checkBox_6",
    "plural": "checkBox_7",
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


def _apply_theme(window: QMainWindow, name: str) -> None:
    window.setStyleSheet(stylesheet(name))


def _select_theme(window: QMainWindow, name: str) -> None:
    object_name = _THEME_RADIOS.get(name, _THEME_RADIOS[DEFAULT_THEME])
    button = window.findChild(QRadioButton, object_name)
    if button is None:
        raise RuntimeError(f"Missing theme control: {object_name}")
    button.setChecked(True)


def _on_theme_selected(window: QMainWindow, config: AppConfig, theme_name: str) -> None:
    _apply_theme(window, theme_name)
    config.theme = theme_name
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


def _language_key_from_combo(language_text: str) -> str:
    return language_text.strip().lower()


def _include_flags(window: QMainWindow) -> dict[str, bool]:
    flags = dict(DEFAULT_INCLUDE)
    for field_name, object_name in _INCLUDE_CHECKBOXES.items():
        checkbox = window.findChild(QCheckBox, object_name)
        if checkbox is None:
            raise RuntimeError(f"Missing include control: {object_name}")
        flags[field_name] = checkbox.isChecked()
    return flags


def _apply_default_include(window: QMainWindow) -> None:
    for field_name, object_name in _INCLUDE_CHECKBOXES.items():
        checkbox = window.findChild(QCheckBox, object_name)
        if checkbox is None:
            raise RuntimeError(f"Missing include control: {object_name}")
        checkbox.setChecked(DEFAULT_INCLUDE[field_name])


def _on_get_words(window: QMainWindow) -> None:
    count_input = window.findChild(QSpinBox, "spinBox")
    language_combo = window.findChild(QComboBox, "comboBox")
    results = window.findChild(QTextEdit, "textEdit_3")
    if count_input is None or language_combo is None or results is None:
        raise RuntimeError("Missing Get Word(s) controls")

    count = count_input.value()
    language_key = _language_key_from_combo(language_combo.currentText())
    include = _include_flags(window)
    try:
        words = get_random_words(language_key, count)
    except (ValueError, FileNotFoundError, OSError) as error:
        results.setPlainText(str(error))
        return

    lines = [format_word_row(row, include) for row in words]
    results.setPlainText("\n".join(lines))


def _wire_get_words(window: QMainWindow) -> None:
    button = window.findChild(QPushButton, "pushButton")
    if button is None:
        raise RuntimeError("Missing Get Word(s) button: pushButton")
    handler = partial(_on_get_words, window)
    button.clicked.connect(handler)


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


def main() -> None:
    application = QApplication(sys.argv)
    config = load_config()
    window = _load_window()
    _apply_window_config(window, config)
    _wire_themes(window, config)
    _wire_get_words(window)
    _apply_default_include(window)
    _load_reference(window)
    _select_theme(window, config.theme)
    quit_handler = partial(_persist_window_config, window, config)
    application.aboutToQuit.connect(quit_handler)
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()
