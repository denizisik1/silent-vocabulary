from urllib.parse import urlsplit

from retrieve.service import RetrieveResult
from words import (
    PronunciationEntry,
    failure_entry_from_row,
    forget_failure_of_row,
    read_failure_entries,
    shipped_failures_path,
    shipped_pronunciations_path,
    upsert_failure_entry,
    upsert_pronunciation_entry,
)
from words.failures import rows_without_failures
from words.load import clear_word_cache
from words.parse import normalize_row


def pronunciation_entry_from_row(row: tuple, result: RetrieveResult) -> PronunciationEntry:
    article, word, _meaning, _pronunciation, classification = normalize_row(row)[:5]
    return PronunciationEntry(
        word=word,
        pronunciation=result.pronunciation,
        classification=classification,
        article=article,
        source=urlsplit(result.url).netloc or None,
    )


def save_pronunciation(language_key: str, row: tuple, result: RetrieveResult) -> None:
    entry = pronunciation_entry_from_row(row, result)
    upsert_pronunciation_entry(shipped_pronunciations_path(language_key), entry)
    forget_failure_of_row(shipped_failures_path(language_key), row)
    clear_word_cache()


def mark_word_failed(language_key: str, row: tuple, reason: str) -> None:
    entry = failure_entry_from_row(row, reason)
    upsert_failure_entry(shipped_failures_path(language_key), entry)


def words_without_marked_failures(
    language_key: str,
    rows: list[tuple],
) -> tuple[list[tuple], int]:
    ledger = shipped_failures_path(language_key)
    remaining = rows_without_failures(rows, read_failure_entries(ledger))
    return remaining, len(rows) - len(remaining)
