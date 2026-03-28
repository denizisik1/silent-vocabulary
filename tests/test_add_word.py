import csv

import pytest

from words import (
    WordFields,
    add_word,
    format_word_row,
    get_random_words,
    remove_word,
    user_vocabulary_dir,
    vocabulary_dir,
)


def _prepare_dirs(tmp_path, monkeypatch) -> None:
    vocabulary_root = tmp_path / "vocabulary"
    vocabulary_root.mkdir()
    for filename in ("nouns.csv", "verbs.csv", "adjectives.csv", "adverbs.csv"):
        (vocabulary_root / filename).write_text("word,meaning\n", encoding="utf-8")
    user_root = tmp_path / "user-vocabulary"
    monkeypatch.setenv("VIPA_VOCABULARY_DIR", str(vocabulary_root))
    monkeypatch.setenv("VIPA_USER_VOCABULARY_DIR", str(user_root))


def test_add_word_writes_user_overlay_not_base(tmp_path, monkeypatch):
    _prepare_dirs(tmp_path, monkeypatch)
    nouns_before = (vocabulary_dir() / "nouns.csv").read_text(encoding="utf-8")

    row = add_word(
        "german",
        WordFields(
            article="der",
            word="Abend",
            meaning="evening",
            pronunciation="[aːbənt]",
            classification="noun",
            source="manual",
            example="Am Abend.",
            translation="In the evening.",
            plural="Abende",
        ),
    )

    assert row == (
        "der",
        "Abend",
        "evening",
        "[aːbənt]",
        "noun",
        "manual",
        "Am Abend.",
        "In the evening.",
        "Abende",
    )
    assert (vocabulary_dir() / "nouns.csv").read_text(encoding="utf-8") == nouns_before

    additions_path = user_vocabulary_dir() / "german" / "additions.csv"
    assert additions_path.is_file()
    with additions_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["word"] == "Abend"
    assert rows[0]["source"] == "manual"
    assert rows[0]["plural"] == "Abende"

    words = get_random_words("german", 1)
    assert words[0] == row


def test_add_word_defaults_classification(tmp_path, monkeypatch):
    _prepare_dirs(tmp_path, monkeypatch)

    noun_row = add_word("german", WordFields(article="die", word="Zeit", meaning="time"))
    adverb_row = add_word("german", WordFields(word="schnell", meaning="quickly"))

    assert noun_row[4] == "noun"
    assert adverb_row[4] == "adverb"


def test_add_word_rejects_duplicates(tmp_path, monkeypatch):
    _prepare_dirs(tmp_path, monkeypatch)
    add_word("german", WordFields(article="der", word="Abend", meaning="evening"))

    with pytest.raises(ValueError, match="Word already exists"):
        add_word("german", WordFields(article="der", word="Abend", meaning="nightfall"))


def test_add_word_rejects_empty_word(tmp_path, monkeypatch):
    _prepare_dirs(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="Word input is empty"):
        add_word("german", WordFields(word="   "))


def test_remove_user_added_word(tmp_path, monkeypatch):
    _prepare_dirs(tmp_path, monkeypatch)
    add_word("german", WordFields(article="der", word="Abend", meaning="evening"))

    removed = remove_word("german", "Abend")

    assert removed == "Abend"
    with pytest.raises(FileNotFoundError):
        get_random_words("german", 1)
    assert not (user_vocabulary_dir() / "german" / "additions.csv").is_file()


def test_remove_base_word_uses_removals_overlay(tmp_path, monkeypatch):
    _prepare_dirs(tmp_path, monkeypatch)
    nouns_path = vocabulary_dir() / "nouns.csv"
    nouns_path.write_text("der Abend,evening\n", encoding="utf-8")
    nouns_before = nouns_path.read_text(encoding="utf-8")

    removed = remove_word("german", "Abend")

    assert removed == "Abend"
    assert nouns_path.read_text(encoding="utf-8") == nouns_before
    removals_path = user_vocabulary_dir() / "german" / "removals.csv"
    assert "Abend" in removals_path.read_text(encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        get_random_words("german", 1)


def test_readd_after_removing_base_word(tmp_path, monkeypatch):
    _prepare_dirs(tmp_path, monkeypatch)
    (vocabulary_dir() / "nouns.csv").write_text("der Abend,evening\n", encoding="utf-8")
    remove_word("german", "Abend")

    row = add_word(
        "german",
        WordFields(article="der", word="Abend", meaning="nightfall", source="user"),
    )

    assert row[0:3] == ("der", "Abend", "nightfall")
    assert row[5] == "user"
    words = get_random_words("german", 1)
    assert words[0][0:3] == ("der", "Abend", "nightfall")


def test_format_word_row_for_added_word():
    row = ("der", "Abend", "evening", None, "noun", None, None, None, None)

    assert format_word_row(row) == "der Abend - evening"
