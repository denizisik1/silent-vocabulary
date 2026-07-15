import pytest

from retrieve.bulk import (
    MAX_BACKOFF_SECONDS,
    BulkSettings,
    failure_backoff_seconds,
    fetch_pronunciations,
    jittered_delay_seconds,
    rows_needing_pronunciation,
)
from retrieve.service import RetrieveResult, SourceEndpoint

PRIMARY = SourceEndpoint("primary", "https://en.pons.com/dict/", "phonetics")
BACKUP = SourceEndpoint("backup", "https://www.collinsdictionary.com/dict/", "pron")
BASIC_ATTEMPTS = [("primary", "basic")]


def noun_row(word, pronunciation=None, article="der"):
    return (article, word, "meaning", pronunciation, "noun", None, None, None, None)


def bulk_settings(**overrides):
    return BulkSettings(
        primary=PRIMARY,
        backup=BACKUP,
        attempts=BASIC_ATTEMPTS,
        **overrides,
    )


def use_pronunciations(monkeypatch, pronunciations):
    asked = []

    def fake_retrieve(*, word, primary, attempts, **_unused):
        asked.append(word)
        found = pronunciations.get(word)
        if found is None:
            raise RuntimeError("HTTP 403")
        return RetrieveResult(
            word=word,
            url=f"{primary.base_url}{word}",
            pronunciation=found,
            source_label=primary.label,
            fetch_method=attempts[0][1],
        )

    monkeypatch.setattr("retrieve.bulk.retrieve_ipa_with_attempts", fake_retrieve)
    return asked


class BulkRun:
    def __init__(self):
        self.saved = []
        self.marked = []
        self.messages = []
        self.outcome = None

    def save(self, row, result):
        self.saved.append((row[1], result.pronunciation))

    def mark_failed(self, row, reason):
        self.marked.append((row[1], reason))

    def report(self, message, kind):
        self.messages.append(f"{kind}: {message}")


def run_bulk(rows, settings, *, sleep=None):
    run = BulkRun()
    run.outcome = fetch_pronunciations(
        rows,
        settings,
        save=run.save,
        fail=run.mark_failed,
        report=run.report,
        sleep=(lambda seconds: None) if sleep is None else sleep,
    )
    return run


def test_every_word_that_answers_is_saved(monkeypatch):
    use_pronunciations(monkeypatch, {"Abend": "[ˈaːbənt]", "Zeit": "[tsaɪt]"})

    run = run_bulk(
        [noun_row("Abend"), noun_row("Zeit")],
        bulk_settings(delay_seconds=0),
    )

    assert run.saved == [("Abend", "[ˈaːbənt]"), ("Zeit", "[tsaɪt]")]
    assert (run.outcome.total, run.outcome.saved, run.outcome.failed) == (2, 2, 0)
    assert run.messages == [
        "header: [1/2] Abend",
        "good: saved Abend [ˈaːbənt] from primary",
        "header: [2/2] Zeit",
        "good: saved Zeit [tsaɪt] from primary",
    ]


def test_a_word_without_an_answer_is_reported_and_counted(monkeypatch):
    use_pronunciations(monkeypatch, {"Zeit": "[tsaɪt]"})

    run = run_bulk(
        [noun_row("Abend"), noun_row("Zeit")],
        bulk_settings(delay_seconds=0),
    )

    assert run.saved == [("Zeit", "[tsaɪt]")]
    assert (run.outcome.saved, run.outcome.failed) == (1, 1)
    assert run.messages[:2] == [
        "header: [1/2] Abend",
        "bad: no pronunciation for Abend, marked to be skipped next time",
    ]


def test_a_failed_word_is_handed_over_to_be_marked(monkeypatch):
    use_pronunciations(monkeypatch, {})

    run = run_bulk([noun_row("Abend")], bulk_settings(delay_seconds=0))

    assert run.marked == [("Abend", "HTTP 403")]


def test_the_wait_falls_between_words_and_not_before_the_first(monkeypatch):
    use_pronunciations(monkeypatch, {"Abend": "[a]", "Zeit": "[b]", "Haus": "[c]"})
    waits = []

    run_bulk(
        [noun_row("Abend"), noun_row("Zeit"), noun_row("Haus")],
        bulk_settings(delay_seconds=4.0),
        sleep=waits.append,
    )

    assert len(waits) == 2
    assert all(3.0 <= wait <= 5.0 for wait in waits)


def test_a_failure_is_followed_by_a_longer_wait(monkeypatch):
    use_pronunciations(monkeypatch, {"Zeit": "[tsaɪt]"})
    waits = []

    run_bulk(
        [noun_row("Abend"), noun_row("Zeit")],
        bulk_settings(delay_seconds=2.0),
        sleep=waits.append,
    )

    assert waits[0] == 4.0
    assert 1.5 <= waits[1] <= 2.5


def test_fast_skips_the_extra_wait_after_a_failure(monkeypatch):
    use_pronunciations(monkeypatch, {"Zeit": "[tsaɪt]"})
    waits = []

    run_bulk(
        [noun_row("Abend"), noun_row("Zeit")],
        bulk_settings(delay_seconds=2.0, backoff_on_failure=False),
        sleep=waits.append,
    )

    assert len(waits) == 1
    assert 1.5 <= waits[0] <= 2.5


def test_the_run_stops_when_too_many_words_fail_in_a_row(monkeypatch):
    asked = use_pronunciations(monkeypatch, {})

    run = run_bulk(
        [noun_row(f"Wort{index}") for index in range(6)],
        bulk_settings(delay_seconds=0, max_consecutive_failures=3),
    )

    assert run.outcome.stopped_early is True
    assert (run.outcome.saved, run.outcome.failed, run.outcome.total) == (0, 3, 6)
    assert len(asked) == 3
    assert run.messages[-1] == "bad: stopped after 3 failures in a row"


def test_a_success_clears_the_failure_streak(monkeypatch):
    use_pronunciations(monkeypatch, {"Zeit": "[tsaɪt]"})

    run = run_bulk(
        [noun_row("Abend"), noun_row("Zeit"), noun_row("Haus")],
        bulk_settings(delay_seconds=0, max_consecutive_failures=2),
    )

    assert run.outcome.stopped_early is False
    assert (run.outcome.saved, run.outcome.failed) == (1, 2)


def test_the_backoff_grows_but_never_past_the_ceiling():
    assert failure_backoff_seconds(3.0, 1) == 6.0
    assert failure_backoff_seconds(3.0, 2) == 12.0
    assert failure_backoff_seconds(3.0, 20) == MAX_BACKOFF_SECONDS
    assert failure_backoff_seconds(3.0, 0) == 0.0


def test_no_delay_means_no_waiting():
    assert jittered_delay_seconds(0.0) == 0.0
    assert failure_backoff_seconds(0.0, 3) == 0.0


@pytest.fixture(autouse=True)
def vocabulary_root(tmp_path, monkeypatch):
    root = tmp_path / "vocabulary"
    root.mkdir()
    (root / "nouns.csv").write_text(
        "article,word,meaning,pronunciation,classification\n"
        "der,Abend,evening,[ˈaːbənt],noun\n"
        "die,Zeit,time,,noun\n",
        encoding="utf-8",
    )
    (root / "verbs.csv").write_text("laufen,to run\n", encoding="utf-8")
    monkeypatch.setenv("SILENT_VOCABULARY_DIR", str(root))


def test_only_the_words_without_a_pronunciation_are_queued():
    rows = rows_needing_pronunciation("german")

    assert [row[1] for row in rows] == ["laufen", "Zeit"]
