import csv

import pytest

from words import (
    WordFields,
    add_word,
    get_random_words,
    remove_word,
    upsert_pronunciation,
    user_vocabulary_dir,
    vocabulary_dir,
)


@pytest.fixture(autouse=True)
def vocabulary_roots(tmp_path, monkeypatch):
    vocabulary_root = tmp_path / "vocabulary"
    vocabulary_root.mkdir()
    (vocabulary_root / "nouns.csv").write_text(
        "article,word,meaning,pronunciation,classification,source,example,translation,plural\n"
        "der,Abend,evening,,noun,duden,Am Abend.,In the evening.,Abende\n",
        encoding="utf-8",
    )
    for filename in ("verbs.csv", "adjectives.csv", "adverbs.csv"):
        (vocabulary_root / filename).write_text("word,meaning\n", encoding="utf-8")
    monkeypatch.setenv("SILENT_VOCABULARY_DIR", str(vocabulary_root))
    monkeypatch.setenv("SILENT_VOCABULARY_USER_DIR", str(tmp_path / "user-vocabulary"))


def additions_rows():
    path = user_vocabulary_dir() / "german" / "additions.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_a_pronunciation_for_a_shipped_word_lands_in_the_overlay():
    row = upsert_pronunciation("german", "Abend", "[ˈa:bn̩t]", source="pons")

    assert row[1] == "Abend"
    assert row[3] == "[ˈa:bn̩t]"
    assert row[5] == "pons"
    assert get_random_words("german", 1)[0][3] == "[ˈa:bn̩t]"


def test_the_shipped_file_is_never_rewritten():
    nouns_path = vocabulary_dir() / "nouns.csv"
    before = nouns_path.read_text(encoding="utf-8")

    upsert_pronunciation("german", "Abend", "[ˈa:bn̩t]", source="pons")

    assert nouns_path.read_text(encoding="utf-8") == before


def test_the_remaining_fields_of_the_word_survive():
    row = upsert_pronunciation("german", "Abend", "[ˈa:bn̩t]")

    assert row == (
        "der",
        "Abend",
        "evening",
        "[ˈa:bn̩t]",
        "noun",
        "duden",
        "Am Abend.",
        "In the evening.",
        "Abende",
    )


def test_a_second_pronunciation_replaces_the_first_instead_of_duplicating():
    upsert_pronunciation("german", "Abend", "[wrong]", source="pons")
    upsert_pronunciation("german", "Abend", "[ˈa:bn̩t]", source="collins")

    rows = additions_rows()
    assert len(rows) == 1
    assert rows[0]["pronunciation"] == "[ˈa:bn̩t]"
    assert rows[0]["source"] == "collins"


def test_a_user_added_word_keeps_its_own_fields():
    add_word("german", WordFields(article="die", word="Zeit", meaning="time"))

    row = upsert_pronunciation("german", "Zeit", "[tsaɪt]")

    assert row[0:4] == ("die", "Zeit", "time", "[tsaɪt]")
    assert len(additions_rows()) == 1


def test_matching_a_word_ignores_letter_case():
    row = upsert_pronunciation("german", "abend", "[ˈa:bn̩t]")

    assert row[1] == "Abend"


def test_a_removed_word_is_not_resurrected_by_a_pronunciation():
    remove_word("german", "Abend")

    with pytest.raises(ValueError, match="Word not found: Abend"):
        upsert_pronunciation("german", "Abend", "[ˈa:bn̩t]")


def test_an_unknown_word_is_rejected():
    with pytest.raises(ValueError, match="Word not found: Morgen"):
        upsert_pronunciation("german", "Morgen", "[ˈmɔʁɡn̩]")


def test_an_unsupported_language_is_rejected():
    with pytest.raises(ValueError, match="Unsupported language: french"):
        upsert_pronunciation("french", "soir", "[swaʁ]")


def test_blank_input_is_rejected():
    with pytest.raises(ValueError, match="Word input is empty"):
        upsert_pronunciation("german", "   ", "[ˈa:bn̩t]")

    with pytest.raises(ValueError, match="Pronunciation is empty"):
        upsert_pronunciation("german", "Abend", "   ")
