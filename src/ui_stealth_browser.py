import threading

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QWidget,
)

from retrieve.stealth_fetch import (
    set_stealth_ensure_callback,
    stealth_browser_available,
)
from stealth_browser import browser_install_command, install_stealth_browser

_PROMPT_ATTR = "_vipa_stealth_browser_prompt"


class StealthBrowserInstallPrompt(QObject):
    _request = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self._lock = threading.Lock()
        self._done = threading.Event()
        self._ok = False
        self._request.connect(self._on_request)

    @Slot()
    def _on_request(self) -> None:
        try:
            self._ok = self._prompt_and_maybe_install()
        finally:
            self._done.set()

    def ensure(self) -> bool:
        if stealth_browser_available():
            return True
        if QThread.currentThread() == self.thread():
            return self._prompt_and_maybe_install()

        with self._lock:
            self._done.clear()
            self._ok = False
            self._request.emit()
            self._done.wait()
            return self._ok

    def _prompt_and_maybe_install(self) -> bool:
        if stealth_browser_available():
            return True

        command = browser_install_command()
        dialog = QMessageBox(self._parent)
        dialog.setWindowTitle("vipa - install browser")
        dialog.setText("Stealth fetch needs Chrome, Chromium, or Brave.")
        if command is None:
            dialog.setIcon(QMessageBox.Icon.Warning)
            dialog.setInformativeText(
                "No supported browser binary was found.\n\n"
                "Install Chrome, Chromium, or Brave, "
                "or set VIPA_STEALTH_BROWSER_PATH in .env to the browser executable."
            )
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.exec()
            return False

        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setInformativeText(
            "No supported browser binary was found.\n\n"
            "Install Chromium now?\n\n"
            f"Command: {' '.join(command)}"
        )
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.Yes)
        if dialog.exec() != QMessageBox.StandardButton.Yes:
            return False

        progress = QProgressDialog(
            "Installing Chromium…",
            None,
            0,
            0,
            self._parent,
        )
        progress.setWindowTitle("vipa")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.show()
        application = QApplication.instance()
        if application is not None:
            application.processEvents()

        try:
            install_stealth_browser()
        except RuntimeError as error:
            progress.close()
            self._show_error("Install failed", str(error))
            return False
        finally:
            progress.close()

        if stealth_browser_available():
            return True
        self._show_error(
            "Install failed",
            "Chromium is still not available after install.\n\n"
            "You can also set VIPA_STEALTH_BROWSER_PATH in .env.",
        )
        return False

    def _show_error(self, title: str, message: str) -> None:
        failure = QMessageBox(self._parent)
        failure.setIcon(QMessageBox.Icon.Critical)
        failure.setWindowTitle(f"vipa - {title}")
        failure.setText(title)
        failure.setInformativeText(message)
        failure.exec()


def wire_stealth_browser_prompt(window: QMainWindow) -> StealthBrowserInstallPrompt:
    prompt = StealthBrowserInstallPrompt(window)
    setattr(window, _PROMPT_ATTR, prompt)
    set_stealth_ensure_callback(prompt.ensure)
    return prompt
