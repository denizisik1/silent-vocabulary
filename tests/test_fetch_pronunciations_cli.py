import pytest

import fetch_pronunciations
from retrieve.service import RetrieveResult
from retrieve.strategy import retrieve_attempt_order
from words.load import load_language_words
from words.paths import shipped_pronunciations_path
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


def test_a_fetched_pronunciation_lands_in_the_shipped_file():
    fetch_pronunciations.save_to_repository("german", ABEND, ABEND_RESULT)

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
    fetch_pronunciations.save_to_repository("german", ABEND, ABEND_RESULT)

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
    fetch_pronunciations.save_to_repository("german", ABEND, ABEND_RESULT)

    exit_code = fetch_pronunciations.main(["german"])

    assert exit_code == 0
    assert "Every word already has a pronunciation." in capsys.readouterr().out
