from functools import partial

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStatusBar,
    QTextEdit,
)
from config import AppConfig, save_config
from daemon import PracticeDaemon, parse_interval_minutes
from notify import (
    NotifyBackend,
    backend_available,
    desktop_notifier_label,
    send_notification,
)
from ui_words import include_flags, language_key_from_combo
from words import format_word_row, get_random_words

_MAX_CONSECUTIVE_NOTIFY_FAILURES = 3
_DAEMON_ATTR = "_vipa_practice_daemon"
_NOTIFY_FAILURE_COUNT_ATTR = "_vipa_notify_failure_count"
_APPLICATION_ATTR = "_vipa_application"

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


def _select_notify_backend(window: QMainWindow, backend: NotifyBackend) -> None:
    for notify_backend, object_name in _BACKEND_RADIOS.items():
        button = window.findChild(QRadioButton, object_name)
        if button is None:
            continue
        button.blockSignals(True)
        button.setChecked(notify_backend == backend)
        button.blockSignals(False)


def _resolve_notify_backend(backend_name: str) -> NotifyBackend:
    backend = NotifyBackend(backend_name)
    if backend_available(backend):
        return backend
    if backend_available(NotifyBackend.DESKTOP):
        return NotifyBackend.DESKTOP
    return backend


def _apply_session_config(window: QMainWindow, config: AppConfig) -> None:
    _interval_input(window).setText(str(config.daemon_interval_minutes))
    _select_notify_backend(window, _resolve_notify_backend(config.notify_backend))


def _on_interval_saved(window: QMainWindow, config: AppConfig) -> None:
    try:
        minutes = parse_interval_minutes(_interval_input(window).text())
    except ValueError:
        return
    config.daemon_interval_minutes = minutes
    save_config(config)


def _on_notify_backend_toggled(
    window: QMainWindow,
    config: AppConfig,
    backend: NotifyBackend,
    checked: bool,
) -> None:
    if not checked:
        return
    config.notify_backend = backend.value
    save_config(config)


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


def consecutive_notify_failures_after(current_count: int, *, succeeded: bool) -> int:
    if succeeded:
        return 0
    return current_count + 1


def should_stop_daemon_after_notify_failures(
    failure_count: int,
    *,
    max_failures: int = _MAX_CONSECUTIVE_NOTIFY_FAILURES,
) -> bool:
    return failure_count >= max_failures


def _get_notify_failure_count(window: QMainWindow) -> int:
    return int(getattr(window, _NOTIFY_FAILURE_COUNT_ATTR, 0))


def _set_notify_failure_count(window: QMainWindow, count: int) -> None:
    setattr(window, _NOTIFY_FAILURE_COUNT_ATTR, count)


def _reset_notify_failure_count(window: QMainWindow) -> None:
    _set_notify_failure_count(window, 0)


def _application_for_window(window: QMainWindow) -> QApplication | None:
    application = getattr(window, _APPLICATION_ATTR, None)
    if isinstance(application, QApplication):
        return application
    instance = QApplication.instance()
    if isinstance(instance, QApplication):
        return instance
    return None


def prompt_notify_failure_dialog(
    window: QMainWindow,
    application: QApplication | None,
    error_message: str,
    failure_count: int,
) -> bool:
    window.show()
    window.raise_()
    window.activateWindow()

    dialog = QMessageBox(window)
    dialog.setIcon(QMessageBox.Icon.Warning)
    dialog.setWindowTitle("vipa - notification failed")
    dialog.setText("The practice daemon could not send a notification.")
    dialog.setInformativeText(
        f"{error_message}\n\nFailure {failure_count} of "
        f"{_MAX_CONSECUTIVE_NOTIFY_FAILURES}. "
        f"The daemon stops after {_MAX_CONSECUTIVE_NOTIFY_FAILURES} "
        "consecutive failures."
    )
    dialog.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
    exit_button = dialog.addButton("Exit program", QMessageBox.ButtonRole.RejectRole)
    dialog.exec()

    if dialog.clickedButton() == exit_button:
        if application is not None:
            application.quit()
        return False
    return True


