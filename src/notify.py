import shutil
import subprocess
from enum import Enum


class NotifyBackend(str, Enum):
    DESKTOP = "desktop"
    WINDOWS = "windows"


def notify_send_available() -> bool:
    return shutil.which("notify-send") is not None


def busctl_available() -> bool:
    return shutil.which("busctl") is not None


def desktop_notifications_available() -> bool:
    return notify_send_available() or busctl_available()


def _notification_service_unit() -> str | None:
    if not busctl_available():
        return None

    completed = subprocess.run(
        ["busctl", "--user", "status", "org.freedesktop.Notifications"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None

    unit_name: str | None = None
    exe_path = ""
    command_line = ""
    for line in completed.stdout.splitlines():
        if line.startswith("Unit:"):
            unit_name = line.split(":", 1)[1].strip().removesuffix(".service")
        elif line.startswith("Exe="):
            exe_path = line.split("=", 1)[1].strip().casefold()
        elif line.startswith("CommandLine="):
            command_line = line.split("=", 1)[1].strip().casefold()

    probe = f"{unit_name or ''} {exe_path} {command_line}"
    if "dunst" in probe:
        return "dunst"
    if "gnome" in probe or "gjs" in probe:
        return "org.gnome.Shell.Notifications"
    if "plasma" in probe or "kde" in probe:
        return "plasma"
    if "xfce" in probe:
        return "xfce4-notifyd"
    if "mako" in probe:
        return "mako"
    if "swaync" in probe:
        return "swaync"
    return unit_name


def desktop_notifier_label() -> str:
    unit = _notification_service_unit()
    if unit:
        lowered = unit.casefold()
        if "dunst" in lowered:
            return "Dunst"
        if "gnome" in lowered:
            return "GNOME"
        if "plasma" in lowered or "kde" in lowered:
            return "KDE"
        if "xfce" in lowered:
            return "XFCE"
        if "mako" in lowered:
            return "Mako"
        if "swaync" in lowered:
            return "SwayNC"
        return unit
    if desktop_notifications_available():
        return "Desktop"
    return "Desktop (unavailable)"


def backend_available(backend: NotifyBackend) -> bool:
    if backend is NotifyBackend.DESKTOP:
        return desktop_notifications_available()
    if backend is NotifyBackend.WINDOWS:
        return False
    return False


def _send_via_busctl(title: str, body: str, *, expire_ms: int) -> None:
    command = [
        "busctl",
        "--user",
        "call",
        "org.freedesktop.Notifications",
        "/org/freedesktop/Notifications",
        "org.freedesktop.Notifications",
        "Notify",
        "susssasa{sv}i",
        "vipa",
        "0",
        "",
        title,
        body,
        "0",
        "0",
        str(expire_ms),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown error").strip()
        raise RuntimeError(f"Desktop notification failed: {detail}")


def _send_via_notify_send(title: str, body: str, *, expire_ms: int) -> None:
    command = [
        "notify-send",
        "--app-name=vipa",
        f"--expire-time={expire_ms}",
        "--urgency=normal",
        title,
        body,
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown error").strip()
        raise RuntimeError(f"notify-send failed: {detail}")


def send_desktop_notification(title: str, body: str, *, expire_ms: int = 10000) -> None:
    if busctl_available():
        try:
            _send_via_busctl(title, body, expire_ms=expire_ms)
            return
        except RuntimeError:
            if not notify_send_available():
                raise

    if notify_send_available():
        _send_via_notify_send(title, body, expire_ms=expire_ms)
        return

    raise RuntimeError(
        "No desktop notification method available. "
        "Need busctl (systemd) or notify-send (libnotify-bin)."
    )


def send_windows_notification(title: str, body: str) -> None:
    raise RuntimeError("Windows notifications are not implemented yet.")


def send_notification(
    title: str,
    body: str,
    *,
    backend: NotifyBackend = NotifyBackend.DESKTOP,
    expire_ms: int = 10000,
) -> None:
    if not title.strip():
        raise ValueError("Notification title is empty.")

    if backend is NotifyBackend.DESKTOP:
        send_desktop_notification(title, body, expire_ms=expire_ms)
        return
    if backend is NotifyBackend.WINDOWS:
        send_windows_notification(title, body)
        return
    raise ValueError(f"Unsupported notification backend: {backend}")
