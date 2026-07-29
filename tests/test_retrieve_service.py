import pytest

from retrieve import (
    STRATEGY_BASIC_FIRST,
    STRATEGY_PRIMARY_FIRST,
    SourceEndpoint,
    check_source_capabilities,
    retrieve_ipa,
    retrieve_ipa_with_strategy,
)

PRIMARY = SourceEndpoint("primary", "https://en.pons.com/dict/", "phonetics")
BACKUP = SourceEndpoint("backup", "https://www.collinsdictionary.com/dict/", "pron")
PRIMARY_URL = "https://en.pons.com/dict/Abend"
BACKUP_URL = "https://www.collinsdictionary.com/dict/Abend"


def page_with(pronunciation, css_class="phonetics"):
    return f"<html><span class='{css_class}'>{pronunciation}</span></html>"


def use_pages(monkeypatch, pages):
    calls = []

    def fake_fetch(url, method):
        calls.append((url, method))
        outcome = pages.get((url, method), RuntimeError("HTTP 403"))
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr("retrieve.service.fetch_html_with_method", fake_fetch)
    return calls


def test_retrieve_reports_where_and_how_the_word_was_found(monkeypatch):
    use_pages(monkeypatch, {(PRIMARY_URL, "basic"): page_with("/ˈaːbənt/")})

    result = retrieve_ipa(
        base_url=PRIMARY.base_url,
        find_by=PRIMARY.find_by,
        word="  Abend  ",
        source_label="primary",
    )

    assert result.word == "Abend"
    assert result.url == PRIMARY_URL
    assert result.pronunciation == "[ˈaːbənt]"
    assert result.source_label == "primary"
    assert result.fetch_method == "basic"


def test_retrieve_propagates_a_missing_selector(monkeypatch):
    use_pages(monkeypatch, {(PRIMARY_URL, "basic"): "<html><span class='x'>hi</span></html>"})

    with pytest.raises(ValueError, match="No IPA found"):
        retrieve_ipa(
            base_url=PRIMARY.base_url,
            find_by=PRIMARY.find_by,
            word="Abend",
            source_label="primary",
        )


def test_strategy_stops_at_the_first_success(monkeypatch):
    calls = use_pages(monkeypatch, {(PRIMARY_URL, "basic"): page_with("[ˈaːbənt]")})

    result = retrieve_ipa_with_strategy(
        word="Abend",
        primary=PRIMARY,
        backup=BACKUP,
        strategy=STRATEGY_PRIMARY_FIRST,
    )

    assert result.source_label == "primary"
    assert calls == [(PRIMARY_URL, "basic")]


def test_primary_first_escalates_to_the_browser_before_the_backup(monkeypatch):
    calls = use_pages(monkeypatch, {(PRIMARY_URL, "browser"): page_with("[ˈaːbənt]")})

    result = retrieve_ipa_with_strategy(
        word="Abend",
        primary=PRIMARY,
        backup=BACKUP,
        strategy=STRATEGY_PRIMARY_FIRST,
    )

    assert (result.source_label, result.fetch_method) == ("primary", "browser")
    assert calls == [(PRIMARY_URL, "basic"), (PRIMARY_URL, "browser")]


def test_basic_first_tries_the_backup_before_the_browser(monkeypatch):
    calls = use_pages(monkeypatch, {(BACKUP_URL, "basic"): page_with("[ˈaːbənt]", "pron")})

    result = retrieve_ipa_with_strategy(
        word="Abend",
        primary=PRIMARY,
        backup=BACKUP,
        strategy=STRATEGY_BASIC_FIRST,
    )

    assert (result.source_label, result.fetch_method) == ("backup", "basic")
    assert calls == [(PRIMARY_URL, "basic"), (BACKUP_URL, "basic")]


def test_unknown_strategy_behaves_like_primary_first(monkeypatch):
    calls = use_pages(monkeypatch, {(PRIMARY_URL, "browser"): page_with("[ˈaːbənt]")})

    retrieve_ipa_with_strategy(word="Abend", primary=PRIMARY, backup=BACKUP, strategy="chaos")

    assert calls == [(PRIMARY_URL, "basic"), (PRIMARY_URL, "browser")]


def test_every_attempt_is_listed_when_all_of_them_fail(monkeypatch):
    calls = use_pages(monkeypatch, {})

    with pytest.raises(RuntimeError) as failure:
        retrieve_ipa_with_strategy(
            word="Abend",
            primary=PRIMARY,
            backup=BACKUP,
            strategy=STRATEGY_PRIMARY_FIRST,
        )

    message = str(failure.value)
    assert len(calls) == 4
    assert "primary/basic: HTTP 403" in message
    assert "primary/browser: HTTP 403" in message
    assert "backup/basic: HTTP 403" in message
    assert "backup/browser: HTTP 403" in message


def test_capability_check_describes_a_working_source(monkeypatch):
    monkeypatch.setattr("retrieve.service.probe_url", lambda url: (True, "HTTP 200"))
    monkeypatch.setattr("retrieve.service.fetch_html", lambda url: page_with("[ˈaːbənt]"))

    report = check_source_capabilities(
        base_url=PRIMARY.base_url,
        find_by=PRIMARY.find_by,
        sample_word="Abend",
        source_label="primary",
    )

    assert report.sample_url == PRIMARY_URL
    assert report.reachable is True
    assert report.ipa_found is True
    assert report.sample_ipa == "[ˈaːbənt]"
    assert report.detail == "ok"


def test_capability_check_skips_fetching_an_unreachable_source(monkeypatch):
    monkeypatch.setattr("retrieve.service.probe_url", lambda url: (False, "requests: HTTP 404"))

    def unexpected_fetch(url):
        raise AssertionError("unreachable source must not be fetched")

    monkeypatch.setattr("retrieve.service.fetch_html", unexpected_fetch)

    report = check_source_capabilities(
        base_url=PRIMARY.base_url,
        find_by=PRIMARY.find_by,
        sample_word="Abend",
        source_label="primary",
    )

    assert report.reachable is False
    assert report.ipa_found is False
    assert report.detail == "requests: HTTP 404"
    assert report.sample_ipa is None


def test_capability_check_separates_reachable_from_parsable(monkeypatch):
    monkeypatch.setattr("retrieve.service.probe_url", lambda url: (True, "HTTP 200"))
    monkeypatch.setattr("retrieve.service.fetch_html", lambda url: "<html>no phonetics</html>")

    report = check_source_capabilities(
        base_url=PRIMARY.base_url,
        find_by=PRIMARY.find_by,
        sample_word="Abend",
        source_label="primary",
    )

    assert report.reachable is True
    assert report.ipa_found is False
    assert "No IPA found" in report.detail
