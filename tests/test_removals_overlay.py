import pytest

from words import WordFields, add_word, get_random_words, remove_word, user_vocabulary_dir
from words.parse import entry_key, is_entry_removed, read_removals

LAKE = ("der", "See", "lake", None, "noun", None, None, None, None)
SEA = ("die", "See", "sea", None, "noun", None, None, None, None)


def _write_removals(tmp_path, text):
    path = tmp_path / "removals.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_a_missing_file_removes_nothing(tmp_path):
    assert not read_removals(tmp_path / "removals.csv")


def test_a_removal_names_the_word_class_and_article(tmp_path):
    path = _write_removals(tmp_path, "word,classification,article\nSee,noun,der\n")

    assert read_removals(path) == {("see", "noun", "der")}


def test_a_removal_of_a_word_without_an_article_keeps_an_empty_article(tmp_path):
    path = _write_removals(tmp_path, "word,classification,article\nmelden,verb,\n")

    assert read_removals(path) == {("melden", "verb", "")}


def test_a_legacy_removal_of_a_bare_word_matches_any_entry(tmp_path):
    path = _write_removals(tmp_path, "word\nsee\n")
    removals = read_removals(path)

    assert removals == {("see", None, None)}
    assert is_entry_removed(LAKE, removals)
    assert is_entry_removed(SEA, removals)


def test_a_precise_removal_matches_only_its_own_entry(tmp_path):
    path = _write_removals(tmp_path, "word,classification,article\nSee,noun,der\n")
    removals = read_removals(path)

    assert is_entry_removed(LAKE, removals)
    assert not is_entry_removed(SEA, removals)


def test_blank_lines_and_the_header_are_ignored(tmp_path):
    path = _write_removals(tmp_path, "word,classification,article\n\nSee,noun,der\n\n")

    assert read_removals(path) == {entry_key("See", "noun", "der")}


@pytest.fixture(name="two_lakes")
def two_lakes_fixture(tmp_path, monkeypatch):
    vocabulary_root = tmp_path / "vocabulary"
    vocabulary_root.mkdir()
    (vocabulary_root / "nouns.csv").write_text("der See,lake\ndie See,sea\n", encoding="utf-8")
    for filename in ("verbs.csv", "adjectives.csv", "adverbs.csv"):
        (vocabulary_root / filename).write_text("", encoding="utf-8")
    monkeypatch.setenv("SILENT_VOCABULARY_DIR", str(vocabulary_root))
    monkeypatch.setenv("SILENT_VOCABULARY_USER_DIR", str(tmp_path / "user-vocabulary"))
    return user_vocabulary_dir() / "german" / "removals.csv"


def test_removing_both_entries_records_both(two_lakes):
    remove_word("german", "See", article="der")
    remove_word("german", "See", article="die")

    assert read_removals(two_lakes) == {("see", "noun", "der"), ("see", "noun", "die")}


def test_the_file_is_deleted_once_nothing_is_removed_any_more(two_lakes):
    remove_word("german", "See", article="der")
    add_word("german", WordFields(article="der", word="See", meaning="lake"))

    assert not two_lakes.is_file()


def test_a_legacy_removal_is_narrowed_when_one_entry_is_added_back(two_lakes):
    two_lakes.parent.mkdir(parents=True, exist_ok=True)
    two_lakes.write_text("word\nsee\n", encoding="utf-8")

    add_word("german", WordFields(article="der", word="See", meaning="lake"))

    assert read_removals(two_lakes) == {("see", "noun", "die")}
    assert [row[2] for row in get_random_words("german", 1)] == ["lake"]
