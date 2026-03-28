import csv
from dataclasses import dataclass
from pathlib import Path

from words.constants import CSV_COLUMNS, LANGUAGE_VOCABULARY_FILES, ROW_FIELD_COUNT
from words.load import clear_word_cache, load_addition_rows, load_base_rows, load_language_words
from words.parse import empty_field, normalize_row, read_removals, word_key
from words.paths import additions_path, removals_path, vocabulary_dir


@dataclass(frozen=True)
class WordFields:
    word: str
    article: str | None = None
    meaning: str | None = None
    pronunciation: str | None = None
    classification: str | None = None
    source: str | None = None
    example: str | None = None
    translation: str | None = None
    plural: str | None = None


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_csv_rows(path: Path, rows: list[tuple]) -> None:
    _ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            (
                article,
                word,
                meaning,
                pronunciation,
                classification,
                source,
                example,
                translation,
                plural,
            ) = normalize_row(row)
            writer.writerow(
                [
                    article or "",
                    word or "",
                    meaning or "",
                    pronunciation or "",
                    classification or "",
                    source or "",
                    example or "",
                    translation or "",
                    plural or "",
                ]
            )


def _append_addition_row(language_key: str, row: tuple) -> None:
    path = additions_path(language_key)
    existing = load_addition_rows(path)
    existing.append(row)
    _write_csv_rows(path, existing)


def _remove_addition_row(language_key: str, word: str) -> bool:
    path = additions_path(language_key)
    if not path.is_file():
        return False

    needle = word_key(word)
    existing = load_addition_rows(path)
    kept = [row for row in existing if word_key(row[1]) != needle]
    if len(kept) == len(existing):
        return False

    if kept:
        _write_csv_rows(path, kept)
    else:
        path.unlink(missing_ok=True)
    return True


def _base_has_word(language_key: str, word: str) -> bool:
    base_rows = load_base_rows(language_key, vocabulary_dir())
    needle = word_key(word)
    return any(word_key(row[1]) == needle for row in base_rows)


def _append_removal(language_key: str, word: str) -> None:
    path = removals_path(language_key)
    removals = read_removals(path)
    key = word_key(word)
    if key in removals:
        return

    _ensure_parent(path)
    write_header = not path.is_file() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if write_header:
            writer.writerow(["word"])
        writer.writerow([word])


def _clear_removal(language_key: str, word: str) -> None:
    path = removals_path(language_key)
    if not path.is_file():
        return

    needle = word_key(word)
    removals = read_removals(path)
    if needle not in removals:
        return

    remaining = sorted(key for key in removals if key != needle)
    if not remaining:
        path.unlink(missing_ok=True)
        return

    _ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["word"])
        for key in remaining:
            writer.writerow([key])


def _word_already_exists(language_key: str, word: str) -> bool:
    try:
        rows = load_language_words(language_key)
    except FileNotFoundError:
        return False
    needle = word_key(word)
    return any(word_key(row[1]) == needle for row in rows)


def _normalize_fields(fields: WordFields) -> WordFields:
    word = empty_field(fields.word)
    if word is None:
        raise ValueError("Word input is empty.")

    article = empty_field(fields.article)
    classification = empty_field(fields.classification)
    if classification is None:
        classification = "noun" if article else "adverb"

    return WordFields(
        word=word,
        article=article,
        meaning=empty_field(fields.meaning),
        pronunciation=empty_field(fields.pronunciation),
        classification=classification,
        source=empty_field(fields.source),
        example=empty_field(fields.example),
        translation=empty_field(fields.translation),
        plural=empty_field(fields.plural),
    )


def _row_from_fields(fields: WordFields) -> tuple:
    return (
        fields.article,
        fields.word,
        fields.meaning,
        fields.pronunciation,
        fields.classification,
        fields.source,
        fields.example,
        fields.translation,
        fields.plural,
    )


def add_word(language_key: str, fields: WordFields) -> tuple:
    if language_key not in LANGUAGE_VOCABULARY_FILES:
        raise ValueError(f"Unsupported language: {language_key}")

    normalized = _normalize_fields(fields)
    if _word_already_exists(language_key, normalized.word):
        raise ValueError(f"Word already exists: {normalized.word}")

    row = _row_from_fields(normalized)
    assert len(row) == ROW_FIELD_COUNT
    _append_addition_row(language_key, row)
    _clear_removal(language_key, normalized.word)
    clear_word_cache()
    return row


def remove_word(language_key: str, word: str) -> str:
    if language_key not in LANGUAGE_VOCABULARY_FILES:
        raise ValueError(f"Unsupported language: {language_key}")

    cleaned = empty_field(word)
    if cleaned is None:
        raise ValueError("Word input is empty.")

    if not _word_already_exists(language_key, cleaned):
        raise ValueError(f"Word not found: {cleaned}")

    _remove_addition_row(language_key, cleaned)
    if _base_has_word(language_key, cleaned):
        _append_removal(language_key, cleaned)

    clear_word_cache()
    return cleaned
