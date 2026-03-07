import sys
from pathlib import Path

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow, QRadioButton, QTextEdit

from themes import DEFAULT_THEME, stylesheet

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


def _load_window() -> QMainWindow:
    loader = QUiLoader()
    ui_file = QFile(str(UI_PATH))
    if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
        raise RuntimeError(f"Cannot open {UI_PATH}")
    window = loader.load(ui_file)
    ui_file.close()
    if window is None:
        raise RuntimeError(f"Cannot load {UI_PATH}")
    return window


def _apply_theme(window: QMainWindow, name: str) -> None:
    window.setStyleSheet(stylesheet(name))


def _wire_themes(window: QMainWindow) -> None:
    for theme, object_name in _THEME_RADIOS.items():
        button = window.findChild(QRadioButton, object_name)
        if button is None:
            raise RuntimeError(f"Missing theme control: {object_name}")
        button.toggled.connect(
            lambda checked, theme_name=theme: checked and _apply_theme(window, theme_name)
        )


def _load_reference(window: QMainWindow) -> None:
    for widget_name, filename in _REFERENCE_VIEWS.items():
        editor = window.findChild(QTextEdit, widget_name)
        if editor is None:
            raise RuntimeError(f"Missing reference view: {widget_name}")
        path = REFERENCE_DIR / filename
        editor.setHtml(path.read_text(encoding="utf-8"))


def main() -> None:
    app = QApplication(sys.argv)
    window = _load_window()
    _wire_themes(window)
    _load_reference(window)
    _apply_theme(window, DEFAULT_THEME)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
