import os
import shutil
import subprocess
from pathlib import Path

from stealth_config import get_stealth_config

_CHROME_NAMES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "chrome",
    "brave-browser",
    "brave",
)

_PACKAGE_BY_FAMILY = {
    "fedora": "chromium",
    "debian": "chromium",
    "arch": "chromium",
}


def _configured_browser_path() -> str | None:
    configured = get_stealth_config().browser_path.strip()
    if not configured:
        return None
    path = Path(configured)
    if path.is_file() and os.access(path, os.X_OK):
        return str(path.resolve())
    return None


def find_stealth_browser_path() -> str | None:
    configured = _configured_browser_path()
    if configured is not None:
        return configured

    for name in _CHROME_NAMES:
        found = shutil.which(name)
        if found:
            return found

    try:
        from zendriver.core.config import find_executable
    except ImportError:
        return None
    try:
        return str(find_executable("auto"))
    except (FileNotFoundError, ValueError, OSError):
        return None


def read_os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, raw = line.split("=", 1)
        values[key] = raw.strip().strip('"')
    return values


def _package_family() -> str | None:
    release = read_os_release()
    os_id = release.get("ID", "").lower()
    like = release.get("ID_LIKE", "").lower()
    if os_id in {"fedora", "rhel", "centos"} or "fedora" in like or "rhel" in like:
        return "fedora"
    if os_id in {"debian", "ubuntu"} or "debian" in like or "ubuntu" in like:
        return "debian"
    if os_id in {"arch", "manjaro"} or "arch" in like:
        return "arch"
    return None


def browser_install_command() -> list[str] | None:
    family = _package_family()
    if family == "fedora":
        return ["pkexec", "dnf", "install", "-y", _PACKAGE_BY_FAMILY["fedora"]]
    if family == "debian":
        return ["pkexec", "apt-get", "install", "-y", _PACKAGE_BY_FAMILY["debian"]]
    if family == "arch":
        return ["pkexec", "pacman", "-S", "--noconfirm", _PACKAGE_BY_FAMILY["arch"]]
    return None


def browser_remove_command() -> list[str] | None:
    family = _package_family()
    if family == "fedora":
        return ["pkexec", "dnf", "remove", "-y", _PACKAGE_BY_FAMILY["fedora"]]
    if family == "debian":
        return ["pkexec", "apt-get", "remove", "-y", _PACKAGE_BY_FAMILY["debian"]]
    if family == "arch":
        return ["pkexec", "pacman", "-R", "--noconfirm", _PACKAGE_BY_FAMILY["arch"]]
    return None


def _run_package_command(command: list[str], *, action: str) -> None:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return
    detail = (completed.stderr or completed.stdout or f"{action} failed").strip()
    raise RuntimeError(detail)


def install_stealth_browser() -> None:
    command = browser_install_command()
    if command is None:
        raise RuntimeError(
            "No automatic browser install is available for this system. "
            "Install Chrome, Chromium, or Brave, or set the browser path in Settings."
        )
    _run_package_command(command, action="browser install")


def remove_stealth_browser() -> None:
    command = browser_remove_command()
    if command is None:
        raise RuntimeError(
            "No automatic browser removal is available for this system. "
            "Uninstall Chrome, Chromium, or Brave with your package manager."
        )
    _run_package_command(command, action="browser remove")
