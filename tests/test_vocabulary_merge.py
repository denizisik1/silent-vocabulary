import pytest

from words.load import load_base_rows, merge_vocabulary_rows
from words.parse import entry_key

ABEND = ("der", "Abend", "evening", None, "noun", None, None, None, None)
ZEIT = ("die", "Zeit", "time", None, "noun", None, None, None, None)
ABEND_WITH_IPA = ("der", "Abend", "evening", "[ˈaːbənt]", "noun", "pons", None, None, None)

LAKE = ("der", "See", "lake", None, "noun", None, None, None, None)
SEA = ("die", "See", "sea", None, "noun", None, None, None, None)


def words_in(rows):
    return [row[1] for row in rows]


def test_base_rows_are_kept_when_nothing_overrides_them():
    merged = merge_vocabulary_rows([ABEND, ZEIT], [], set())

    assert merged == [ABEND, ZEIT]


def test_a_removal_hides_a_base_entry():
    merged = merge_vocabulary_rows([ABEND, ZEIT], [], {entry_key("Abend", "noun", "der")})

    assert words_in(merged) == ["Zeit"]


def test_an_addition_replaces_the_base_entry_for_the_same_word():
    merged = merge_vocabulary_rows([ABEND, ZEIT], [ABEND_WITH_IPA], set())

    assert merged == [ABEND_WITH_IPA, ZEIT]


def test_an_addition_survives_a_removal_of_the_same_entry():
    removals = {entry_key("Abend", "noun", "der")}

    merged = merge_vocabulary_rows([ABEND], [ABEND_WITH_IPA], removals)

    assert merged == [ABEND_WITH_IPA]


def test_entries_are_matched_without_regard_to_case():
    shouting = ("DER", "ABEND", "evening", None, "NOUN", None, None, None, None)

    assert merge_vocabulary_rows([ABEND], [shouting], set()) == [shouting]
    assert not merge_vocabulary_rows([shouting], [], {entry_key("abend", "noun", "der")})


def test_homographs_of_different_word_classes_both_survive():
    noun = ("der", "Arm", "arm", None, "noun", None, None, None, None)
    adjective = (None, "arm", "poor", None, "adjective", None, None, None, None)

    merged = merge_vocabulary_rows([noun, adjective], [], set())

    assert merged == [noun, adjective]


def test_nouns_that_differ_only_by_article_both_survive():
    merged = merge_vocabulary_rows([LAKE, SEA], [], set())

    assert merged == [LAKE, SEA]


def test_a_removal_hides_only_the_entry_it_names():
    merged = merge_vocabulary_rows([LAKE, SEA], [], {entry_key("See", "noun", "der")})

    assert merged == [SEA]


def test_a_legacy_removal_without_a_word_class_hides_every_entry_for_that_word():
    merged = merge_vocabulary_rows([LAKE, SEA], [], {("see", None, None)})

    assert not merged


def test_an_addition_only_replaces_the_entry_with_the_same_identity():
    louder_sea = ("die", "See", "sea", "[zeː]", "noun", "pons", None, None, None)

    merged = merge_vocabulary_rows([LAKE, SEA], [louder_sea], set())

    assert merged == [LAKE, louder_sea]


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
