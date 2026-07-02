import csv
from dataclasses import dataclass
from pathlib import Path

from words.constants import (
    CSV_COLUMNS,
    LANGUAGE_VOCABULARY_FILES,
    REMOVAL_COLUMNS,
    ROW_FIELD_COUNT,
)
from words.load import clear_word_cache, load_addition_rows, load_base_rows, load_language_words
from words.lookup import describe_entry, resolve_entry
from words.parse import (
    RemovalKey,
    empty_field,
    normalize_row,
    read_removals,
    row_entry_key,
)
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


def _remove_addition_row(language_key: str, key: tuple[str, str, str]) -> bool:
    path = additions_path(language_key)
    if not path.is_file():
        return False

    existing = load_addition_rows(path)
    kept = [row for row in existing if row_entry_key(row) != key]
    if len(kept) == len(existing):
        return False

    if kept:
        _write_csv_rows(path, kept)
    else:
        path.unlink(missing_ok=True)
    return True


def _base_entry_keys(language_key: str) -> list[tuple[str, str, str]]:
    return [row_entry_key(row) for row in load_base_rows(language_key, vocabulary_dir())]


def _write_removals(path: Path, removals: set[RemovalKey]) -> None:
    if not removals:
        path.unlink(missing_ok=True)
        return

    _ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(REMOVAL_COLUMNS)
        for word, classification, article in sorted(
            removals, key=lambda removal: tuple(part or "" for part in removal)
        ):
            writer.writerow([word, classification or "", article or ""])


def _append_removal(language_key: str, key: tuple[str, str, str]) -> None:
    path = removals_path(language_key)
    removals = read_removals(path)
    if key in removals:
        return
    _write_removals(path, removals | {key})


def _clear_removal(language_key: str, key: tuple[str, str, str]) -> None:
    path = removals_path(language_key)
    if not path.is_file():
        return

    removals = read_removals(path)
    wildcard: RemovalKey = (key[0], None, None)
    remaining = {removal for removal in removals if removal not in (key, wildcard)}
    if wildcard in removals:
        remaining.update(
            base_key
            for base_key in _base_entry_keys(language_key)
            if base_key[0] == key[0] and base_key != key
        )
    if remaining != removals:
        _write_removals(path, remaining)


def _entry_exists(language_key: str, key: tuple[str, str, str]) -> bool:
    try:
        rows = load_language_words(language_key)
    except (FileNotFoundError, ValueError):
        return False
    return any(row_entry_key(row) == key for row in rows)


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


def _require_language(language_key: str) -> None:
    if language_key not in LANGUAGE_VOCABULARY_FILES:
        raise ValueError(f"Unsupported language: {language_key}")


def add_word(language_key: str, fields: WordFields) -> tuple:
    _require_language(language_key)

    normalized = _normalize_fields(fields)
    row = _row_from_fields(normalized)
    assert len(row) == ROW_FIELD_COUNT

    key = row_entry_key(row)
    if _entry_exists(language_key, key):
        raise ValueError(f"Word already exists: {describe_entry(row)}")

    _append_addition_row(language_key, row)
    _clear_removal(language_key, key)
    clear_word_cache()
    return row


def upsert_pronunciation(
    language_key: str,
    word: str,
    pronunciation: str,
    *,
    classification: str | None = None,
    article: str | None = None,
    source: str | None = None,
) -> tuple:
    _require_language(language_key)

    cleaned_pronunciation = empty_field(pronunciation)
    if cleaned_pronunciation is None:
        raise ValueError("Pronunciation is empty.")

    existing = resolve_entry(
        language_key,
        word,
        classification=classification,
        article=article,
    )
    (
        existing_article,
        existing_word,
        meaning,
        _old_pronunciation,
        existing_classification,
        old_source,
        example,
        translation,
        plural,
    ) = normalize_row(existing)

    row = (
        existing_article,
        existing_word,
        meaning,
        cleaned_pronunciation,
        existing_classification,
        empty_field(source) or old_source,
        example,
        translation,
        plural,
    )
    key = row_entry_key(row)
    _remove_addition_row(language_key, key)
    _append_addition_row(language_key, row)
    _clear_removal(language_key, key)
    clear_word_cache()
    return row


def remove_word(
    language_key: str,
    word: str,
    *,
    classification: str | None = None,
    article: str | None = None,
) -> tuple:
    _require_language(language_key)

    existing = resolve_entry(
        language_key,
        word,
        classification=classification,
        article=article,
    )
    key = row_entry_key(existing)

    _remove_addition_row(language_key, key)
    if key in _base_entry_keys(language_key):
        _append_removal(language_key, key)

    clear_word_cache()
    return existing
