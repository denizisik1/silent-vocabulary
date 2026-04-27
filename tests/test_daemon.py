from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from daemon import PracticeDaemon, parse_interval_minutes
from notify import NotifyBackend, desktop_notifier_label, send_notification
from ui_daemon import (
    _MAX_CONSECUTIVE_NOTIFY_FAILURES,
    _handle_notify_failure,
    _surface_notify_failure_alert,
    consecutive_notify_failures_after,
    should_stop_daemon_after_notify_failures,
)


def test_parse_interval_minutes_accepts_positive_int():
    assert parse_interval_minutes("15") == 15


def test_parse_interval_minutes_rejects_empty():
    with pytest.raises(ValueError, match="Interval is empty"):
        parse_interval_minutes("   ")


def test_parse_interval_minutes_rejects_non_integer():
    with pytest.raises(ValueError, match="whole number"):
        parse_interval_minutes("1.5")


def test_parse_interval_minutes_rejects_zero():
    with pytest.raises(ValueError, match="at least 1"):
        parse_interval_minutes("0")


def test_practice_daemon_fires_immediately_and_can_stop():
    ticks: list[int] = []

    def on_tick() -> None:
        ticks.append(1)

    if QCoreApplication.instance() is None:
        QCoreApplication([])
    daemon = PracticeDaemon(on_tick)
    daemon.start(1, fire_immediately=True)
    assert daemon.is_running()
    assert ticks == [1]

    daemon.stop()
    assert not daemon.is_running()


def test_send_notification_prefers_busctl(monkeypatch):
    calls: list[list[str]] = []

    def fake_which(name: str) -> str | None:
        if name == "busctl":
            return "/usr/bin/busctl"
        if name == "notify-send":
            return None
        return None

    def fake_run(command, check=False, capture_output=True, text=True):
        calls.append(command)
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        result.stdout = "u 1\n"
        return result

    monkeypatch.setattr("notify.shutil.which", fake_which)
    monkeypatch.setattr("notify.subprocess.run", fake_run)

    send_notification("vipa", "der Abend - evening ([aːbənt])")

    assert calls
    assert calls[0][0] == "busctl"
    assert "org.freedesktop.Notifications" in calls[0]
    assert "der Abend - evening ([aːbənt])" in calls[0]


def test_send_notification_falls_back_to_notify_send(monkeypatch):
    calls: list[list[str]] = []

    def fake_which(name: str) -> str | None:
        if name == "notify-send":
            return "/usr/bin/notify-send"
        return None

    def fake_run(command, check=False, capture_output=True, text=True):
        calls.append(command)
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        result.stdout = ""
        return result

    monkeypatch.setattr("notify.shutil.which", fake_which)
    monkeypatch.setattr("notify.subprocess.run", fake_run)

    send_notification("vipa", "body")

    assert calls[0][0] == "notify-send"


def test_send_notification_requires_a_method(monkeypatch):
    monkeypatch.setattr("notify.shutil.which", lambda name: None)

    with pytest.raises(RuntimeError, match="No desktop notification method"):
        send_notification("vipa", "body", backend=NotifyBackend.DESKTOP)


def test_send_notification_windows_not_implemented():
    with pytest.raises(RuntimeError, match="Windows notifications"):
        send_notification("vipa", "body", backend=NotifyBackend.WINDOWS)


def test_desktop_notifier_label_detects_dunst(monkeypatch):
    monkeypatch.setattr("notify.shutil.which", lambda name: "/usr/bin/busctl")

    def fake_run(command, check=False, capture_output=True, text=True):
        result = MagicMock()
        result.returncode = 0
        result.stdout = "Unit: dunst.service\n"
        result.stderr = ""
        return result

    monkeypatch.setattr("notify.subprocess.run", fake_run)
    assert desktop_notifier_label() == "Dunst"


def test_desktop_notifier_label_detects_gnome(monkeypatch):
    monkeypatch.setattr("notify.shutil.which", lambda name: "/usr/bin/busctl")

    def fake_run(command, check=False, capture_output=True, text=True):
        result = MagicMock()
        result.returncode = 0
        result.stdout = (
            "Unit: user@1000.service\nExe=/usr/bin/gjs-console\n"
            "CommandLine=/usr/bin/gjs -m /usr/share/gnome-shell/org.gnome.Shell.Notifications\n"
        )
        result.stderr = ""
        return result

    monkeypatch.setattr("notify.subprocess.run", fake_run)
    assert desktop_notifier_label() == "GNOME"


def test_consecutive_notify_failures_after_success_resets():
    assert consecutive_notify_failures_after(2, succeeded=True) == 0


def test_consecutive_notify_failures_after_failure_increments():
    assert consecutive_notify_failures_after(2, succeeded=False) == 3


