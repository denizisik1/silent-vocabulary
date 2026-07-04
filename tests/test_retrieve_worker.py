import pytest

from retrieve import CapabilityReport, RetrieveResult
from retrieve.worker import RetrieveWorker

RESULT = RetrieveResult(
    word="Abend",
    url="https://en.pons.com/dict/Abend",
    pronunciation="[ˈaːbənt]",
    source_label="backup",
    fetch_method="browser",
)
ROW = ("der", "Abend", "evening", "[ˈaːbənt]", "noun", None, None, None, None)


def build_worker(**overrides):
    settings = {
        "mode": "retrieve",
        "language_key": "german",
        "word": "Abend",
        "primary_url": "https://en.pons.com/dict/",
        "primary_find": "phonetics",
        "backup_url": "https://www.collinsdictionary.com/dict/",
        "backup_find": "pron",
    }
    settings.update(overrides)
    return RetrieveWorker(**settings)


def run_and_collect(worker):
    successes = []
    errors = []
    worker.finished_ok.connect(lambda message, row: successes.append((message, row)))
    worker.finished_error.connect(errors.append)
    worker.run()
    return successes, errors


def use_retrieve(monkeypatch, outcome):
    def fake_retrieve(**_settings):
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr("retrieve.worker.retrieve_ipa_with_strategy", fake_retrieve)


def use_upsert(monkeypatch, outcome=ROW):
    calls = []

    def fake_upsert(language_key, word, pronunciation, **options):
        calls.append((language_key, word, pronunciation, options))
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr("retrieve.worker.upsert_pronunciation", fake_upsert)
    return calls


def use_capabilities(monkeypatch, primary, backup):
    checked_words = []

    def fake_check(*, sample_word, source_label, **_endpoint):
        checked_words.append(sample_word)
        return primary if source_label == "primary" else backup

    monkeypatch.setattr("retrieve.worker.check_source_capabilities", fake_check)
    return checked_words


def report(source_label, *, reachable=True, ipa_found=True, detail="ok", sample_ipa=None):
    return CapabilityReport(
        source_label=source_label,
        base_url="https://example.com/dict/",
        sample_url="https://example.com/dict/Abend",
        reachable=reachable,
        detail=detail,
        ipa_found=ipa_found,
        sample_ipa=sample_ipa,
    )


def test_a_retrieved_pronunciation_is_saved_and_reported(monkeypatch):
    use_retrieve(monkeypatch, RESULT)
    upserts = use_upsert(monkeypatch)

    successes, errors = run_and_collect(build_worker())

    assert not errors
    message, row = successes[0]
    assert row == ROW
    assert "backup" in message
    assert "browser" in message
    assert "Abend" in message
    assert "[ˈaːbənt]" in message
    assert upserts == [
        (
            "german",
            "Abend",
            "[ˈaːbənt]",
            {"classification": None, "article": None, "source": RESULT.url},
        )
    ]


def test_the_chosen_entry_is_passed_through_to_the_write(monkeypatch):
    use_retrieve(monkeypatch, RESULT)
    upserts = use_upsert(monkeypatch)

    worker = build_worker(word="Weg", classification="noun", article="der")
    successes, errors = run_and_collect(worker)

    assert not errors
    assert successes
    assert upserts[0][3]["classification"] == "noun"
    assert upserts[0][3]["article"] == "der"


def test_a_failed_retrieve_saves_nothing(monkeypatch):
    use_retrieve(monkeypatch, RuntimeError("primary/basic: HTTP 403"))
    upserts = use_upsert(monkeypatch)

    successes, errors = run_and_collect(build_worker())

    assert not successes
    assert errors == ["primary/basic: HTTP 403"]
    assert not upserts


def test_a_word_that_is_not_in_the_list_is_reported_as_an_error(monkeypatch):
    use_retrieve(monkeypatch, RESULT)
    use_upsert(monkeypatch, ValueError("Word not found: Abend"))

    successes, errors = run_and_collect(build_worker())

    assert not successes
    assert errors == ["Word not found: Abend"]


def test_the_check_summarises_both_sources(monkeypatch):
    use_capabilities(
        monkeypatch,
        report("primary", sample_ipa="[ˈaːbənt]"),
        report("backup", reachable=False, ipa_found=False, detail="requests: HTTP 404"),
    )

    successes, errors = run_and_collect(build_worker(mode="check"))

    assert not errors
    message, row = successes[0]
    assert row is None
    primary_line, backup_line, strategy_line = message.splitlines()
    assert primary_line == "Primary: reachable=True ipa=True detail=ok sample=[ˈaːbənt]"
    assert backup_line == "Backup: reachable=False ipa=False detail=requests: HTTP 404"
    assert strategy_line == "Strategy: primary_first"


def test_the_check_falls_back_to_the_sample_word(monkeypatch):
    monkeypatch.setenv("SILENT_VOCABULARY_SAMPLE_WORD", "Morgen")
    checked_words = use_capabilities(monkeypatch, report("primary"), report("backup"))

    run_and_collect(build_worker(mode="check", word=""))

    assert checked_words == ["Morgen", "Morgen"]


def test_an_unusable_strategy_falls_back_to_the_default(monkeypatch):
    use_capabilities(monkeypatch, report("primary"), report("backup"))

    successes, _errors = run_and_collect(
        build_worker(mode="check", retrieve_strategy="chaos"),
    )

    assert successes[0][0].endswith("Strategy: primary_first")


def test_the_configured_strategy_reaches_the_service(monkeypatch):
    used = []

    def fake_retrieve(*, word, primary, backup, strategy):
        used.append((word, primary.base_url, backup.find_by, strategy))
        return RESULT

    monkeypatch.setattr("retrieve.worker.retrieve_ipa_with_strategy", fake_retrieve)
    use_upsert(monkeypatch)

    run_and_collect(build_worker(retrieve_strategy="basic_first"))

    assert used == [("Abend", "https://en.pons.com/dict/", "pron", "basic_first")]


def test_an_unexpected_failure_is_surfaced_instead_of_crashing(monkeypatch):
    def explode(**_settings):
        raise KeyError("boom")

    monkeypatch.setattr("retrieve.worker.retrieve_ipa_with_strategy", explode)

    successes, errors = run_and_collect(build_worker())

    assert not successes
    assert errors == ["'boom'"]


@pytest.mark.parametrize("mode", ["retrieve", "check"])
def test_each_mode_emits_exactly_one_signal(monkeypatch, mode):
    use_retrieve(monkeypatch, RESULT)
    use_upsert(monkeypatch)
    use_capabilities(monkeypatch, report("primary"), report("backup"))

    successes, errors = run_and_collect(build_worker(mode=mode))

    assert len(successes) + len(errors) == 1
