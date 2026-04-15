from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QMainWindow,
    QMenu,
    QSystemTrayIcon,
)

from config import AppConfig, save_config

_TRAY_ATTR = "_vipa_tray_icon"
_DAEMON_ATTR = "_vipa_practice_daemon"
_CHECKBOX_NAME = "checkBox_minimize_to_tray"


def system_tray_available() -> bool:
    return QSystemTrayIcon.isSystemTrayAvailable()


def _tray_icon_image() -> QIcon:
    themed = QIcon.fromTheme("accessories-dictionary")
    if not themed.isNull():
        return themed

    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#4a90d9"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(8, 8, 48, 48)
    painter.setPen(QPen(Qt.GlobalColor.white, 3))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "V")
    painter.end()
    return QIcon(pixmap)


def _is_daemon_running(window: QMainWindow) -> bool:
    daemon = getattr(window, _DAEMON_ATTR, None)
    return daemon is not None and daemon.is_running()


def _minimize_checkbox(window: QMainWindow) -> QCheckBox | None:
    return window.findChild(QCheckBox, _CHECKBOX_NAME)


def minimize_to_tray_enabled(window: QMainWindow, config: AppConfig) -> bool:
    checkbox = _minimize_checkbox(window)
    if checkbox is not None:
        return checkbox.isChecked()
    return config.minimize_to_tray_on_daemon


def _get_tray(window: QMainWindow, application: QApplication) -> QSystemTrayIcon:
    tray = getattr(window, _TRAY_ATTR, None)
    if tray is None:
        tray = QSystemTrayIcon(_tray_icon_image(), parent=window)
        tray.setToolTip("vipa")
        menu = QMenu(window)

        show_action = QAction("Show vipa", window)
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
    from ui_daemon import stop_daemon

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
    tray.setToolTip("vipa - practice daemon running")
    tray.show()
    window.hide()
    application.setQuitOnLastWindowClosed(False)
    return True


def show_window_from_tray(window: QMainWindow, application: QApplication) -> None:
    window.show()
    window.raise_()
    window.activateWindow()
    _sync_quit_on_last_window_closed(window, application)


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

    window.closeEvent = close_event  # type: ignore[method-assign]


def _on_minimize_to_tray_toggled(
    window: QMainWindow,
    config: AppConfig,
    checked: bool,
) -> None:
    config.minimize_to_tray_on_daemon = checked
    save_config(config)


def _apply_minimize_to_tray_checkbox(window: QMainWindow, config: AppConfig) -> None:
    checkbox = _minimize_checkbox(window)
    if checkbox is None:
        raise RuntimeError(f"Missing tray control: {_CHECKBOX_NAME}")

    available = system_tray_available()
    checkbox.setEnabled(available)
    if not available:
        checkbox.setToolTip(
            "System tray is not available in this desktop session "
            "(common on GNOME without a tray extension)"
        )

    checkbox.blockSignals(True)
    checkbox.setChecked(config.minimize_to_tray_on_daemon)
    checkbox.blockSignals(False)


def wire_tray(window: QMainWindow, application: QApplication, config: AppConfig) -> None:
    _apply_minimize_to_tray_checkbox(window, config)
    checkbox = _minimize_checkbox(window)
    if checkbox is not None:
        handler = partial(_on_minimize_to_tray_toggled, window, config)
        checkbox.toggled.connect(handler)
    _install_window_close_handler(window, application)
