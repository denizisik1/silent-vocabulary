import pytest

from retrieve.http_headers import browser_headers, browser_locale, origin_url

ENTRY_URL = "https://www.collinsdictionary.com/dictionary/german-english/daten"

pytestmark = pytest.mark.usefixtures("without_app_environment")


def test_origin_url_drops_path_query_and_fragment():
    assert origin_url(f"{ENTRY_URL}?q=1#top") == "https://www.collinsdictionary.com/"


def test_origin_url_keeps_port():
    assert origin_url("http://localhost:8000/dict/word") == "http://localhost:8000/"


def test_origin_url_rejects_url_without_scheme():
    with pytest.raises(ValueError, match="Cannot derive origin"):
        origin_url("www.collinsdictionary.com/dictionary")


def test_headers_default_referer_to_origin():
    headers = browser_headers(ENTRY_URL)

    assert headers["Referer"] == "https://www.collinsdictionary.com/"
    assert headers["Sec-Fetch-Site"] == "same-origin"


def test_headers_mark_foreign_referer_as_cross_site(monkeypatch):
    monkeypatch.setenv("SILENT_VOCABULARY_HTTP_REFERER", "https://www.google.com/")

    headers = browser_headers(ENTRY_URL)

    assert headers["Referer"] == "https://www.google.com/"
    assert headers["Sec-Fetch-Site"] == "cross-site"


def test_headers_describe_a_navigating_browser():
    headers = browser_headers(ENTRY_URL)

    assert headers["Sec-Fetch-Dest"] == "document"
    assert headers["Sec-Fetch-Mode"] == "navigate"
    assert headers["Sec-Fetch-User"] == "?1"
    assert headers["Upgrade-Insecure-Requests"] == "1"
    assert "Chrome" in headers["User-Agent"]
    assert headers["Sec-CH-UA-Platform"] == '"Linux"'


def test_headers_take_overrides_from_environment(monkeypatch):
    monkeypatch.setenv("SILENT_VOCABULARY_HTTP_USER_AGENT", "TestAgent/1.0")
    monkeypatch.setenv("SILENT_VOCABULARY_HTTP_ACCEPT_LANGUAGE", "de-DE,de;q=0.9")
    monkeypatch.setenv("SILENT_VOCABULARY_HTTP_ACCEPT_ENCODING", "identity")

    headers = browser_headers(ENTRY_URL)

    assert headers["User-Agent"] == "TestAgent/1.0"
    assert headers["Accept-Language"] == "de-DE,de;q=0.9"
    assert headers["Accept-Encoding"] == "identity"


def test_locale_uses_first_language_of_the_header():
    assert browser_locale("de-DE,de;q=0.9,en;q=0.8") == "de-DE"


def test_locale_strips_quality_value():
    assert browser_locale("de;q=0.9") == "de"


def test_locale_falls_back_to_environment_then_default(monkeypatch):
    assert browser_locale("") == "en-US"

    monkeypatch.setenv("SILENT_VOCABULARY_HTTP_ACCEPT_LANGUAGE", "fr-FR,fr;q=0.9")
    assert browser_locale() == "fr-FR"


def test_locale_defaults_when_header_has_no_language():
    assert browser_locale(",en;q=0.9") == "en-US"
