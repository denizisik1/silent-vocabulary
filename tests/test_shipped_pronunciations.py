from dataclasses import replace

from words.load import load_base_rows
from words.paths import shipped_pronunciations_path
from words.pronunciations import (
    PronunciationEntry,
    apply_pronunciations,
    read_pronunciation_entries,
    rows_missing_pronunciation,
    upsert_pronunciation_entry,
    write_pronunciation_entries,
)

ABEND = ("der", "Abend", "evening", None, "noun", None, None, None, None)
LAKE = ("der", "See", "lake", None, "noun", None, None, None, None)
SEA = ("die", "See", "sea", None, "noun", None, None, None, None)

ABEND_ENTRY = PronunciationEntry(
    word="Abend",
    pronunciation="[ˈaːbənt]",
    classification="noun",
    article="der",
    source="en.pons.com",
)


def german_pronunciations(vocabulary_root):
    return shipped_pronunciations_path("german", vocabulary_root)


def test_a_written_entry_is_read_back_unchanged(tmp_path):
    path = german_pronunciations(tmp_path)

    write_pronunciation_entries(path, [ABEND_ENTRY])

    assert read_pronunciation_entries(path) == [ABEND_ENTRY]


def test_a_missing_file_reads_as_no_entries(tmp_path):
    assert not read_pronunciation_entries(german_pronunciations(tmp_path))


def test_entries_are_written_in_a_stable_order(tmp_path):
    path = german_pronunciations(tmp_path)
    zeit = PronunciationEntry(word="Zeit", pronunciation="[tsaɪt]", classification="noun")

    write_pronunciation_entries(path, [zeit, ABEND_ENTRY])

    assert [entry.word for entry in read_pronunciation_entries(path)] == ["Abend", "Zeit"]


def test_a_second_pronunciation_for_the_same_entry_replaces_the_first(tmp_path):
    path = german_pronunciations(tmp_path)
    upsert_pronunciation_entry(path, replace(ABEND_ENTRY, pronunciation="[wrong]"))

    upsert_pronunciation_entry(path, ABEND_ENTRY)

    assert read_pronunciation_entries(path) == [ABEND_ENTRY]


def test_an_entry_without_a_pronunciation_is_ignored(tmp_path):
    path = german_pronunciations(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "word,classification,article,pronunciation,source\n"
        "Abend,noun,der,,pons\n"
        ",noun,die,[tsaɪt],pons\n",
        encoding="utf-8",
    )

    assert not read_pronunciation_entries(path)


def test_a_pronunciation_reaches_the_row_it_names():
    applied = apply_pronunciations([ABEND, LAKE], [ABEND_ENTRY])

    assert applied[0][3] == "[ˈaːbənt]"
    assert applied[0][5] == "en.pons.com"
    assert applied[1] == LAKE


def test_a_pronunciation_only_reaches_the_entry_with_the_same_article():
    entry = PronunciationEntry(
        word="See",
        pronunciation="[zeː]",
        classification="noun",
        article="die",
    )

    applied = apply_pronunciations([LAKE, SEA], [entry])

    assert applied[0][3] is None
    assert applied[1][3] == "[zeː]"


def test_a_row_keeps_its_own_source_when_the_entry_has_none():
    row = ("der", "Abend", "evening", None, "noun", "duden", None, None, None)
    entry = replace(ABEND_ENTRY, source=None)

    applied = apply_pronunciations([row], [entry])

    assert applied[0][5] == "duden"


def test_rows_that_still_need_a_pronunciation_are_listed():
    spoken = ("die", "Zeit", "time", "[tsaɪt]", "noun", None, None, None, None)

    missing = rows_missing_pronunciation([ABEND, spoken, LAKE])

    assert [row[1] for row in missing] == ["Abend", "See"]


def test_a_shipped_pronunciation_file_fills_the_word_lists(tmp_path):
    (tmp_path / "nouns.csv").write_text("der Abend,evening\n", encoding="utf-8")
    write_pronunciation_entries(german_pronunciations(tmp_path), [ABEND_ENTRY])

    rows = load_base_rows("german", tmp_path)

    assert rows == [
        ("der", "Abend", "evening", "[ˈaːbənt]", "noun", "en.pons.com", None, None, None),
    ]


def test_a_shipped_pronunciation_replaces_one_written_in_a_word_list(tmp_path):
    (tmp_path / "nouns.csv").write_text(
        "article,word,meaning,pronunciation,classification\nder,Abend,evening,[old],noun\n",
        encoding="utf-8",
    )
    write_pronunciation_entries(german_pronunciations(tmp_path), [ABEND_ENTRY])

    rows = load_base_rows("german", tmp_path)

    assert rows[0][3] == "[ˈaːbənt]"
