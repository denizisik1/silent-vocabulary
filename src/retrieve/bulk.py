import random
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from retrieve.service import RetrieveResult, SourceEndpoint, retrieve_ipa_with_attempts
from words.load import load_language_words
from words.parse import normalize_row, row_entry_key
from words.pronunciations import rows_missing_pronunciation

DEFAULT_DELAY_SECONDS = 3.0
DEFAULT_MAX_CONSECUTIVE_FAILURES = 10
MAX_BACKOFF_SECONDS = 300.0
_JITTER_RATIO = 0.25

SaveCallback = Callable[[tuple, RetrieveResult], None]
ReportCallback = Callable[[str], None]
SleepCallback = Callable[[float], None]


@dataclass(frozen=True)
class BulkSettings:
    primary: SourceEndpoint
    backup: SourceEndpoint
    attempts: Sequence[tuple[str, str]]
    delay_seconds: float = DEFAULT_DELAY_SECONDS
    max_consecutive_failures: int = DEFAULT_MAX_CONSECUTIVE_FAILURES


@dataclass
class BulkOutcome:
    total: int = 0
    saved: int = 0
    failed: int = 0
    stopped_early: bool = False


def rows_needing_pronunciation(language_key: str) -> list[tuple]:
    missing = rows_missing_pronunciation(load_language_words(language_key))
    return sorted(missing, key=row_entry_key)


def jittered_delay_seconds(delay_seconds: float) -> float:
    if delay_seconds <= 0:
        return 0.0
    lowest = delay_seconds * (1.0 - _JITTER_RATIO)
    highest = delay_seconds * (1.0 + _JITTER_RATIO)
    return random.uniform(lowest, highest)  # nosec B311


def failure_backoff_seconds(delay_seconds: float, consecutive_failures: int) -> float:
    if delay_seconds <= 0 or consecutive_failures < 1:
        return 0.0
    return min(delay_seconds * (2**consecutive_failures), MAX_BACKOFF_SECONDS)


def _describe_success(position: int, total: int, word: str, result: RetrieveResult) -> str:
    return (
        f"[{position}/{total}] {word} {result.pronunciation} "
        f"via {result.source_label}/{result.fetch_method}"
    )


def fetch_pronunciations(
    rows: Sequence[tuple],
    settings: BulkSettings,
    *,
    save: SaveCallback,
    report: ReportCallback,
    sleep: SleepCallback = time.sleep,
) -> BulkOutcome:
    outcome = BulkOutcome(total=len(rows))
    consecutive_failures = 0

    for position, row in enumerate(rows, start=1):
        if position > 1:
            sleep(jittered_delay_seconds(settings.delay_seconds))

        word = normalize_row(row)[1]
        try:
            result = retrieve_ipa_with_attempts(
                word=word,
                primary=settings.primary,
                backup=settings.backup,
                attempts=settings.attempts,
            )
        except (ValueError, RuntimeError, OSError) as error:
            consecutive_failures += 1
            outcome.failed += 1
            report(f"[{position}/{outcome.total}] {word} failed: {error}")
            if consecutive_failures >= settings.max_consecutive_failures:
                outcome.stopped_early = True
                report(f"Stopped after {consecutive_failures} failures in a row.")
                return outcome
            sleep(failure_backoff_seconds(settings.delay_seconds, consecutive_failures))
            continue

        consecutive_failures = 0
        save(row, result)
        outcome.saved += 1
        report(_describe_success(position, outcome.total, word, result))

    return outcome
