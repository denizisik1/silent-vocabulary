from retrieve.parse import clean_ipa_text, extract_ipa_from_html
from retrieve.url import build_entry_url


def test_build_entry_url_appends_word():
    url = build_entry_url("https://en.pons.com/translate/german-english", "Abend")

    assert url == "https://en.pons.com/translate/german-english/Abend"


def test_build_entry_url_quotes_spaces():
    url = build_entry_url("https://example.com/dict/", "der Abend")

    assert url.endswith("/der%20Abend")


def test_clean_ipa_text_brackets():
    assert clean_ipa_text("[ˈa:bn̩t]") == "[ˈa:bn̩t]"
    assert clean_ipa_text("/ˈaːbənt/") == "[ˈaːbənt]"


def test_extract_ipa_from_html_by_class():
    page_html = """
    <html><body>
      <span class="phonetics">[ˈa:bn̩t]</span>
      <span class="other">noise</span>
    </body></html>
    """

    assert extract_ipa_from_html(page_html, "phonetics") == "[ˈa:bn̩t]"


def test_extract_ipa_from_html_missing_raises():
    page_html = "<html><body><span class='x'>hello</span></body></html>"

    try:
        extract_ipa_from_html(page_html, "phonetics")
        assert False, "expected ValueError"
    except ValueError as error:
        assert "No IPA found" in str(error)


def test_fetch_html_falls_back_to_playwright(monkeypatch):
    calls: list[str] = []

    def fake_basic(url: str, *, timeout_seconds: float) -> str:
        calls.append("basic")
        raise RuntimeError("HTTP 403 for https://example.com/word")

    def fake_playwright(url: str, *, timeout_seconds: float) -> str:
        calls.append("playwright")
        return "<html><span class='phonetics'>[ˈa:bn̩t]</span></html>"

    monkeypatch.setattr("retrieve.fetch.fetch_html_basic", fake_basic)
    monkeypatch.setattr("retrieve.fetch.playwright_available", lambda: True)
    monkeypatch.setattr("retrieve.fetch.fetch_html_playwright", fake_playwright)

    from retrieve.fetch import fetch_html

    html = fetch_html("https://example.com/word")

    assert calls == ["basic", "playwright"]
    assert "phonetics" in html


def test_fetch_html_reports_both_failures(monkeypatch):
    monkeypatch.setattr(
        "retrieve.fetch.fetch_html_basic",
        lambda url, timeout_seconds: (_ for _ in ()).throw(RuntimeError("HTTP 403")),
    )
    monkeypatch.setattr("retrieve.fetch.playwright_available", lambda: True)
    monkeypatch.setattr(
        "retrieve.fetch.fetch_html_playwright",
        lambda url, timeout_seconds: (_ for _ in ()).throw(RuntimeError("browser missing")),
    )

    from retrieve.fetch import fetch_html

    try:
        fetch_html("https://example.com/word")
        assert False, "expected RuntimeError"
    except RuntimeError as error:
        assert "basic" in str(error)
        assert "playwright" in str(error)


def test_retrieve_attempt_order_primary_first():
    from retrieve.strategy import STRATEGY_PRIMARY_FIRST, retrieve_attempt_order

    assert retrieve_attempt_order(STRATEGY_PRIMARY_FIRST) == [
        ("primary", "basic"),
        ("primary", "playwright"),
        ("backup", "basic"),
        ("backup", "playwright"),
    ]


def test_retrieve_attempt_order_basic_first():
    from retrieve.strategy import STRATEGY_BASIC_FIRST, retrieve_attempt_order

    assert retrieve_attempt_order(STRATEGY_BASIC_FIRST) == [
        ("primary", "basic"),
        ("backup", "basic"),
        ("primary", "playwright"),
        ("backup", "playwright"),
    ]


def test_retrieve_ipa_with_strategy_primary_first(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_fetch(url: str, method: str, *, timeout_seconds: float = 20) -> str:
        calls.append((url, method))
        if "collins" in url and method == "basic":
            raise RuntimeError("HTTP 403")
        if "collins" in url and method == "playwright":
            return "<html><span class='pron'>[ˈa:bn̩t]</span></html>"
        raise RuntimeError("unexpected")

    monkeypatch.setattr("retrieve.service.fetch_html_with_method", fake_fetch)

    from retrieve.service import SourceEndpoint, retrieve_ipa_with_strategy
    from retrieve.strategy import STRATEGY_PRIMARY_FIRST

    result = retrieve_ipa_with_strategy(
        word="Abend",
        primary=SourceEndpoint(
            "primary",
            "https://www.collinsdictionary.com/dictionary/german-english/",
            "pron",
        ),
        backup=SourceEndpoint(
            "backup",
            "https://en.pons.com/translate/german-english/",
            "phonetics",
        ),
        strategy=STRATEGY_PRIMARY_FIRST,
    )

    assert result.source_label == "primary"
    assert result.fetch_method == "playwright"
    assert result.pronunciation == "[ˈa:bn̩t]"
    assert calls == [
        ("https://www.collinsdictionary.com/dictionary/german-english/Abend", "basic"),
        (
            "https://www.collinsdictionary.com/dictionary/german-english/Abend",
            "playwright",
        ),
    ]


def test_retrieve_ipa_with_strategy_basic_first(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_fetch(url: str, method: str, *, timeout_seconds: float = 20) -> str:
        calls.append((url, method))
        if "collins" in url:
            raise RuntimeError("HTTP 403")
        if "pons" in url and method == "basic":
            return "<html><span class='phonetics'>[ˈa:bn̩t]</span></html>"
        raise RuntimeError("unexpected")

    monkeypatch.setattr("retrieve.service.fetch_html_with_method", fake_fetch)

    from retrieve.service import SourceEndpoint, retrieve_ipa_with_strategy
    from retrieve.strategy import STRATEGY_BASIC_FIRST

    result = retrieve_ipa_with_strategy(
        word="Abend",
        primary=SourceEndpoint(
            "primary",
            "https://www.collinsdictionary.com/dictionary/german-english/",
            "pron",
        ),
        backup=SourceEndpoint(
            "backup",
            "https://en.pons.com/translate/german-english/",
            "phonetics",
        ),
        strategy=STRATEGY_BASIC_FIRST,
    )

    assert result.source_label == "backup"
    assert result.fetch_method == "basic"
    assert calls == [
        ("https://www.collinsdictionary.com/dictionary/german-english/Abend", "basic"),
        ("https://en.pons.com/translate/german-english/Abend", "basic"),
    ]
