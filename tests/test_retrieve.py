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

    def fake_requests(url: str, *, timeout_seconds: float) -> str:
        calls.append("requests")
        raise RuntimeError("HTTP 403 for https://example.com/word")

    def fake_playwright(url: str, *, timeout_seconds: float) -> str:
        calls.append("playwright")
        return "<html><span class='phonetics'>[ˈa:bn̩t]</span></html>"

    monkeypatch.setattr("retrieve.fetch._fetch_html_requests", fake_requests)
    monkeypatch.setattr("retrieve.fetch.playwright_available", lambda: True)
    monkeypatch.setattr("retrieve.fetch.fetch_html_playwright", fake_playwright)

    from retrieve.fetch import fetch_html

    html = fetch_html("https://example.com/word")

    assert calls == ["requests", "playwright"]
    assert "phonetics" in html


def test_fetch_html_reports_both_failures(monkeypatch):
    monkeypatch.setattr(
        "retrieve.fetch._fetch_html_requests",
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
        assert "requests" in str(error)
        assert "playwright" in str(error)
