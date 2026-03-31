from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from daemon import PracticeDaemon, parse_interval_minutes
from notify import NotifyBackend, desktop_notifier_label, send_notification


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
