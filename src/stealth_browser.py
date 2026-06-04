import os
import shutil
import subprocess
from pathlib import Path

_CHROME_NAMES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "chrome",
    "brave-browser",
    "brave",
)


def _configured_browser_path() -> str | None:
    configured = os.environ.get("VIPA_STEALTH_BROWSER_PATH", "").strip()
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


def browser_install_command() -> list[str] | None:
    release = read_os_release()
    os_id = release.get("ID", "").lower()
    like = release.get("ID_LIKE", "").lower()
    if os_id in {"fedora", "rhel", "centos"} or "fedora" in like or "rhel" in like:
        return ["pkexec", "dnf", "install", "-y", "chromium"]
    if os_id in {"debian", "ubuntu"} or "debian" in like or "ubuntu" in like:
        return ["pkexec", "apt-get", "install", "-y", "chromium"]
    if os_id in {"arch", "manjaro"} or "arch" in like:
        return ["pkexec", "pacman", "-S", "--noconfirm", "chromium"]
    return None


def install_stealth_browser() -> None:
    command = browser_install_command()
    if command is None:
        raise RuntimeError(
            "No automatic browser install is available for this system. "
            "Install Chrome, Chromium, or Brave, or set VIPA_STEALTH_BROWSER_PATH."
        )
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return
    detail = (completed.stderr or completed.stdout or "browser install failed").strip()
    raise RuntimeError(detail)
