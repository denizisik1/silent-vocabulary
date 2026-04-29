from functools import partial
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QTextEdit,
)

from words.export import default_export_filename, export_user_vocabulary

_EXPORT_BUTTON_NAME = "pushButton_export_overlay"


def _status_bar(window: QMainWindow) -> QStatusBar | None:
    return window.findChild(QStatusBar, "statusbar")


def _set_status(window: QMainWindow, message: str) -> None:
    status = _status_bar(window)
    if status is not None:
        status.showMessage(message)


def _append_results(window: QMainWindow, message: str) -> None:
    results = window.findChild(QTextEdit, "textEdit_3")
    if results is None:
        return
    existing = results.toPlainText().strip()
    if existing:
        results.setPlainText(f"{existing}\n{message}")
    else:
        results.setPlainText(message)


def on_export_overlay(window: QMainWindow) -> None:
    suggested = str(Path.home() / default_export_filename())
    destination, _selected_filter = QFileDialog.getSaveFileName(
        window,
        "Export vocabulary overlay",
        suggested,
        "Zip archive (*.zip)",
    )
    if not destination:
        return

    try:
        written = export_user_vocabulary(Path(destination))
    except FileNotFoundError as error:
        message = str(error)
        _set_status(window, message)
        _append_results(window, message)
        return
    except OSError as error:
        message = f"Export failed: {error}"
        _set_status(window, message)
        _append_results(window, message)
        return

    message = f"Exported overlay to {written}"
    _set_status(window, message)
    _append_results(window, message)


def wire_export_overlay(window: QMainWindow) -> None:
    button = window.findChild(QPushButton, _EXPORT_BUTTON_NAME)
    if button is None:
        raise RuntimeError(f"Missing export control: {_EXPORT_BUTTON_NAME}")
    button.clicked.connect(partial(on_export_overlay, window))
