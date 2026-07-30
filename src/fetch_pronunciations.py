# pylint: disable=wrong-import-position,wrong-import-order  # .env must load first
import argparse
import sys
from dataclasses import replace
from functools import partial
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from browser_config import (
    FAST_BROWSER_WAIT_SECONDS,
    BrowserConfig,
    apply_browser_config,
)
from config import load_config
from retrieve.bulk import (
    DEFAULT_DELAY_SECONDS,
    DEFAULT_MAX_CONSECUTIVE_FAILURES,
    BulkOutcome,
    BulkSettings,
    fetch_pronunciations,
    rows_needing_pronunciation,
)
from retrieve.progress import KIND_BAD, KIND_GOOD, KIND_NOTE
from retrieve.sources import backup_endpoint, primary_endpoint
from retrieve.strategy import (
    RETRIEVE_STRATEGIES,
    basic_attempts_only,
    normalize_retrieve_strategy,
    retrieve_attempt_order,
)
from pronunciation_repository import (
    mark_word_failed,
    save_pronunciation,
    words_without_marked_failures,
)
from terminal_output import print_notice, print_progress
from words.constants import LANGUAGE_VOCABULARY_FILES
from words.lookup import describe_entry
from words.paths import shipped_failures_path, shipped_pronunciations_path


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch the missing IPA pronunciations of a language into the shipped "
            "pronunciation file, one word at a time."
        ),
    )
    parser.add_argument("language", choices=sorted(LANGUAGE_VOCABULARY_FILES))
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help="Seconds to wait between words, jittered by a quarter (default: %(default)s).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Fetch at most this many words, then stop.",
    )
    parser.add_argument(
        "--strategy",
        choices=sorted(RETRIEVE_STRATEGIES),
        default=None,
        help="Source order to try. Defaults to the strategy saved by the app.",
    )
    parser.add_argument(
        "--browser-fallback",
        action="store_true",
        help="Allow the browser when a source refuses the plain request. Slow.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Keep the browser window hidden, for a run you leave alone.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help=(
            "Give the browser a few seconds to find IPA, then move on. "
            "Skips the extra wait after a miss."
        ),
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Try the words marked as failed before, instead of skipping them.",
    )
    parser.add_argument(
        "--max-consecutive-failures",
        type=int,
        default=DEFAULT_MAX_CONSECUTIVE_FAILURES,
        help="Stop when this many words fail in a row (default: %(default)s).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List the words that need a pronunciation and exit.",
    )
    return parser.parse_args(argv)


def bulk_settings_from_arguments(arguments: argparse.Namespace, strategy: str) -> BulkSettings:
    attempts = retrieve_attempt_order(strategy)
    if not arguments.browser_fallback:
        attempts = basic_attempts_only(attempts)
    return BulkSettings(
        primary=primary_endpoint(),
        backup=backup_endpoint(),
        attempts=attempts,
        delay_seconds=arguments.delay,
        max_consecutive_failures=arguments.max_consecutive_failures,
        backoff_on_failure=not arguments.fast,
    )


def _word_count(count: int) -> str:
    return "1 word" if count == 1 else f"{count} words"


def _print_words(rows: list[tuple]) -> None:
    for row in rows:
        print(describe_entry(row))
    print_notice(f"{_word_count(len(rows))} to fetch.")


def _hide_browser_window(browser: BrowserConfig) -> BrowserConfig:
    if browser.headless:
        return browser
    return replace(browser, headless=True)


def shorten_browser_wait(browser: BrowserConfig) -> BrowserConfig:
    return replace(
        browser,
        wait_seconds=FAST_BROWSER_WAIT_SECONDS,
        extra_timeout_seconds=0.0,
        fetch_timeout_seconds=min(browser.fetch_timeout_seconds, FAST_BROWSER_WAIT_SECONDS),
    )


def apply_run_overrides(browser: BrowserConfig, arguments: argparse.Namespace) -> BrowserConfig:
    if arguments.headless:
        browser = _hide_browser_window(browser)
    if arguments.fast:
        browser = shorten_browser_wait(browser)
        print_notice(
            f"Fast: the browser waits up to {FAST_BROWSER_WAIT_SECONDS:.0f}s per page.",
            KIND_NOTE,
        )
    if arguments.headless or arguments.fast:
        apply_browser_config(browser)
    return browser


def words_to_fetch(arguments: argparse.Namespace) -> list[tuple]:
    rows = rows_needing_pronunciation(arguments.language)
    if not arguments.retry_failed:
        rows, skipped = words_without_marked_failures(arguments.language, rows)
        if skipped:
            ledger = shipped_failures_path(arguments.language)
            print_notice(f"Skipping {_word_count(skipped)} marked as failed in {ledger}", KIND_NOTE)
    if arguments.limit is None:
        return rows
    return rows[: arguments.limit]


def _report_outcome(outcome: BulkOutcome) -> None:
    kind = KIND_GOOD if outcome.failed == 0 else KIND_BAD
    print_notice(f"Saved {outcome.saved}, failed {outcome.failed}, of {outcome.total}.", kind)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    config = load_config()

    rows = words_to_fetch(arguments)
    if not rows:
        print_notice(
            "Nothing left to fetch. Every word has a pronunciation or is marked as failed."
        )
        return 0

    if arguments.dry_run:
        _print_words(rows)
        return 0

    apply_run_overrides(config.browser, arguments)

    strategy = normalize_retrieve_strategy(arguments.strategy or config.retrieve_strategy)
    destination = shipped_pronunciations_path(arguments.language)
    print_notice(f"Fetching {_word_count(len(rows))} into {destination}")

    try:
        outcome = fetch_pronunciations(
            rows,
            bulk_settings_from_arguments(arguments, strategy),
            save=partial(save_pronunciation, arguments.language),
            fail=partial(mark_word_failed, arguments.language),
            report=print_progress,
        )
    except KeyboardInterrupt:
        print_notice("\nInterrupted. Every pronunciation fetched so far is saved.", KIND_NOTE)
        return 1

    _report_outcome(outcome)
    if outcome.stopped_early:
        print_notice(
            "Wait a while, then run the command again to carry on where it stopped.", KIND_NOTE
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
