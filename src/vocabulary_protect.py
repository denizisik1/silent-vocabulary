import os
import stat
from pathlib import Path

from words.paths import vocabulary_dir


def base_vocabulary_files(root: Path | None = None) -> list[Path]:
    directory = vocabulary_dir() if root is None else root
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.csv") if path.is_file())


def is_writable(path: Path) -> bool:
    return os.access(path, os.W_OK)


def make_file_readonly(path: Path) -> bool:
    if not path.is_file():
        return False
    if not is_writable(path):
        return False
    mode = path.stat().st_mode
    path.chmod(mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
    return True


def make_file_user_writable(path: Path) -> bool:
    if not path.is_file():
        return False
    if is_writable(path):
        return False
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IWUSR)
    return True


def protect_base_vocabulary(root: Path | None = None) -> int:
    changed = 0
    for path in base_vocabulary_files(root):
        if make_file_readonly(path):
            changed += 1
    return changed


def unprotect_base_vocabulary(root: Path | None = None) -> int:
    changed = 0
    for path in base_vocabulary_files(root):
        if make_file_user_writable(path):
            changed += 1
    return changed


def apply_base_vocabulary_protection(enabled: bool, root: Path | None = None) -> int:
    if enabled:
        return protect_base_vocabulary(root)
    return unprotect_base_vocabulary(root)
