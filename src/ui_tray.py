from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QMenu,
    QSystemTrayIcon,
)

from config import AppConfig, save_config

_TRAY_ATTR = "_silent_vocabulary_tray_icon"
_DAEMON_ATTR = "_silent_vocabulary_practice_daemon"
_CHECKBOX_NAME = "checkBox_minimize_to_tray"
_UNAVAILABLE_LABEL_NAME = "label_tray_unavailable"
_ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
_TRAY_UNAVAILABLE_REASON = (
    "System tray is not available in this desktop session "
    "(common on GNOME without a tray extension)."
)


def system_tray_available() -> bool:
    return QSystemTrayIcon.isSystemTrayAvailable()


def app_icon() -> QIcon:
    if _ICON_PATH.is_file():
        return QIcon(str(_ICON_PATH))

    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#c45c2a"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 12, 12)
    painter.setPen(QPen(QColor("#f5e6d3"), 3))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "SV")
    painter.end()
    return QIcon(pixmap)


def _tray_icon_image() -> QIcon:
    return app_icon()


def _is_daemon_running(window: QMainWindow) -> bool:
    daemon = getattr(window, _DAEMON_ATTR, None)
    return daemon is not None and daemon.is_running()


def _minimize_checkbox(window: QMainWindow) -> QCheckBox | None:
    return window.findChild(QCheckBox, _CHECKBOX_NAME)


def _tray_unavailable_label(window: QMainWindow) -> QLabel | None:
    return window.findChild(QLabel, _UNAVAILABLE_LABEL_NAME)


def tray_unavailable_reason() -> str:
    return _TRAY_UNAVAILABLE_REASON


def minimize_to_tray_enabled(window: QMainWindow, config: AppConfig) -> bool:
    checkbox = _minimize_checkbox(window)
    if checkbox is not None:
        return checkbox.isChecked()
    return config.minimize_to_tray_on_daemon


def _get_tray(window: QMainWindow, application: QApplication) -> QSystemTrayIcon:
    tray = getattr(window, _TRAY_ATTR, None)
    if tray is None:
        tray = QSystemTrayIcon(_tray_icon_image(), parent=window)
        tray.setToolTip("silent-vocabulary")
        menu = QMenu(window)

        show_action = QAction("Show silent-vocabulary", window)
        show_action.triggered.connect(partial(show_window_from_tray, window, application))
        menu.addAction(show_action)

        stop_action = QAction("Stop daemon", window)
        stop_action.triggered.connect(partial(_stop_daemon_from_tray, window, application))
        menu.addAction(stop_action)

        quit_action = QAction("Quit", window)
        quit_action.triggered.connect(application.quit)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(partial(_on_tray_activated, window, application))
        setattr(window, _TRAY_ATTR, tray)
    return tray


def _on_tray_activated(
    window: QMainWindow,
    application: QApplication,
    reason: QSystemTrayIcon.ActivationReason,
) -> None:
    if reason in (
        QSystemTrayIcon.ActivationReason.Trigger,
        QSystemTrayIcon.ActivationReason.DoubleClick,
    ):
        show_window_from_tray(window, application)


def _stop_daemon_from_tray(window: QMainWindow, application: QApplication) -> None:
    from ui_daemon import stop_daemon  # pylint: disable=import-outside-toplevel  # circular import

    stop_daemon(window)
    show_window_from_tray(window, application)


def _sync_quit_on_last_window_closed(window: QMainWindow, application: QApplication) -> None:
    if _is_daemon_running(window) and not window.isVisible():
        application.setQuitOnLastWindowClosed(False)
        return
    application.setQuitOnLastWindowClosed(True)


def hide_window_to_tray(window: QMainWindow, application: QApplication) -> bool:
    if not system_tray_available():
        return False

    tray = _get_tray(window, application)
    tray.setToolTip("silent-vocabulary - practice daemon running")
    tray.show()
    window.hide()
    application.setQuitOnLastWindowClosed(False)
    return True


def show_window_from_tray(window: QMainWindow, application: QApplication) -> None:
    window.show()
    window.raise_()
    window.activateWindow()
    _sync_quit_on_last_window_closed(window, application)


def show_tray_message(  # pylint: disable=too-many-arguments  # tray API needs window + message
    window: QMainWindow,
    application: QApplication,
    title: str,
    message: str,
    *,
    icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Warning,
    duration_ms: int = 10000,
) -> bool:
    if not system_tray_available():
        return False

    tray = _get_tray(window, application)
    tray.show()
    tray.showMessage(title, message, icon, duration_ms)
    return True


def try_minimize_on_daemon_start(
    window: QMainWindow,
    application: QApplication,
    config: AppConfig,
) -> bool:
    if not minimize_to_tray_enabled(window, config):
        return False
    if not system_tray_available():
        return False
    return hide_window_to_tray(window, application)


def _should_hide_on_close(window: QMainWindow) -> bool:
    return _is_daemon_running(window) and system_tray_available()


def _install_window_close_handler(window: QMainWindow, application: QApplication) -> None:
    original_close_event = window.closeEvent

    def close_event(event: QCloseEvent) -> None:
        if _should_hide_on_close(window):
            event.ignore()
            hide_window_to_tray(window, application)
            return
        if original_close_event is not None:
            original_close_event(event)
        else:
            event.accept()

    window.closeEvent = close_event  # type: ignore[method-assign]  # Qt lets us replace the handler


def _on_minimize_to_tray_toggled(config: AppConfig, checked: bool) -> None:
    config.minimize_to_tray_on_daemon = checked
    save_config(config)


def _apply_minimize_to_tray_checkbox(window: QMainWindow, config: AppConfig) -> None:
    checkbox = _minimize_checkbox(window)
    if checkbox is None:
        raise RuntimeError(f"Missing tray control: {_CHECKBOX_NAME}")

    reason_label = _tray_unavailable_label(window)
    if reason_label is None:
        raise RuntimeError(f"Missing tray control: {_UNAVAILABLE_LABEL_NAME}")

    available = system_tray_available()
    checkbox.setEnabled(available)
    if available:
        checkbox.setToolTip(
            "Hide the window in the system tray while the practice daemon runs "
            "(KDE, XFCE, GNOME with tray support, ...)"
        )
        reason_label.clear()
        reason_label.hide()
        checkbox.blockSignals(True)
        checkbox.setChecked(config.minimize_to_tray_on_daemon)
        checkbox.blockSignals(False)
        return

    checkbox.setToolTip("")
    reason_label.setText(tray_unavailable_reason())
    reason_label.show()
    checkbox.blockSignals(True)
    checkbox.setChecked(False)
    checkbox.blockSignals(False)


def wire_tray(window: QMainWindow, application: QApplication, config: AppConfig) -> None:
    _apply_minimize_to_tray_checkbox(window, config)
    checkbox = _minimize_checkbox(window)
    if checkbox is not None:
        handler = partial(_on_minimize_to_tray_toggled, config)
        checkbox.toggled.connect(handler)
    _install_window_close_handler(window, application)
