import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from words.constants import PRONUNCIATION_COLUMNS
from words.parse import empty_field, entry_key, normalize_row, row_entry_key

PronunciationKey = tuple[str, str, str]


@dataclass(frozen=True)
class PronunciationEntry:
    word: str
    pronunciation: str
    classification: str | None = None
    article: str | None = None
    source: str | None = None


def pronunciation_entry_key(entry: PronunciationEntry) -> PronunciationKey:
    return entry_key(entry.word, entry.classification, entry.article)


def _entry_from_values(values: Mapping[str, str | None]) -> PronunciationEntry | None:
    word = empty_field(values.get("word"))
    pronunciation = empty_field(values.get("pronunciation"))
    if word is None or pronunciation is None:
        return None

    return PronunciationEntry(
        word=word,
        pronunciation=pronunciation,
        classification=empty_field(values.get("classification")),
        article=empty_field(values.get("article")),
        source=empty_field(values.get("source")),
    )


def read_pronunciation_entries(path: Path) -> list[PronunciationEntry]:
    if not path.is_file():
        return []

    entries: list[PronunciationEntry] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for values in csv.DictReader(handle):
            entry = _entry_from_values(values)
            if entry is not None:
                entries.append(entry)
    return entries


def write_pronunciation_entries(path: Path, entries: Iterable[PronunciationEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(PRONUNCIATION_COLUMNS)
        for entry in sorted(entries, key=pronunciation_entry_key):
            writer.writerow(
                [
                    entry.word,
                    entry.classification or "",
                    entry.article or "",
                    entry.pronunciation,
                    entry.source or "",
                ]
            )


def upsert_pronunciation_entry(path: Path, entry: PronunciationEntry) -> None:
    key = pronunciation_entry_key(entry)
    kept = [
        existing
        for existing in read_pronunciation_entries(path)
        if pronunciation_entry_key(existing) != key
    ]
    kept.append(entry)
    write_pronunciation_entries(path, kept)


def _row_with_pronunciation(row: tuple, entry: PronunciationEntry) -> tuple:
    (
        article,
        word,
        meaning,
        _old_pronunciation,
        classification,
        old_source,
        example,
        translation,
        plural,
    ) = normalize_row(row)
    return (
        article,
        word,
        meaning,
        entry.pronunciation,
        classification,
        entry.source or old_source,
        example,
        translation,
        plural,
    )


def apply_pronunciations(
    rows: Iterable[tuple],
    entries: Iterable[PronunciationEntry],
) -> list[tuple]:
    by_key = {pronunciation_entry_key(entry): entry for entry in entries}
    if not by_key:
        return list(rows)

    applied: list[tuple] = []
    for row in rows:
        entry = by_key.get(row_entry_key(row))
        if entry is None:
            applied.append(row)
            continue
        applied.append(_row_with_pronunciation(row, entry))
    return applied


def rows_missing_pronunciation(rows: Iterable[tuple]) -> list[tuple]:
    return [row for row in rows if normalize_row(row)[3] is None]
