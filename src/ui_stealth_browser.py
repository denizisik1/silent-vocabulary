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
from stealth_browser import (
    browser_install_command,
    browser_remove_command,
    install_stealth_browser,
    remove_stealth_browser,
)

_PROMPT_ATTR = "_vipa_stealth_browser_prompt"


def run_browser_package_action(
    parent: QWidget,
    *,
    title: str,
    question: str,
    progress_label: str,
    command: list[str] | None,
    unavailable_message: str,
    action,
    success_check,
    success_failure_message: str,
) -> bool:
    dialog = QMessageBox(parent)
    dialog.setWindowTitle(title)
    if command is None:
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setText(unavailable_message)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()
        return False

    dialog.setIcon(QMessageBox.Icon.Question)
    dialog.setText(question)
    dialog.setInformativeText(f"Command: {' '.join(command)}")
    dialog.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    dialog.setDefaultButton(QMessageBox.StandardButton.Yes)
    if dialog.exec() != QMessageBox.StandardButton.Yes:
        return False

    progress = QProgressDialog(progress_label, None, 0, 0, parent)
    progress.setWindowTitle("vipa")
    progress.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress.setMinimumDuration(0)
    progress.setCancelButton(None)
    progress.show()
    application = QApplication.instance()
    if application is not None:
        application.processEvents()

    try:
        action()
    except RuntimeError as error:
        progress.close()
        failure = QMessageBox(parent)
        failure.setIcon(QMessageBox.Icon.Critical)
        failure.setWindowTitle("vipa - action failed")
        failure.setText("Action failed")
        failure.setInformativeText(str(error))
        failure.exec()
        return False
    finally:
        progress.close()

    if success_check():
        return True

    failure = QMessageBox(parent)
    failure.setIcon(QMessageBox.Icon.Critical)
    failure.setWindowTitle("vipa - action failed")
    failure.setText("Action failed")
    failure.setInformativeText(success_failure_message)
    failure.exec()
    return False


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
        return run_browser_package_action(
            self._parent,
            title="vipa - install browser",
            question="Stealth fetch needs Chrome, Chromium, or Brave. Install Chromium now?",
            progress_label="Installing Chromium…",
            command=browser_install_command(),
            unavailable_message=(
                "No supported browser binary was found.\n\n"
                "Install Chrome, Chromium, or Brave, "
                "or set the browser path in Settings."
            ),
            action=install_stealth_browser,
            success_check=stealth_browser_available,
            success_failure_message=(
                "Chromium is still not available after install.\n\n"
                "You can also set the browser path in Settings."
            ),
        )


def remove_chromium_with_prompt(parent: QWidget) -> bool:
    return run_browser_package_action(
        parent,
        title="vipa - remove browser",
        question="Remove the system Chromium package?",
        progress_label="Removing Chromium…",
        command=browser_remove_command(),
        unavailable_message=(
            "No automatic browser removal is available for this system.\n\n"
            "Uninstall Chrome, Chromium, or Brave with your package manager."
        ),
        action=remove_stealth_browser,
        success_check=lambda: not stealth_browser_available(),
        success_failure_message=(
            "A browser binary is still available after removal.\n\n"
            "Another Chrome/Chromium/Brave install may still be on PATH."
        ),
    )


def install_chromium_with_prompt(parent: QWidget) -> bool:
    return run_browser_package_action(
        parent,
        title="vipa - install browser",
        question="Install Chromium for stealth fetch?",
        progress_label="Installing Chromium…",
        command=browser_install_command(),
        unavailable_message=(
            "No automatic browser install is available for this system.\n\n"
            "Install Chrome, Chromium, or Brave manually, "
            "or set the browser path in Settings."
        ),
        action=install_stealth_browser,
        success_check=stealth_browser_available,
        success_failure_message=(
            "Chromium is still not available after install.\n\n"
            "You can also set the browser path in Settings."
        ),
    )


def wire_stealth_browser_prompt(window: QMainWindow) -> StealthBrowserInstallPrompt:
    prompt = StealthBrowserInstallPrompt(window)
    setattr(window, _PROMPT_ATTR, prompt)
    set_stealth_ensure_callback(prompt.ensure)
    return prompt