def _surface_notify_failure_alert(
    window: QMainWindow,
    application: QApplication | None,
    error_message: str,
    failure_count: int,
) -> str:
    title = "vipa - notification failed"
    body = f"{error_message} ({failure_count}/{_MAX_CONSECUTIVE_NOTIFY_FAILURES})"
    if backend_available(NotifyBackend.DESKTOP):
        try:
            send_notification(title, body, backend=NotifyBackend.DESKTOP)
            return "background"
        except (ValueError, RuntimeError, OSError):
            pass

    if application is not None:
        from ui_tray import show_tray_message

        if show_tray_message(window, application, title, body):
            return "background"

    if prompt_notify_failure_dialog(window, application, error_message, failure_count):
        return "continue"
    return "exit"


def _handle_notify_failure(
    window: QMainWindow,
    application: QApplication | None,
    error: Exception,
) -> None:
    failure_count = consecutive_notify_failures_after(
        _get_notify_failure_count(window),
        succeeded=False,
    )
    _set_notify_failure_count(window, failure_count)
    error_message = str(error)
    _set_status(window, error_message)
    _append_result_line(window, f"Notify error: {error_message}")
    alert_result = _surface_notify_failure_alert(
        window,
        application,
        error_message,
        failure_count,
    )
    if alert_result == "exit":
        return

    if should_stop_daemon_after_notify_failures(failure_count):
        stop_message = (
            f"Daemon stopped after {failure_count} consecutive notification failures."
        )
        _append_result_line(window, stop_message)
        stop_daemon(window, application, status_message=stop_message)


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
        _handle_notify_failure(window, _application_for_window(window), error)
        return

    _reset_notify_failure_count(window)
    _append_result_line(window, body)
    _set_status(window, f"Notified ({backend.value}): {body}")


def _get_daemon(window: QMainWindow) -> PracticeDaemon:
    daemon = getattr(window, _DAEMON_ATTR, None)
    if daemon is None:
        daemon = PracticeDaemon(partial(fire_practice_notification, window), parent=window)
        setattr(window, _DAEMON_ATTR, daemon)
    return daemon


def stop_daemon(
    window: QMainWindow,
    application: QApplication | None = None,
    *,
    status_message: str | None = None,
) -> None:
    daemon = getattr(window, _DAEMON_ATTR, None)
    if daemon is not None:
        daemon.stop()
    _update_daemon_button(window, False)
    _set_status(window, status_message or "Daemon stopped")
    if application is not None:
        from ui_tray import show_window_from_tray

        show_window_from_tray(window, application)


def start_daemon(
    window: QMainWindow,
    application: QApplication | None = None,
    config: AppConfig | None = None,
) -> None:
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

    _reset_notify_failure_count(window)
    _update_daemon_button(window, True)
    _set_status(window, f"Daemon running every {minutes} min ({backend.value})")

    if application is not None and config is not None:
        from ui_tray import try_minimize_on_daemon_start

        if try_minimize_on_daemon_start(window, application, config):
            _set_status(
                window,
                f"Daemon running every {minutes} min ({backend.value}); minimized to tray",
            )


def on_daemon_toggle(
    window: QMainWindow,
    application: QApplication,
    config: AppConfig,
) -> None:
    daemon = getattr(window, _DAEMON_ATTR, None)
    if daemon is not None and daemon.is_running():
        stop_daemon(window, application)
        return
    start_daemon(window, application, config)


def wire_daemon(
    window: QMainWindow,
    application: QApplication,
    config: AppConfig,
) -> None:
    setattr(window, _APPLICATION_ATTR, application)
    button = _daemon_button(window)
    handler = partial(on_daemon_toggle, window, application, config)
    button.clicked.connect(handler)
    _apply_backend_labels(window)
    _apply_session_config(window, config)
    _interval_input(window).editingFinished.connect(partial(_on_interval_saved, window, config))
    for backend, object_name in _BACKEND_RADIOS.items():
        radio_button = window.findChild(QRadioButton, object_name)
        if radio_button is None:
            continue
        toggle_handler = partial(_on_notify_backend_toggled, window, config, backend)
        radio_button.toggled.connect(toggle_handler)
    _update_daemon_button(window, False)
