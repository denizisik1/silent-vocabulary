# pylint: disable=wrong-import-position,wrong-import-order
import argparse
import sys
from functools import partial
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from config import load_config  # noqa: E402
from retrieve.bulk import (  # noqa: E402
    DEFAULT_DELAY_SECONDS,
    DEFAULT_MAX_CONSECUTIVE_FAILURES,
    BulkSettings,
    fetch_pronunciations,
    rows_needing_pronunciation,
)
from retrieve.service import RetrieveResult  # noqa: E402
from retrieve.sources import backup_endpoint, primary_endpoint  # noqa: E402
from retrieve.strategy import (  # noqa: E402
    RETRIEVE_STRATEGIES,
    basic_attempts_only,
    normalize_retrieve_strategy,
    retrieve_attempt_order,
)
from words import (  # noqa: E402
    PronunciationEntry,
    shipped_pronunciations_path,
    upsert_pronunciation_entry,
)
from words.constants import LANGUAGE_VOCABULARY_FILES  # noqa: E402
from words.load import clear_word_cache  # noqa: E402
from words.lookup import describe_entry  # noqa: E402
from words.parse import normalize_row  # noqa: E402


def _entry_from_row(row: tuple, result: RetrieveResult) -> PronunciationEntry:
    article, word, _meaning, _pronunciation, classification = normalize_row(row)[:5]
    return PronunciationEntry(
        word=word,
        pronunciation=result.pronunciation,
        classification=classification,
        article=article,
        source=urlsplit(result.url).netloc or None,
    )


def save_to_repository(language_key: str, row: tuple, result: RetrieveResult) -> None:
    entry = _entry_from_row(row, result)
    upsert_pronunciation_entry(shipped_pronunciations_path(language_key), entry)
    clear_word_cache()


def _report(message: str) -> None:
    print(message, flush=True)


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
        help="Allow the headless browser when a plain HTTP request is not enough. Slow.",
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
    )


def _print_words(rows: list[tuple]) -> None:
    for row in rows:
        print(describe_entry(row))
    print(f"{len(rows)} words need a pronunciation.")


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    config = load_config()

    rows = rows_needing_pronunciation(arguments.language)
    if arguments.limit is not None:
        rows = rows[: arguments.limit]

    if not rows:
        print("Every word already has a pronunciation.")
        return 0

    if arguments.dry_run:
        _print_words(rows)
        return 0

    strategy = normalize_retrieve_strategy(arguments.strategy or config.retrieve_strategy)
    destination = shipped_pronunciations_path(arguments.language)
    print(f"{len(rows)} words need a pronunciation. Writing to {destination}")

    try:
        outcome = fetch_pronunciations(
            rows,
            bulk_settings_from_arguments(arguments, strategy),
            save=partial(save_to_repository, arguments.language),
            report=_report,
        )
    except KeyboardInterrupt:
        print("\nInterrupted. Every pronunciation fetched so far is saved.")
        return 1

    print(f"Saved {outcome.saved}, failed {outcome.failed}, of {outcome.total}.")
    if outcome.stopped_early:
        print("Wait a while, then run the command again to carry on where it stopped.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
