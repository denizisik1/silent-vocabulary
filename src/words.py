import csv
import os
import random
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VOCABULARY_DIR = PROJECT_ROOT / "vocabulary"

CSV_COLUMNS = (
    "article",
    "word",
    "meaning",
    "pronunciation",
    "classification",
    "source",
    "example",
    "translation",
    "plural",
)

DISPLAY_COLUMNS = (
    "article",
    "word",
    "meaning",
    "pronunciation",
    "example",
    "translation",
    "plural",
)

DEFAULT_INCLUDE = {
    "article": True,
    "word": True,
    "meaning": True,
    "pronunciation": True,
    "example": False,
    "translation": False,
    "plural": False,
}

LANGUAGE_VOCABULARY_FILES = {
    "german": {
        "nouns.csv": "noun",
        "verbs.csv": "verb",
        "adjectives.csv": "adjective",
        "adverbs.csv": "adverb",
    },
}

ARTICLE_PREFIXES = (
    "der/die",
    "der",
    "die",
    "das",
    "dem",
    "den",
    "des",
    "ein",
    "eine",
)

HEADER_ALIASES = {
    "article": "article",
    "word": "word",
    "meaning": "meaning",
    "pronunciation": "pronunciation",
    "classification": "classification",
    "source": "source",
    "example": "example",
    "translation": "translation",
    "plural": "plural",
}


def vocabulary_dir() -> Path:
    override = os.environ.get("VIPA_VOCABULARY_DIR")
    if override:
        return Path(override)
    return VOCABULARY_DIR


def _empty_field(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped


def _split_article(word_field: str) -> tuple[str | None, str]:
    text = word_field.strip()
    for prefix in ARTICLE_PREFIXES:
        prefix_with_space = f"{prefix} "
        if text.startswith(prefix_with_space):
            return prefix, text[len(prefix_with_space) :]
    return None, text


def _row_from_mapping(values: dict[str, str | None], default_classification: str) -> tuple | None:
    article = _empty_field(values.get("article"))
    word = _empty_field(values.get("word"))
    meaning = _empty_field(values.get("meaning"))
    if word is None:
        return None

    if article is None and word:
        article, word = _split_article(word)

    pronunciation = _empty_field(values.get("pronunciation"))
    classification = _empty_field(values.get("classification")) or default_classification
    example = _empty_field(values.get("example"))
    translation = _empty_field(values.get("translation"))
    plural = _empty_field(values.get("plural"))
    return (
        article,
        word,
        meaning,
        pronunciation,
        classification,
        example,
        translation,
        plural,
    )


def _legacy_row(word_field: str, meaning_field: str, default_classification: str) -> tuple | None:
    return _row_from_mapping(
        {
            "word": word_field,
            "meaning": meaning_field,
        },
        default_classification,
    )


def _is_header_row(row: list[str]) -> bool:
    if not row:
        return False
    first_cell = row[0].strip().lower()
    return first_cell in HEADER_ALIASES or first_cell == "word"


def _normalize_header_row(row: list[str]) -> list[str]:
    return [cell.strip().lower() for cell in row]


def _read_csv_rows(path: Path, default_classification: str) -> list[tuple]:
    rows: list[tuple] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header_names: list[str] | None = None

        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue

            if header_names is None and _is_header_row(row):
                header_names = _normalize_header_row(row)
                continue

            if header_names is not None:
                values = {
                    header_names[index]: _empty_field(row[index])
                    for index in range(min(len(header_names), len(row)))
                }
                parsed = _row_from_mapping(values, default_classification)
            elif len(row) >= 2:
                parsed = _legacy_row(row[0], row[1], default_classification)
            else:
                continue

            if parsed is not None:
                rows.append(parsed)

    return rows


@lru_cache(maxsize=8)
def _load_language_words_cached(language_key: str, vocabulary_root: str) -> tuple[tuple, ...]:
    vocabulary_files = LANGUAGE_VOCABULARY_FILES.get(language_key)
    if vocabulary_files is None:
        raise ValueError(f"Unsupported language: {language_key}")

    rows: list[tuple] = []
    root = Path(vocabulary_root)
    for filename, default_classification in vocabulary_files.items():
        path = root / filename
        if not path.is_file():
            continue
        rows.extend(_read_csv_rows(path, default_classification))

    if not rows:
        raise FileNotFoundError(f"No vocabulary rows found for language: {language_key}")

    return tuple(rows)


def get_random_words(language_key: str, count: int) -> list[tuple]:
    if count < 1:
        raise ValueError("Count must be at least 1.")

    words = list(_load_language_words_cached(language_key, str(vocabulary_dir())))
    if count > len(words):
        raise ValueError(f"Count must be at most {len(words)}.")
    return random.sample(words, count)


def _normalize_row(row: tuple) -> tuple:
    padded = row + (None,) * (8 - len(row))
    return padded[:8]


def format_word_row(row: tuple, include: dict[str, bool] | None = None) -> str:
    (
        article,
        word,
        meaning,
        pronunciation,
        _classification,
        example,
        translation,
        plural,
    ) = _normalize_row(row)
    flags = DEFAULT_INCLUDE if include is None else include

    head_parts: list[str] = []
    if flags.get("article") and article:
        head_parts.append(article)
    if flags.get("word") and word:
        head_parts.append(word)

    line = " ".join(head_parts)
    if flags.get("meaning") and meaning:
        line = f"{line} - {meaning}" if line else meaning
    if flags.get("pronunciation") and pronunciation:
        line = f"{line} ({pronunciation})" if line else pronunciation
    if flags.get("plural") and plural:
        line = f"{line} [pl. {plural}]" if line else f"[pl. {plural}]"
    if flags.get("example") and example:
        line = f"{line}; e.g. {example}" if line else example
    if flags.get("translation") and translation:
        line = f"{line}; tr. {translation}" if line else translation
    return line
