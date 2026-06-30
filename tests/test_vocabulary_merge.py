import pytest

from words.load import load_base_rows, merge_vocabulary_rows

ABEND = ("der", "Abend", "evening", None, "noun", None, None, None, None)
ZEIT = ("die", "Zeit", "time", None, "noun", None, None, None, None)
ABEND_WITH_IPA = ("der", "Abend", "evening", "[ˈaːbənt]", "noun", "pons", None, None, None)


def words_in(rows):
    return [row[1] for row in rows]


def test_base_rows_are_kept_when_nothing_overrides_them():
    merged = merge_vocabulary_rows([ABEND, ZEIT], [], set())

    assert merged == [ABEND, ZEIT]


def test_a_removal_hides_a_base_word():
    merged = merge_vocabulary_rows([ABEND, ZEIT], [], {"abend"})

    assert words_in(merged) == ["Zeit"]


def test_an_addition_replaces_the_base_entry_for_the_same_word():
    merged = merge_vocabulary_rows([ABEND, ZEIT], [ABEND_WITH_IPA], set())

    assert merged == [ABEND_WITH_IPA, ZEIT]


def test_an_addition_survives_a_removal_of_the_same_word():
    merged = merge_vocabulary_rows([ABEND], [ABEND_WITH_IPA], {"abend"})

    assert merged == [ABEND_WITH_IPA]


def test_words_are_matched_without_regard_to_case():
    shouting = ("der", "ABEND", "evening", None, "noun", None, None, None, None)

    assert merge_vocabulary_rows([ABEND], [shouting], set()) == [shouting]
    assert not merge_vocabulary_rows([shouting], [], {"abend"})


def test_only_one_entry_survives_per_word_regardless_of_word_class():
    noun = ("der", "Arm", "arm", None, "noun", None, None, None, None)
    adjective = (None, "arm", "poor", None, "adjective", None, None, None, None)

    merged = merge_vocabulary_rows([noun, adjective], [], set())

    assert merged == [adjective]


def test_base_rows_carry_the_word_class_of_their_file(tmp_path):
    (tmp_path / "nouns.csv").write_text("der Abend,evening\n", encoding="utf-8")
    (tmp_path / "verbs.csv").write_text("laufen,to run\n", encoding="utf-8")

    rows = load_base_rows("german", tmp_path)

    assert sorted((row[1], row[4]) for row in rows) == [("Abend", "noun"), ("laufen", "verb")]


def test_missing_files_are_skipped_rather_than_failing(tmp_path):
    (tmp_path / "nouns.csv").write_text("der Abend,evening\n", encoding="utf-8")

    assert words_in(load_base_rows("german", tmp_path)) == ["Abend"]


def test_an_unsupported_language_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unsupported language: french"):
        load_base_rows("french", tmp_path)
