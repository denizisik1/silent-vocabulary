import pytest

import fetch_pronunciations
from browser_config import (
    FAST_BROWSER_WAIT_SECONDS,
    BrowserConfig,
    apply_browser_config,
    get_browser_config,
)
from pronunciation_repository import mark_word_failed, save_pronunciation
from retrieve.service import RetrieveResult
from retrieve.strategy import retrieve_attempt_order
from words.failures import FailureEntry, read_failure_entries, upsert_failure_entry
from words.load import load_language_words
from words.paths import shipped_failures_path, shipped_pronunciations_path
from words.pronunciations import PronunciationEntry, read_pronunciation_entries

ABEND = ("der", "Abend", "evening", None, "noun", None, None, None, None)
ABEND_RESULT = RetrieveResult(
    word="Abend",
    url="https://en.pons.com/translate/german-english/Abend",
    pronunciation="[ˈaːbənt]",
    source_label="primary",
)


@pytest.fixture(autouse=True)
def vocabulary_root(tmp_path, monkeypatch):
    root = tmp_path / "vocabulary"
    root.mkdir()
    (root / "nouns.csv").write_text("der Abend,evening\n", encoding="utf-8")
    monkeypatch.setenv("SILENT_VOCABULARY_DIR", str(root))
    return root


def test_a_fetched_pronunciation_lands_in_the_shipped_file():
    save_pronunciation("german", ABEND, ABEND_RESULT)

    entries = read_pronunciation_entries(shipped_pronunciations_path("german"))

    assert entries == [
        PronunciationEntry(
            word="Abend",
            pronunciation="[ˈaːbənt]",
            classification="noun",
            article="der",
            source="en.pons.com",
        )
    ]


def test_a_saved_pronunciation_shows_up_in_the_loaded_words():
    save_pronunciation("german", ABEND, ABEND_RESULT)

    rows = load_language_words("german")

    assert [row[3] for row in rows] == ["[ˈaːbənt]"]


def test_the_browser_is_skipped_unless_it_is_asked_for():
    arguments = fetch_pronunciations.parse_arguments(["german"])

    settings = fetch_pronunciations.bulk_settings_from_arguments(arguments, "primary_first")

    assert settings.attempts == [("primary", "basic"), ("backup", "basic")]


def test_the_browser_joins_the_attempts_when_it_is_asked_for():
    arguments = fetch_pronunciations.parse_arguments(["german", "--browser-fallback"])

    settings = fetch_pronunciations.bulk_settings_from_arguments(arguments, "primary_first")

    assert settings.attempts == retrieve_attempt_order("primary_first")


def test_nothing_is_fetched_when_every_word_already_has_a_pronunciation(capsys):
    save_pronunciation("german", ABEND, ABEND_RESULT)

    exit_code = fetch_pronunciations.main(["german"])

    assert exit_code == 0
    assert "Nothing left to fetch." in capsys.readouterr().out


def test_a_failed_word_is_written_to_the_ledger():
    mark_word_failed("german", ABEND, "primary/basic: HTTP 403")

    assert read_failure_entries(shipped_failures_path("german")) == [
        FailureEntry(
            word="Abend",
            classification="noun",
            article="der",
            reason="primary/basic: HTTP 403",
        )
    ]


def test_a_word_in_the_ledger_is_left_out_of_the_next_run(capsys):
    mark_word_failed("german", ABEND, "HTTP 403")

    exit_code = fetch_pronunciations.main(["german"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Skipping 1 word marked as failed" in output
    assert "Nothing left to fetch." in output


def test_the_ledger_is_ignored_when_the_run_asks_for_a_retry(capsys):
    mark_word_failed("german", ABEND, "HTTP 403")

    exit_code = fetch_pronunciations.main(["german", "--retry-failed", "--dry-run"])

    assert exit_code == 0
    assert "1 word to fetch." in capsys.readouterr().out


def test_a_pronunciation_that_arrives_later_clears_the_ledger():
    upsert_failure_entry(
        shipped_failures_path("german"),
        FailureEntry(word="Abend", classification="noun", article="der", reason="HTTP 403"),
    )

    save_pronunciation("german", ABEND, ABEND_RESULT)

    assert not read_failure_entries(shipped_failures_path("german"))


def test_fast_is_accepted_as_a_flag():
    arguments = fetch_pronunciations.parse_arguments(["german", "--fast"])
    settings = fetch_pronunciations.bulk_settings_from_arguments(arguments, "primary_first")

    assert arguments.fast is True
    assert settings.backoff_on_failure is False


def test_fast_caps_how_long_the_browser_stays_on_a_page():
    apply_browser_config(
        BrowserConfig(wait_seconds=90.0, extra_timeout_seconds=40.0, fetch_timeout_seconds=20.0)
    )
    arguments = fetch_pronunciations.parse_arguments(["german", "--fast"])
    try:
        browser = fetch_pronunciations.apply_run_overrides(get_browser_config(), arguments)
        assert browser.wait_seconds == FAST_BROWSER_WAIT_SECONDS
        assert browser.extra_timeout_seconds == 0.0
        assert browser.fetch_timeout_seconds == FAST_BROWSER_WAIT_SECONDS
        assert get_browser_config().wait_seconds == FAST_BROWSER_WAIT_SECONDS
    finally:
        apply_browser_config(BrowserConfig())


def test_fast_keeps_a_hidden_window_hidden():
    arguments = fetch_pronunciations.parse_arguments(["german", "--fast", "--headless"])
    try:
        browser = fetch_pronunciations.apply_run_overrides(
            BrowserConfig(headless=False, wait_seconds=90.0),
            arguments,
        )
        assert browser.headless is True
        assert browser.wait_seconds == FAST_BROWSER_WAIT_SECONDS
    finally:
        apply_browser_config(BrowserConfig())
