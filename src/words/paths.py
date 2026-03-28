import os
from pathlib import Path

from words.constants import USER_VOCABULARY_DIR, VOCABULARY_DIR


def vocabulary_dir() -> Path:
    override = os.environ.get("VIPA_VOCABULARY_DIR")
    if override:
        return Path(override)
    return VOCABULARY_DIR


def user_vocabulary_dir() -> Path:
    override = os.environ.get("VIPA_USER_VOCABULARY_DIR")
    if override:
        return Path(override)
    return USER_VOCABULARY_DIR


def language_user_dir(language_key: str) -> Path:
    return user_vocabulary_dir() / language_key


def additions_path(language_key: str) -> Path:
    return language_user_dir(language_key) / "additions.csv"


def removals_path(language_key: str) -> Path:
    return language_user_dir(language_key) / "removals.csv"
