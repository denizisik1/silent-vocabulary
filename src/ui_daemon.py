from functools import partial

from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QStatusBar,
    QTextEdit,
)
from daemon import PracticeDaemon, parse_interval_minutes
from notify import (
    NotifyBackend,
    backend_available,
    desktop_notifier_label,
    send_notification,
)
from ui_words import include_flags, language_key_from_combo
from words import format_word_row, get_random_words

_DAEMON_ATTR = "_vipa_practice_daemon"

_BACKEND_RADIOS = {
    NotifyBackend.DESKTOP: "radioButton",
    NotifyBackend.WINDOWS: "radioButton_2",
}


def _results_view(window: QMainWindow) -> QTextEdit:
    results = window.findChild(QTextEdit, "textEdit_3")
    if results is None:
        raise RuntimeError("Missing results view: textEdit_3")
    return results


def _status_bar(window: QMainWindow) -> QStatusBar | None:
    return window.findChild(QStatusBar, "statusbar")


def _set_status(window: QMainWindow, message: str) -> None:
    status = _status_bar(window)
    if status is not None:
        status.showMessage(message)


def _daemon_button(window: QMainWindow) -> QPushButton:
    button = window.findChild(QPushButton, "pushButton_2")
    if button is None:
        raise RuntimeError("Missing daemon button: pushButton_2")
    return button


def _interval_input(window: QMainWindow) -> QLineEdit:
    editor = window.findChild(QLineEdit, "lineEdit_3")
    if editor is None:
        raise RuntimeError("Missing interval control: lineEdit_3")
    return editor


def _update_daemon_button(window: QMainWindow, running: bool) -> None:
    button = _daemon_button(window)
    button.setText("Stop daemon" if running else "Start daemon")


def _append_result_line(window: QMainWindow, line: str) -> None:
    results = _results_view(window)
    existing = results.toPlainText().strip()
    if existing:
        results.setPlainText(f"{existing}\n{line}")
    else:
        results.setPlainText(line)


def selected_notify_backend(window: QMainWindow) -> NotifyBackend:
    for backend, object_name in _BACKEND_RADIOS.items():
        button = window.findChild(QRadioButton, object_name)
        if button is not None and button.isChecked():
            return backend
    return NotifyBackend.DESKTOP


def _apply_backend_labels(window: QMainWindow) -> None:
    desktop_button = window.findChild(QRadioButton, "radioButton")
    windows_button = window.findChild(QRadioButton, "radioButton_2")
    if desktop_button is not None:
        label = desktop_notifier_label()
        desktop_button.setText(label)
        desktop_button.setEnabled(backend_available(NotifyBackend.DESKTOP))
        desktop_button.setToolTip(
            "Freedesktop notifications via D-Bus "
            "(GNOME, KDE Plasma, XFCE, Dunst, Mako, SwayNC, ...)"
        )
    if windows_button is not None:
        windows_button.setEnabled(backend_available(NotifyBackend.WINDOWS))
        windows_button.setToolTip("Windows toast notifications (not implemented yet)")


def fire_practice_notification(window: QMainWindow) -> None:
    language_combo = window.findChild(QComboBox, "comboBox")
    if language_combo is None:
        raise RuntimeError("Missing language control: comboBox")

    language_key = language_key_from_combo(language_combo.currentText())
    include = include_flags(window)
    backend = selected_notify_backend(window)
    try:
        words = get_random_words(language_key, 1)
    except (ValueError, FileNotFoundError, OSError) as error:
        _set_status(window, str(error))
        _append_result_line(window, f"Daemon error: {error}")
        return

    row = words[0]
    body = format_word_row(row, include)
    title = "vipa"
    try:
        send_notification(title, body, backend=backend)
    except (ValueError, RuntimeError, OSError) as error:
        _set_status(window, str(error))
        _append_result_line(window, f"Notify error: {error}")
        return

    _append_result_line(window, body)
    _set_status(window, f"Notified ({backend.value}): {body}")


def _get_daemon(window: QMainWindow) -> PracticeDaemon:
    daemon = getattr(window, _DAEMON_ATTR, None)
    if daemon is None:
        daemon = PracticeDaemon(partial(fire_practice_notification, window), parent=window)
        setattr(window, _DAEMON_ATTR, daemon)
    return daemon


def stop_daemon(window: QMainWindow) -> None:
    daemon = getattr(window, _DAEMON_ATTR, None)
    if daemon is not None:
        daemon.stop()
    _update_daemon_button(window, False)
    _set_status(window, "Daemon stopped")


def start_daemon(window: QMainWindow) -> None:
    backend = selected_notify_backend(window)
    if not backend_available(backend):
        message = (
            "Desktop notifications need busctl or notify-send."
            if backend is NotifyBackend.DESKTOP
            else "Windows notifications are not implemented yet."
        )
        _set_status(window, message)
        _append_result_line(window, message)
        return

    interval_text = _interval_input(window).text()
    try:
        minutes = parse_interval_minutes(interval_text)
    except ValueError as error:
        _set_status(window, str(error))
        _append_result_line(window, str(error))
        return

    daemon = _get_daemon(window)
    try:
        daemon.start(minutes, fire_immediately=True)
    except ValueError as error:
        _set_status(window, str(error))
        return

    _update_daemon_button(window, True)
    _set_status(window, f"Daemon running every {minutes} min ({backend.value})")


def on_daemon_toggle(window: QMainWindow) -> None:
    daemon = getattr(window, _DAEMON_ATTR, None)
    if daemon is not None and daemon.is_running():
        stop_daemon(window)
        return
    start_daemon(window)


def wire_daemon(window: QMainWindow) -> None:
    button = _daemon_button(window)
    handler = partial(on_daemon_toggle, window)
    button.clicked.connect(handler)
    _apply_backend_labels(window)
    _update_daemon_button(window, False)