def test_should_stop_daemon_after_notify_failures():
    assert not should_stop_daemon_after_notify_failures(2)
    assert should_stop_daemon_after_notify_failures(_MAX_CONSECUTIVE_NOTIFY_FAILURES)


def test_handle_notify_failure_stops_daemon_after_threshold(monkeypatch):
    window = MagicMock()
    application = MagicMock()
    stop_daemon = MagicMock()
    monkeypatch.setattr("ui_daemon._get_notify_failure_count", lambda _window: 2)
    monkeypatch.setattr("ui_daemon._set_notify_failure_count", MagicMock())
    monkeypatch.setattr("ui_daemon._surface_notify_failure_alert", lambda *args, **kwargs: "background")
    monkeypatch.setattr("ui_daemon.stop_daemon", stop_daemon)

    _handle_notify_failure(window, application, RuntimeError("notify-send failed"))

    stop_daemon.assert_called_once()
    stop_args, stop_kwargs = stop_daemon.call_args
    assert stop_args == (window, application)
    assert "3 consecutive notification failures" in stop_kwargs["status_message"]


def test_handle_notify_failure_keeps_daemon_running_below_threshold(monkeypatch):
    window = MagicMock()
    application = MagicMock()
    stop_daemon = MagicMock()
    monkeypatch.setattr("ui_daemon._get_notify_failure_count", lambda _window: 0)
    monkeypatch.setattr("ui_daemon._set_notify_failure_count", MagicMock())
    monkeypatch.setattr("ui_daemon._surface_notify_failure_alert", lambda *args, **kwargs: "background")
    monkeypatch.setattr("ui_daemon.stop_daemon", stop_daemon)

    _handle_notify_failure(window, application, RuntimeError("notify-send failed"))

    stop_daemon.assert_not_called()


def test_handle_notify_failure_dialog_ok_still_stops_after_threshold(monkeypatch):
    window = MagicMock()
    application = MagicMock()
    stop_daemon = MagicMock()
    monkeypatch.setattr("ui_daemon._get_notify_failure_count", lambda _window: 2)
    monkeypatch.setattr("ui_daemon._set_notify_failure_count", MagicMock())
    monkeypatch.setattr("ui_daemon._surface_notify_failure_alert", lambda *args, **kwargs: "continue")
    monkeypatch.setattr("ui_daemon.stop_daemon", stop_daemon)

    _handle_notify_failure(window, application, RuntimeError("notify-send failed"))

    stop_daemon.assert_called_once()
    assert "3 consecutive notification failures" in stop_daemon.call_args.kwargs["status_message"]


def test_handle_notify_failure_dialog_ok_below_threshold_keeps_running(monkeypatch):
    window = MagicMock()
    application = MagicMock()
    stop_daemon = MagicMock()
    monkeypatch.setattr("ui_daemon._get_notify_failure_count", lambda _window: 0)
    monkeypatch.setattr("ui_daemon._set_notify_failure_count", MagicMock())
    monkeypatch.setattr("ui_daemon._surface_notify_failure_alert", lambda *args, **kwargs: "continue")
    monkeypatch.setattr("ui_daemon.stop_daemon", stop_daemon)

    _handle_notify_failure(window, application, RuntimeError("notify-send failed"))

    stop_daemon.assert_not_called()


def test_handle_notify_failure_dialog_exit_skips_auto_stop(monkeypatch):
    window = MagicMock()
    application = MagicMock()
    stop_daemon = MagicMock()
    monkeypatch.setattr("ui_daemon._get_notify_failure_count", lambda _window: 2)
    monkeypatch.setattr("ui_daemon._set_notify_failure_count", MagicMock())
    monkeypatch.setattr("ui_daemon._surface_notify_failure_alert", lambda *args, **kwargs: "exit")
    monkeypatch.setattr("ui_daemon.stop_daemon", stop_daemon)

    _handle_notify_failure(window, application, RuntimeError("notify-send failed"))

    stop_daemon.assert_not_called()


def test_surface_notify_failure_alert_uses_dialog_when_background_alerts_fail(monkeypatch):
    window = MagicMock()
    application = MagicMock()
    prompt = MagicMock(return_value=True)
    monkeypatch.setattr("ui_daemon.backend_available", lambda _backend: True)
    monkeypatch.setattr(
        "ui_daemon.send_notification",
        MagicMock(side_effect=RuntimeError("notify-send failed")),
    )
    monkeypatch.setattr("ui_tray.show_tray_message", lambda *args, **kwargs: False)
    monkeypatch.setattr("ui_daemon.prompt_notify_failure_dialog", prompt)

    result = _surface_notify_failure_alert(
        window,
        application,
        "notify-send failed",
        1,
    )

    assert result == "continue"
    prompt.assert_called_once_with(window, application, "notify-send failed", 1)
