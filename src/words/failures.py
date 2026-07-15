import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from words.constants import FAILURE_COLUMNS
from words.parse import empty_field, entry_key, normalize_row, row_entry_key

FailureKey = tuple[str, str, str]


@dataclass(frozen=True)
class FailureEntry:
    word: str
    classification: str | None = None
    article: str | None = None
    reason: str | None = None


def failure_entry_key(entry: FailureEntry) -> FailureKey:
    return entry_key(entry.word, entry.classification, entry.article)


def _entry_from_values(values: Mapping[str, str | None]) -> FailureEntry | None:
    word = empty_field(values.get("word"))
    if word is None:
        return None

    return FailureEntry(
        word=word,
        classification=empty_field(values.get("classification")),
        article=empty_field(values.get("article")),
        reason=empty_field(values.get("reason")),
    )


def read_failure_entries(path: Path) -> list[FailureEntry]:
    if not path.is_file():
        return []

    entries: list[FailureEntry] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for values in csv.DictReader(handle):
            entry = _entry_from_values(values)
            if entry is not None:
                entries.append(entry)
    return entries


def write_failure_entries(path: Path, entries: Iterable[FailureEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(FAILURE_COLUMNS)
        for entry in sorted(entries, key=failure_entry_key):
            writer.writerow(
                [
                    entry.word,
                    entry.classification or "",
                    entry.article or "",
                    entry.reason or "",
                ]
            )


def _entries_without(path: Path, key: FailureKey) -> list[FailureEntry]:
    return [entry for entry in read_failure_entries(path) if failure_entry_key(entry) != key]


def upsert_failure_entry(path: Path, entry: FailureEntry) -> None:
    kept = _entries_without(path, failure_entry_key(entry))
    kept.append(entry)
    write_failure_entries(path, kept)


def forget_failure_of_row(path: Path, row: tuple) -> None:
    key = row_entry_key(row)
    if not any(failure_entry_key(entry) == key for entry in read_failure_entries(path)):
        return
    write_failure_entries(path, _entries_without(path, key))


def failure_entry_from_row(row: tuple, reason: str) -> FailureEntry:
    article, word, _meaning, _pronunciation, classification = normalize_row(row)[:5]
    return FailureEntry(
        word=word,
        classification=classification,
        article=article,
        reason=reason,
    )


def rows_without_failures(rows: Iterable[tuple], entries: Iterable[FailureEntry]) -> list[tuple]:
    marked = {failure_entry_key(entry) for entry in entries}
    if not marked:
        return list(rows)
    return [row for row in rows if row_entry_key(row) not in marked]
