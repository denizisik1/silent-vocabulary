import pytest

from words import CSV_COLUMNS, LANGUAGE_VOCABULARY_FILES, get_random_words, vocabulary_dir
from words.load import load_base_rows
from words.parse import word_key

GERMAN_FILES = LANGUAGE_VOCABULARY_FILES["german"]
CLASSIFICATIONS = set(GERMAN_FILES.values())
SHIPPED_ROWS = load_base_rows("german", vocabulary_dir())


def test_every_shipped_file_of_a_supported_language_is_present():
    missing = [name for name in GERMAN_FILES if not (vocabulary_dir() / name).is_file()]

    assert missing == []


def test_shipped_rows_have_a_word_and_a_known_classification():
    assert SHIPPED_ROWS

    for row in SHIPPED_ROWS:
        assert len(row) == len(CSV_COLUMNS)
        assert row[1] and row[1].strip() == row[1]
        assert row[4] in CLASSIFICATIONS


def test_shipped_pronunciations_are_bracketed():
    malformed = [
        row[1]
        for row in SHIPPED_ROWS
        if row[3] is not None and not (row[3].startswith("[") and row[3].endswith("]"))
    ]

    assert malformed == []


def test_optional_fields_are_absent_rather_than_blank():
    for row in SHIPPED_ROWS:
        for value in row:
            assert value is None or value.strip()


def test_random_words_come_from_the_shipped_list():
    words = get_random_words("german", 5)
    shipped_keys = {word_key(row[1]) for row in SHIPPED_ROWS}

    assert len(words) == 5
    assert len({word_key(row[1]) for row in words}) == 5
    assert {word_key(row[1]) for row in words} <= shipped_keys


def test_requesting_more_words_than_exist_is_rejected():
    too_many = len(SHIPPED_ROWS) + 1

    with pytest.raises(ValueError, match="Count must be at most"):
        get_random_words("german", too_many)


def test_header_and_legacy_csv_layouts_load_the_same_way(tmp_path, monkeypatch):
    vocabulary_root = tmp_path / "vocabulary"
    vocabulary_root.mkdir()
    (vocabulary_root / "nouns.csv").write_text(
        ",".join(CSV_COLUMNS) + "\n"
        "der,Abend,evening,[aːbənt],noun,wiki,Am Abend.,In the evening.,Abende\n",
        encoding="utf-8",
    )
    (vocabulary_root / "verbs.csv").write_text("die Zeit,time\n", encoding="utf-8")
    for filename in ("adjectives.csv", "adverbs.csv"):
        (vocabulary_root / filename).write_text("word,meaning\n", encoding="utf-8")
    monkeypatch.setenv("SILENT_VOCABULARY_DIR", str(vocabulary_root))
    monkeypatch.setenv("SILENT_VOCABULARY_USER_DIR", str(tmp_path / "user-vocabulary"))

    rows = sorted(get_random_words("german", 2), key=lambda row: row[1])

    assert rows[0] == (
        "der",
        "Abend",
        "evening",
        "[aːbənt]",
        "noun",
        "wiki",
        "Am Abend.",
        "In the evening.",
        "Abende",
    )
    assert rows[1] == ("die", "Zeit", "time", None, "verb", None, None, None, None)
