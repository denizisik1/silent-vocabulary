import pytest

from words import AmbiguousWordError, describe_entry, find_word_entries, resolve_entry

pytestmark = pytest.mark.usefixtures("homographs")


def _prepare_vocabulary(tmp_path, monkeypatch, files) -> None:
    vocabulary_root = tmp_path / "vocabulary"
    vocabulary_root.mkdir()
    for filename in ("nouns.csv", "verbs.csv", "adjectives.csv", "adverbs.csv"):
        (vocabulary_root / filename).write_text(files.get(filename, ""), encoding="utf-8")
    monkeypatch.setenv("SILENT_VOCABULARY_DIR", str(vocabulary_root))
    monkeypatch.setenv("SILENT_VOCABULARY_USER_DIR", str(tmp_path / "user-vocabulary"))


@pytest.fixture(name="homographs")
def homographs_fixture(tmp_path, monkeypatch):
    _prepare_vocabulary(
        tmp_path,
        monkeypatch,
        {
            "nouns.csv": 'der See,lake\ndie See,sea\nder Weg,"path, way"\ndie Katze,cat\n',
            "adverbs.csv": 'weg,"gone, vanished"\n',
        },
    )


def test_an_entry_is_described_with_its_word_class_article_and_meaning():
    row = ("der", "Weg", "path, way", None, "noun", None, None, None, None)

    assert describe_entry(row) == "noun: der Weg - path, way"


def test_an_entry_without_an_article_is_described_without_one():
    row = (None, "weg", "gone", None, "adverb", None, None, None, None)

    assert describe_entry(row) == "adverb: weg - gone"


def test_every_entry_that_shares_a_spelling_is_found():
    found = find_word_entries("german", "Weg")

    assert sorted(row[4] for row in found) == ["adverb", "noun"]


def test_lookup_ignores_case():
    assert len(find_word_entries("german", "wEg")) == 2


def test_an_unknown_word_finds_nothing():
    assert not find_word_entries("german", "Fenster")


def test_a_blank_word_finds_nothing():
    assert not find_word_entries("german", "   ")


def test_a_word_with_one_entry_resolves_without_help():
    resolved = resolve_entry("german", "Katze")

    assert resolved[2] == "cat"


def test_a_word_class_picks_one_of_two_homographs():
    resolved = resolve_entry("german", "Weg", classification="adverb")

    assert resolved[2] == "gone, vanished"


def test_an_article_separates_two_nouns_with_the_same_spelling():
    assert resolve_entry("german", "See", article="die")[2] == "sea"
    assert resolve_entry("german", "See", article="der")[2] == "lake"


def test_an_ambiguous_word_is_reported_with_its_candidates():
    with pytest.raises(AmbiguousWordError) as ambiguity:
        resolve_entry("german", "See")

    assert ambiguity.value.word == "See"
    assert sorted(row[2] for row in ambiguity.value.candidates) == ["lake", "sea"]
    assert "der See" in str(ambiguity.value)
    assert "die See" in str(ambiguity.value)


def test_an_unknown_word_is_reported_as_missing():
    with pytest.raises(ValueError, match="Word not found: Fenster"):
        resolve_entry("german", "Fenster")


def test_a_word_class_that_does_not_match_is_reported_as_missing():
    with pytest.raises(ValueError, match="Word not found: See"):
        resolve_entry("german", "See", classification="verb")


def test_a_blank_word_is_rejected():
    with pytest.raises(ValueError, match="Word input is empty"):
        resolve_entry("german", "  ")
