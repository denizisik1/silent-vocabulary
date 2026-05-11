import shutil
import subprocess
import sys
from pathlib import Path

_RED = "\033[31m"
_RESET = "\033[0m"


def _parse_env_entries(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key:
            entries[key] = value
    return entries


def _send_notification(title: str, body: str) -> None:
    if shutil.which("notify-send"):
        subprocess.run(
            [
                "notify-send",
                "--app-name=env-check",
                "--urgency=normal",
                title,
                body,
            ],
            check=False,
            capture_output=True,
        )
        return

    if not shutil.which("busctl"):
        return

    subprocess.run(
        [
            "busctl",
            "--user",
            "call",
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications",
            "org.freedesktop.Notifications",
            "Notify",
            "susssasa{sv}i",
            "env-check",
            "0",
            "",
            title,
            body,
            "0",
            "0",
            "10000",
        ],
        check=False,
        capture_output=True,
    )


def _warn(message: str) -> None:
    print(f"{_RED}{message}{_RESET}", file=sys.stderr)
    _send_notification(".env differs from .env.example", message)


def check_env_files(project_root: Path | None = None) -> bool:
    """Warn when `.env` and `.env.example` keys or values diverge.

    Returns True when both files define the same keys with the same values.
    """
    root = Path.cwd() if project_root is None else project_root
    env_path = root / ".env"
    example_path = root / ".env.example"

    if not example_path.is_file():
        return True

    if not env_path.is_file():
        _warn(
            f".env is missing at {env_path}. "
            "Copy .env.example to .env and adjust values."
        )
        return False

    env_entries = _parse_env_entries(env_path)
    example_entries = _parse_env_entries(example_path)
    env_keys = set(env_entries)
    example_keys = set(example_entries)

    missing_in_env = sorted(example_keys - env_keys)
    extra_in_env = sorted(env_keys - example_keys)
    changed_values = sorted(
        key
        for key in env_keys & example_keys
        if env_entries[key] != example_entries[key]
    )

    if not missing_in_env and not extra_in_env and not changed_values:
        return True

    parts = [".env and .env.example differ."]
    if missing_in_env:
        parts.append("Missing in .env: " + ", ".join(missing_in_env))
    if extra_in_env:
        parts.append("Only in .env: " + ", ".join(extra_in_env))
    if changed_values:
        parts.append("Different values: " + ", ".join(changed_values))
    _warn(" ".join(parts))
    return False
