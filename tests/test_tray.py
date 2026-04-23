from unittest.mock import MagicMock

from config import AppConfig
from ui_tray import (
    _apply_minimize_to_tray_checkbox,
    minimize_to_tray_enabled,
    tray_unavailable_reason,
)


def _mock_tray_controls(window: MagicMock, checkbox: MagicMock, reason_label: MagicMock) -> None:
    def find_child(widget_type, object_name: str):
        type_name = getattr(widget_type, "__name__", str(widget_type))
        if type_name == "QCheckBox" and object_name == "checkBox_minimize_to_tray":
            return checkbox
        if type_name == "QLabel" and object_name == "label_tray_unavailable":
            return reason_label
        return None

    window.findChild.side_effect = find_child


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


def test_apply_minimize_to_tray_checkbox_unchecked_when_tray_unavailable(monkeypatch):
    window = MagicMock()
    checkbox = MagicMock()
    reason_label = MagicMock()
    _mock_tray_controls(window, checkbox, reason_label)
    config = AppConfig(minimize_to_tray_on_daemon=True)
    monkeypatch.setattr("ui_tray.system_tray_available", lambda: False)

    _apply_minimize_to_tray_checkbox(window, config)

    checkbox.setEnabled.assert_called_once_with(False)
    checkbox.setChecked.assert_called_once_with(False)
    reason_label.setText.assert_called_once_with(tray_unavailable_reason())
    reason_label.show.assert_called_once_with()


def test_apply_minimize_to_tray_checkbox_hides_reason_when_tray_available(monkeypatch):
    window = MagicMock()
    checkbox = MagicMock()
    reason_label = MagicMock()
    _mock_tray_controls(window, checkbox, reason_label)
    config = AppConfig(minimize_to_tray_on_daemon=True)
    monkeypatch.setattr("ui_tray.system_tray_available", lambda: True)

    _apply_minimize_to_tray_checkbox(window, config)

    checkbox.setEnabled.assert_called_once_with(True)
    checkbox.setChecked.assert_called_once_with(True)
    reason_label.clear.assert_called_once_with()
    reason_label.hide.assert_called_once_with()
