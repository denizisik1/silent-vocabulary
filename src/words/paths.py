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
