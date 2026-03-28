import random
from functools import lru_cache
from pathlib import Path

from words.constants import LANGUAGE_VOCABULARY_FILES
from words.parse import read_csv_rows, read_removals, word_key
from words.paths import vocabulary_dir, user_vocabulary_dir


def load_base_rows(language_key: str, vocabulary_root: Path) -> list[tuple]:
    vocabulary_files = LANGUAGE_VOCABULARY_FILES.get(language_key)
    if vocabulary_files is None:
        raise ValueError(f"Unsupported language: {language_key}")

    rows: list[tuple] = []
    for filename, default_classification in vocabulary_files.items():
        path = vocabulary_root / filename
        if not path.is_file():
            continue
        rows.extend(read_csv_rows(path, default_classification))
    return rows


def load_addition_rows(path: Path) -> list[tuple]:
    if not path.is_file():
        return []
    return read_csv_rows(path, "adverb")


def merge_vocabulary_rows(
    base_rows: list[tuple],
    addition_rows: list[tuple],
    removals: set[str],
) -> list[tuple]:
    merged: dict[str, tuple] = {}
    for row in base_rows:
        key = word_key(row[1])
        if key in removals:
            continue
        merged[key] = row
    for row in addition_rows:
        merged[word_key(row[1])] = row
    return list(merged.values())


@lru_cache(maxsize=8)
def load_language_words_cached(
    language_key: str,
    vocabulary_root: str,
    user_root: str,
) -> tuple[tuple, ...]:
    if language_key not in LANGUAGE_VOCABULARY_FILES:
        raise ValueError(f"Unsupported language: {language_key}")

    language_user_dir = Path(user_root) / language_key
    base_rows = load_base_rows(language_key, Path(vocabulary_root))
    addition_rows = load_addition_rows(language_user_dir / "additions.csv")
    removals = read_removals(language_user_dir / "removals.csv")
    rows = merge_vocabulary_rows(base_rows, addition_rows, removals)

    if not rows:
        raise FileNotFoundError(f"No vocabulary rows found for language: {language_key}")

    return tuple(rows)


def clear_word_cache() -> None:
    load_language_words_cached.cache_clear()


def load_language_words(language_key: str) -> tuple[tuple, ...]:
    return load_language_words_cached(
        language_key,
        str(vocabulary_dir()),
        str(user_vocabulary_dir()),
    )


def get_random_words(language_key: str, count: int) -> list[tuple]:
    if count < 1:
        raise ValueError("Count must be at least 1.")

    words = list(load_language_words(language_key))
    if count > len(words):
        raise ValueError(f"Count must be at most {len(words)}.")
    return random.sample(words, count)
