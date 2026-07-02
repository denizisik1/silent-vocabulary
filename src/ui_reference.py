from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QMainWindow, QPushButton, QTextEdit

from config import AppConfig, save_config
from zoom import (
    MAX_ZOOM_PERCENT,
    MIN_ZOOM_PERCENT,
    ZOOM_STEP_PERCENT,
    clamp_zoom_percent,
)

REFERENCE_DIR = Path(__file__).resolve().parent.parent / "data" / "reference"
_REFERENCE_VIEWS = {
    "textEdit": "consonants.html",
    "textEdit_2": "vowels.html",
}
_ZOOM_OUT = "pushButton_reference_zoom_out"
_ZOOM_IN = "pushButton_reference_zoom_in"


def scale_document_fonts(editor: QTextEdit, zoom_percent: int) -> None:
    factor = clamp_zoom_percent(zoom_percent) / 100
    if abs(factor - 1.0) < 1e-9:
        return

    document = editor.document()
    cursor = QTextCursor(document)
    block = document.begin()
    while block.isValid():
        iterator = block.begin()
        while not iterator.atEnd():
            fragment = iterator.fragment()
            if fragment.isValid():
                size = fragment.charFormat().fontPointSize()
                if size > 0:
                    format_update = QTextCharFormat()
                    format_update.setFontPointSize(size * factor)
                    cursor.setPosition(fragment.position())
                    cursor.setPosition(
                        fragment.position() + fragment.length(),
                        QTextCursor.MoveMode.KeepAnchor,
                    )
                    cursor.mergeCharFormat(format_update)
            iterator += 1
        block = block.next()


def load_reference(window: QMainWindow, zoom_percent: int = 100) -> None:
    for widget_name, filename in _REFERENCE_VIEWS.items():
        editor = window.findChild(QTextEdit, widget_name)
        if editor is None:
            raise RuntimeError(f"Missing reference view: {widget_name}")
        path = REFERENCE_DIR / filename
        editor.setHtml(path.read_text(encoding="utf-8"))
        scale_document_fonts(editor, zoom_percent)


def apply_reference_zoom_controls(window: QMainWindow, zoom_percent: int) -> None:
    zoom = clamp_zoom_percent(zoom_percent)
    zoom_out = window.findChild(QPushButton, _ZOOM_OUT)
    zoom_in = window.findChild(QPushButton, _ZOOM_IN)
    if zoom_out is None or zoom_in is None:
        raise RuntimeError("Missing reference zoom controls")
    zoom_out.setEnabled(zoom > MIN_ZOOM_PERCENT)
    zoom_in.setEnabled(zoom < MAX_ZOOM_PERCENT)


def apply_reference_zoom(window: QMainWindow, config: AppConfig) -> None:
    load_reference(window, config.reference_zoom_percent)
    apply_reference_zoom_controls(window, config.reference_zoom_percent)


def _set_reference_zoom(window: QMainWindow, config: AppConfig, zoom_percent: int) -> None:
    config.reference_zoom_percent = clamp_zoom_percent(zoom_percent)
    apply_reference_zoom(window, config)
    save_config(config)


def _on_reference_zoom_out(window: QMainWindow, config: AppConfig) -> None:
    _set_reference_zoom(window, config, config.reference_zoom_percent - ZOOM_STEP_PERCENT)


def _on_reference_zoom_in(window: QMainWindow, config: AppConfig) -> None:
    _set_reference_zoom(window, config, config.reference_zoom_percent + ZOOM_STEP_PERCENT)


def wire_reference(window: QMainWindow, config: AppConfig) -> None:
    zoom_out = window.findChild(QPushButton, _ZOOM_OUT)
    zoom_in = window.findChild(QPushButton, _ZOOM_IN)
    if zoom_out is None or zoom_in is None:
        raise RuntimeError("Missing reference zoom controls")

    for button in (zoom_out, zoom_in):
        button.setAutoDefault(False)
        button.setDefault(False)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    zoom_out.clicked.connect(partial(_on_reference_zoom_out, window, config))
    zoom_in.clicked.connect(partial(_on_reference_zoom_in, window, config))
    apply_reference_zoom(window, config)
