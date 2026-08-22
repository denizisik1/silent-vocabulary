import os
from pathlib import Path

from words.constants import PRONUNCIATIONS_DIR_NAME, USER_VOCABULARY_DIR, VOCABULARY_DIR


def vocabulary_dir() -> Path:
    override = os.environ.get("SILENT_VOCABULARY_DIR")
    if override:
        return Path(override)
    return VOCABULARY_DIR


def user_vocabulary_dir() -> Path:
    override = os.environ.get("SILENT_VOCABULARY_USER_DIR")
    if override:
        return Path(override)
    return USER_VOCABULARY_DIR


def language_user_dir(language_key: str) -> Path:
    return user_vocabulary_dir() / language_key


def additions_path(language_key: str) -> Path:
    return language_user_dir(language_key) / "additions.csv"


def removals_path(language_key: str) -> Path:
    return language_user_dir(language_key) / "removals.csv"


def shipped_pronunciations_path(language_key: str, vocabulary_root: Path | None = None) -> Path:
    root = vocabulary_dir() if vocabulary_root is None else vocabulary_root
    return root / PRONUNCIATIONS_DIR_NAME / f"{language_key}.csv"


def shipped_failures_path(language_key: str, vocabulary_root: Path | None = None) -> Path:
    root = vocabulary_dir() if vocabulary_root is None else vocabulary_root
    return root / PRONUNCIATIONS_DIR_NAME / f"{language_key}-failures.csv"


def project_pronunciation_dir(project_root: Path) -> Path:
    return project_root / VOCABULARY_DIR.name / "pronunciation"


def _file_line_count(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            return sum(1 for _line in handle)
    except OSError:
        return 0


def pronunciation_files_line_count(project_root: Path) -> int:
    directory = project_pronunciation_dir(project_root)
    if not directory.is_dir():
        return 0
    total = 0
    for path in directory.rglob("*"):
        if path.is_file():
            total += _file_line_count(path)
    return total
