import random
import time
from collections.abc import Callable, Sequence
from contextlib import nullcontext
from dataclasses import dataclass

from retrieve.browser_session import reused_browser_session
from retrieve.progress import (
    KIND_BAD,
    KIND_GOOD,
    KIND_HEADER,
    ReportCallback,
    retrieve_reporter,
)
from retrieve.service import RetrieveResult, SourceEndpoint, retrieve_ipa_with_attempts
from retrieve.strategy import FETCH_METHOD_BROWSER
from words.load import load_language_words
from words.parse import normalize_row, row_entry_key
from words.pronunciations import rows_missing_pronunciation

DEFAULT_DELAY_SECONDS = 3.0
DEFAULT_MAX_CONSECUTIVE_FAILURES = 10
MAX_BACKOFF_SECONDS = 300.0
_JITTER_RATIO = 0.25

SaveCallback = Callable[[tuple, RetrieveResult], None]
FailCallback = Callable[[tuple, str], None]
SleepCallback = Callable[[float], None]


@dataclass(frozen=True)
class BulkSettings:
    primary: SourceEndpoint
    backup: SourceEndpoint
    attempts: Sequence[tuple[str, str]]
    delay_seconds: float = DEFAULT_DELAY_SECONDS
    max_consecutive_failures: int = DEFAULT_MAX_CONSECUTIVE_FAILURES
    backoff_on_failure: bool = True


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


def wants_browser(settings: BulkSettings) -> bool:
    return any(fetch_method == FETCH_METHOD_BROWSER for _label, fetch_method in settings.attempts)


def fetch_pronunciations(  # pylint: disable=too-many-arguments
    rows: Sequence[tuple],
    settings: BulkSettings,
    *,
    save: SaveCallback,
    fail: FailCallback,
    report: ReportCallback,
    sleep: SleepCallback = time.sleep,
) -> BulkOutcome:
    keep_browser_open = reused_browser_session() if wants_browser(settings) else nullcontext()
    with keep_browser_open, retrieve_reporter(report):
        return _fetch_every_row(rows, settings, save=save, fail=fail, report=report, sleep=sleep)


def _fetch_every_row(  # pylint: disable=too-many-arguments
    rows: Sequence[tuple],
    settings: BulkSettings,
    *,
    save: SaveCallback,
    fail: FailCallback,
    report: ReportCallback,
    sleep: SleepCallback,
) -> BulkOutcome:
    outcome = BulkOutcome(total=len(rows))
    consecutive_failures = 0

    for position, row in enumerate(rows, start=1):
        if position > 1:
            sleep(jittered_delay_seconds(settings.delay_seconds))

        word = normalize_row(row)[1]
        report(f"[{position}/{outcome.total}] {word}", KIND_HEADER)
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
            fail(row, str(error))
            report(f"no pronunciation for {word}, marked to be skipped next time", KIND_BAD)
            if consecutive_failures >= settings.max_consecutive_failures:
                outcome.stopped_early = True
                report(f"stopped after {consecutive_failures} failures in a row", KIND_BAD)
                return outcome
            if settings.backoff_on_failure:
                sleep(failure_backoff_seconds(settings.delay_seconds, consecutive_failures))
            continue

        consecutive_failures = 0
        save(row, result)
        outcome.saved += 1
        report(f"saved {word} {result.pronunciation} from {result.source_label}", KIND_GOOD)

    return outcome
