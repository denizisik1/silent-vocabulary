import pytest
import requests  # type: ignore[import-untyped]

from browser_config import BrowserConfig, apply_browser_config
from retrieve.fetch import fetch_html_basic, fetch_html_with_method
from retrieve.progress import retrieve_reporter

ORIGIN_URL = "https://example.com/"
ENTRY_URL = "https://example.com/dict/Abend"
PAGE = "<html><span class='pron'>[ˈaːbənt]</span></html>"

pytestmark = pytest.mark.usefixtures("without_app_environment")


@pytest.fixture(autouse=True)
def default_browser_config():
    apply_browser_config(BrowserConfig())
    yield
    apply_browser_config(BrowserConfig())


def test_visits_the_origin_before_the_entry_page(fake_http):
    fake_http.respond(ORIGIN_URL, "<html>home</html>")
    fake_http.respond(ENTRY_URL, PAGE)

    assert fetch_html_basic(ENTRY_URL) == PAGE
    assert fake_http.requested_urls() == [ORIGIN_URL, ENTRY_URL]


def test_warmup_promotes_the_entry_request_to_same_origin(fake_http):
    fake_http.respond(ORIGIN_URL, "<html>home</html>")
    fake_http.respond(ENTRY_URL, PAGE)

    fetch_html_basic(ENTRY_URL)

    entry_request = fake_http.calls[-1]
    assert entry_request.headers["Referer"] == ORIGIN_URL
    assert entry_request.headers["Sec-Fetch-Site"] == "same-origin"


def test_warmup_can_be_disabled(fake_http, monkeypatch):
    monkeypatch.setenv("SILENT_VOCABULARY_HTTP_WARMUP", "0")
    fake_http.respond(ENTRY_URL, PAGE)

    fetch_html_basic(ENTRY_URL)

    assert fake_http.requested_urls() == [ENTRY_URL]


def test_a_failing_warmup_does_not_stop_the_entry_request(fake_http):
    fake_http.fail(ORIGIN_URL, requests.ConnectionError("origin refused"))
    fake_http.respond(ENTRY_URL, PAGE)

    assert fetch_html_basic(ENTRY_URL) == PAGE


def test_error_status_is_reported_with_the_url(fake_http):
    fake_http.respond(ORIGIN_URL, "")
    fake_http.respond(ENTRY_URL, "denied", status_code=403)

    with pytest.raises(RuntimeError, match=f"HTTP 403 for {ENTRY_URL}"):
        fetch_html_basic(ENTRY_URL)


def test_a_challenge_page_counts_as_a_refusal_rather_than_a_missing_word(fake_http):
    fake_http.respond(ORIGIN_URL, "")
    fake_http.respond(
        ENTRY_URL,
        "<html><title>Just a moment...</title>cf_chl_opt</html>",
    )

    with pytest.raises(RuntimeError, match="bot challenge"):
        fetch_html_basic(ENTRY_URL)


def test_a_page_that_merely_mentions_cookies_is_served_as_usual(fake_http):
    fake_http.respond(ORIGIN_URL, "")
    fake_http.respond(ENTRY_URL, "<html><title>Abend</title>cookie consent</html>")

    assert "Abend" in fetch_html_basic(ENTRY_URL)


def test_the_plain_request_reports_what_it_read(fake_http, progress_log):
    fake_http.respond(ORIGIN_URL, "")
    fake_http.respond(ENTRY_URL, PAGE)

    with retrieve_reporter(progress_log.record):
        fetch_html_basic(ENTRY_URL)

    assert progress_log.messages() == [f"plain request answered {len(PAGE)} bytes for {ENTRY_URL}"]


def test_body_is_decoded_with_the_detected_encoding(fake_http):
    fake_http.respond(ORIGIN_URL, "")
    fake_http.respond(
        ENTRY_URL,
        "Grüße",
        encoding="iso-8859-1",
        apparent_encoding="iso-8859-1",
    )

    assert fetch_html_basic(ENTRY_URL) == "Grüße"


def test_undecodable_bytes_are_replaced_instead_of_raising(fake_http):
    fake_http.respond(ORIGIN_URL, "")
    fake_http.respond(ENTRY_URL, b"\xff\xfe", apparent_encoding="utf-8")

    assert fetch_html_basic(ENTRY_URL) == "\ufffd\ufffd"


def test_configured_fetch_timeout_is_used(fake_http):
    apply_browser_config(BrowserConfig(fetch_timeout_seconds=7.0))
    fake_http.respond(ORIGIN_URL, "")
    fake_http.respond(ENTRY_URL, PAGE)

    fetch_html_basic(ENTRY_URL)

    assert fake_http.calls[-1].timeout == 7.0


def test_warmup_timeout_is_capped_at_ten_seconds(fake_http):
    apply_browser_config(BrowserConfig(fetch_timeout_seconds=60.0))
    fake_http.respond(ORIGIN_URL, "")
    fake_http.respond(ENTRY_URL, PAGE)

    fetch_html_basic(ENTRY_URL)

    assert fake_http.calls[0].timeout == 10.0
    assert fake_http.calls[-1].timeout == 60.0


def test_explicit_timeout_overrides_the_configuration(fake_http):
    apply_browser_config(BrowserConfig(fetch_timeout_seconds=60.0))
    fake_http.respond(ORIGIN_URL, "")
    fake_http.respond(ENTRY_URL, PAGE)

    fetch_html_basic(ENTRY_URL, timeout_seconds=3.0)

    assert fake_http.calls[-1].timeout == 3.0


def test_method_dispatch_routes_to_basic_and_browser(monkeypatch):
    monkeypatch.setattr(
        "retrieve.fetch.fetch_html_basic",
        lambda url, timeout_seconds=None: f"basic {url} {timeout_seconds}",
    )
    monkeypatch.setattr(
        "retrieve.fetch.fetch_html_browser",
        lambda url, timeout_seconds=None, wanted=None: f"browser {url} {timeout_seconds}",
    )

    assert fetch_html_with_method(ENTRY_URL, "basic") == f"basic {ENTRY_URL} None"
    assert (
        fetch_html_with_method(ENTRY_URL, "browser", timeout_seconds=5.0)
        == f"browser {ENTRY_URL} 5.0"
    )


def test_method_dispatch_rejects_unknown_methods():
    with pytest.raises(ValueError, match="Unknown fetch method: carrier-pigeon"):
        fetch_html_with_method(ENTRY_URL, "carrier-pigeon")
