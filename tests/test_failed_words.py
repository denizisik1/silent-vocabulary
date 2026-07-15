from words.failures import (
    FailureEntry,
    failure_entry_from_row,
    forget_failure_of_row,
    read_failure_entries,
    rows_without_failures,
    upsert_failure_entry,
    write_failure_entries,
)
from words.paths import shipped_failures_path

ABEND = ("der", "Abend", "evening", None, "noun", None, None, None, None)
HAUS = ("das", "Haus", "house", None, "noun", None, None, None, None)


def german_failures(vocabulary_root):
    return shipped_failures_path("german", vocabulary_root)


def failure(word, reason="HTTP 403", classification="noun", article=None):
    return FailureEntry(word=word, classification=classification, article=article, reason=reason)


def test_a_missing_ledger_reads_as_empty(tmp_path):
    assert not read_failure_entries(german_failures(tmp_path))


def test_what_is_written_can_be_read_back(tmp_path):
    ledger = german_failures(tmp_path)

    write_failure_entries(ledger, [failure("Haus"), failure("Abend", article="der")])

    assert [entry.word for entry in read_failure_entries(ledger)] == ["Abend", "Haus"]


def test_a_second_failure_of_one_word_replaces_the_first(tmp_path):
    ledger = german_failures(tmp_path)

    upsert_failure_entry(ledger, failure("Abend", reason="HTTP 403"))
    upsert_failure_entry(ledger, failure("Abend", reason="no phonetics"))

    entries = read_failure_entries(ledger)

    assert len(entries) == 1
    assert entries[0].reason == "no phonetics"


def test_the_same_word_of_another_kind_is_kept_apart(tmp_path):
    ledger = german_failures(tmp_path)

    upsert_failure_entry(ledger, failure("laufen", classification="verb"))
    upsert_failure_entry(ledger, failure("laufen", classification="noun"))

    assert len(read_failure_entries(ledger)) == 2


def test_a_row_without_a_word_is_dropped(tmp_path):
    ledger = german_failures(tmp_path)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("word,classification,article,reason\n,noun,,HTTP 403\n", encoding="utf-8")

    assert not read_failure_entries(ledger)


def test_marked_words_are_taken_out_of_the_queue():
    remaining = rows_without_failures([ABEND, HAUS], [failure("Abend", article="der")])

    assert remaining == [HAUS]


def test_an_empty_ledger_leaves_the_queue_alone():
    assert rows_without_failures([ABEND, HAUS], []) == [ABEND, HAUS]


def test_a_row_carries_its_own_details_into_the_ledger():
    entry = failure_entry_from_row(ABEND, "HTTP 403")

    assert entry == FailureEntry(
        word="Abend",
        classification="noun",
        article="der",
        reason="HTTP 403",
    )


def test_a_word_can_be_forgotten_again(tmp_path):
    ledger = german_failures(tmp_path)
    upsert_failure_entry(ledger, failure_entry_from_row(ABEND, "HTTP 403"))
    upsert_failure_entry(ledger, failure_entry_from_row(HAUS, "HTTP 403"))

    forget_failure_of_row(ledger, ABEND)

    assert [entry.word for entry in read_failure_entries(ledger)] == ["Haus"]


def test_forgetting_a_word_that_never_failed_writes_nothing(tmp_path):
    ledger = german_failures(tmp_path)

    forget_failure_of_row(ledger, ABEND)

    assert not ledger.exists()
