from unittest.mock import MagicMock

from config import AppConfig
from ui_tray import minimize_to_tray_enabled


def test_minimize_to_tray_enabled_uses_checkbox_state():
    window = MagicMock()
    checkbox = MagicMock()
    checkbox.isChecked.return_value = False
    window.findChild.return_value = checkbox

    enabled = minimize_to_tray_enabled(window, AppConfig(minimize_to_tray_on_daemon=True))

    assert enabled is False


def test_minimize_to_tray_enabled_falls_back_to_config():
    window = MagicMock()
    window.findChild.return_value = None

    enabled = minimize_to_tray_enabled(window, AppConfig(minimize_to_tray_on_daemon=False))

    assert enabled is False


def test_hide_window_to_tray_returns_false_when_unavailable(monkeypatch):
    from ui_tray import hide_window_to_tray

    window = MagicMock()
    window.isVisible.return_value = True
    application = MagicMock()
    monkeypatch.setattr("ui_tray.system_tray_available", lambda: False)

    hidden = hide_window_to_tray(window, application)

    assert hidden is False
    window.hide.assert_not_called()


def test_try_minimize_on_daemon_start_respects_config(monkeypatch):
    from ui_tray import try_minimize_on_daemon_start

    window = MagicMock()
    window.findChild.return_value = None
    application = MagicMock()
    config = AppConfig(minimize_to_tray_on_daemon=False)

    monkeypatch.setattr("ui_tray.system_tray_available", lambda: True)
    hide = MagicMock(return_value=True)
    monkeypatch.setattr("ui_tray.hide_window_to_tray", hide)

    minimized = try_minimize_on_daemon_start(window, application, config)

    assert minimized is False
    hide.assert_not_called()
