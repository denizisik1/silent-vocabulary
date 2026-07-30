import pytest
import requests  # type: ignore[import-untyped]  # no stubs

from browser_config import BrowserConfig, apply_browser_config
from retrieve.fetch import fetch_html, fetch_html_browser, probe_url
from retrieve.headword import WantedIpa

ENTRY_URL = "https://example.com/dict/Abend"
PAGE = "<html><span class='pron'>[ˈaːbənt]</span></html>"

pytestmark = pytest.mark.usefixtures("without_app_environment")


@pytest.fixture(autouse=True)
def default_browser_config():
    apply_browser_config(BrowserConfig())
    yield
    apply_browser_config(BrowserConfig())


def use_browser(monkeypatch, *, available=True, result=PAGE):
    calls = []

    def fake_browser_fetch(url, *, timeout_seconds=None, wanted=None):
        calls.append((url, timeout_seconds, wanted))
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr("retrieve.fetch.ensure_browser_ready", lambda: available)
    monkeypatch.setattr("retrieve.fetch.fetch_html_via_browser", fake_browser_fetch)
    return calls


def fail_basic(monkeypatch, error):
    def fake_basic(url, *, timeout_seconds=None):
        raise error

    monkeypatch.setattr("retrieve.fetch.fetch_html_basic", fake_basic)


def test_browser_fetch_adds_the_configured_extra_time(monkeypatch):
    apply_browser_config(BrowserConfig(fetch_timeout_seconds=20.0, extra_timeout_seconds=15.0))
    calls = use_browser(monkeypatch)

    assert fetch_html_browser(ENTRY_URL) == PAGE
    assert calls == [(ENTRY_URL, 35.0, None)]


def test_the_browser_is_told_what_to_wait_for(monkeypatch):
    calls = use_browser(monkeypatch)
    wanted = WantedIpa("pron", "Abend")

    assert fetch_html_browser(ENTRY_URL, wanted=wanted) == PAGE
    assert calls[-1][2] == wanted


def test_browser_fetch_explains_how_to_get_a_browser(monkeypatch):
    use_browser(monkeypatch, available=False)

    with pytest.raises(RuntimeError, match="Chrome, Chromium, or Brave"):
        fetch_html_browser(ENTRY_URL)


def test_successful_basic_fetch_never_starts_a_browser(monkeypatch):
    monkeypatch.setattr("retrieve.fetch.fetch_html_basic", lambda url, timeout_seconds=None: PAGE)
    calls = use_browser(monkeypatch)

    assert fetch_html(ENTRY_URL) == PAGE
    assert not calls


def test_blocked_basic_fetch_falls_back_to_the_browser(monkeypatch):
    fail_basic(monkeypatch, RuntimeError("HTTP 403 for " + ENTRY_URL))
    calls = use_browser(monkeypatch)

    assert fetch_html(ENTRY_URL) == PAGE
    assert len(calls) == 1


def test_network_error_also_falls_back_to_the_browser(monkeypatch):
    fail_basic(monkeypatch, requests.ConnectionError("name resolution failed"))
    calls = use_browser(monkeypatch)

    assert fetch_html(ENTRY_URL) == PAGE
    assert len(calls) == 1


def test_both_failures_are_reported_together(monkeypatch):
    fail_basic(monkeypatch, RuntimeError("HTTP 403"))
    use_browser(monkeypatch, result=RuntimeError("browser timed out"))

    with pytest.raises(RuntimeError) as failure:
        fetch_html(ENTRY_URL)

    message = str(failure.value)
    assert "basic (HTTP 403)" in message
    assert "browser (browser timed out)" in message


def test_probe_reports_a_reachable_url(fake_http):
    fake_http.respond(ENTRY_URL, PAGE)

    assert probe_url(ENTRY_URL) == (True, "HTTP 200")


def test_probe_uses_the_configured_probe_timeout(fake_http):
    apply_browser_config(BrowserConfig(probe_timeout_seconds=4.0))
    fake_http.respond(ENTRY_URL, PAGE)

    probe_url(ENTRY_URL)

    assert fake_http.calls[-1].timeout == 4.0


def test_probe_retries_a_rejected_request_with_the_browser(fake_http, monkeypatch):
    fake_http.respond(ENTRY_URL, "denied", status_code=403)
    use_browser(monkeypatch)

    assert probe_url(ENTRY_URL) == (True, "requests: HTTP 403; browser: ok")


def test_probe_retries_a_network_error_with_the_browser(fake_http, monkeypatch):
    fake_http.fail(ENTRY_URL, requests.ConnectionError("refused"))
    use_browser(monkeypatch)

    reachable, detail = probe_url(ENTRY_URL)

    assert reachable is True
    assert detail.startswith("requests: refused")
    assert detail.endswith("browser: ok")


def test_probe_fails_when_no_browser_can_confirm(fake_http, monkeypatch):
    fake_http.respond(ENTRY_URL, "denied", status_code=403)
    use_browser(monkeypatch, available=False)

    assert probe_url(ENTRY_URL) == (False, "requests: HTTP 403")


def test_probe_reports_both_failures(fake_http, monkeypatch):
    fake_http.respond(ENTRY_URL, "denied", status_code=503)
    use_browser(monkeypatch, result=RuntimeError("challenge page"))

    reachable, detail = probe_url(ENTRY_URL)

    assert reachable is False
    assert detail == "requests: HTTP 503; browser: challenge page"
