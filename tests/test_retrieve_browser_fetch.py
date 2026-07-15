import pytest

from browser_config import BrowserConfig, apply_browser_config
from retrieve.browser_fetch import (
    ensure_browser_ready,
    fetch_html_via_browser,
    reset_browser_ensure_state,
    set_browser_ensure_callback,
)
from retrieve.browser_page import page_holds_wanted
from retrieve.headword import WantedIpa

PAGE = '<html><span class="pron">[ˈaːbənt]</span></html>'
ENTRY_URL = "https://example.com/dict/Abend"
PRON = WantedIpa("pron")


@pytest.fixture(autouse=True)
def clean_browser_state():
    reset_browser_ensure_state()
    apply_browser_config(BrowserConfig())
    yield
    set_browser_ensure_callback(None)
    reset_browser_ensure_state()
    apply_browser_config(BrowserConfig())


def test_a_page_carrying_the_wanted_markup_is_ready():
    assert page_holds_wanted(PAGE, PRON)
    assert page_holds_wanted("<html><span class='pron'>[a]</span></html>", PRON)


def test_a_challenge_page_that_already_holds_the_entry_is_ready():
    assert page_holds_wanted('<html>cf-challenge<span class="pron">[a]</span></html>', PRON)


def test_a_page_without_the_wanted_markup_is_not_ready():
    assert not page_holds_wanted("<html>checking your browser</html>", PRON)
    assert not page_holds_wanted('<html><span class="phonetics">[a]</span></html>', PRON)


def test_a_page_holding_another_words_pronunciation_is_not_ready():
    page = '<html><h3>Zelt</h3><span class="pron">[tsɛlt]</span></html>'

    assert page_holds_wanted(page, WantedIpa("pron", "Zelt"))
    assert not page_holds_wanted(page, WantedIpa("pron", "abbrechen"))


def test_a_big_page_of_the_wrong_kind_is_not_ready():
    assert not page_holds_wanted("x" * 200_000, PRON)


def test_a_page_is_never_ready_without_something_to_look_for():
    assert not page_holds_wanted(PAGE, None)
    assert not page_holds_wanted(PAGE, WantedIpa(""))


def test_an_installed_browser_needs_no_prompt(monkeypatch):
    monkeypatch.setattr("retrieve.browser_fetch.browser_available", lambda: True)

    def unexpected_prompt():
        raise AssertionError("must not prompt when a browser is installed")

    set_browser_ensure_callback(unexpected_prompt)

    assert ensure_browser_ready() is True


def test_without_a_prompt_a_missing_browser_is_final(monkeypatch):
    monkeypatch.setattr("retrieve.browser_fetch.browser_available", lambda: False)

    assert ensure_browser_ready() is False


def test_an_approved_install_makes_the_browser_usable(monkeypatch):
    prompts = []
    monkeypatch.setattr("retrieve.browser_fetch.browser_available", lambda: bool(prompts))

    def approve():
        prompts.append("installed")
        return True

    set_browser_ensure_callback(approve)

    assert ensure_browser_ready() is True
    assert len(prompts) == 1


def test_an_approved_install_that_produced_nothing_still_fails(monkeypatch):
    monkeypatch.setattr("retrieve.browser_fetch.browser_available", lambda: False)
    set_browser_ensure_callback(lambda: True)

    assert ensure_browser_ready() is False


def test_a_declined_install_is_not_asked_again(monkeypatch):
    prompts = []
    monkeypatch.setattr("retrieve.browser_fetch.browser_available", lambda: False)

    def decline():
        prompts.append("declined")
        return False

    set_browser_ensure_callback(decline)

    assert ensure_browser_ready() is False
    assert ensure_browser_ready() is False
    assert len(prompts) == 1

    reset_browser_ensure_state()
    assert ensure_browser_ready() is False
    assert len(prompts) == 2


def use_async_fetch(monkeypatch, outcome):
    calls = []

    def fake_run_with_browser(work):
        calls.append((work.keywords["url"], work.keywords["timeout_seconds"]))
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr("retrieve.browser_fetch.ensure_browser_ready", lambda: True)
    monkeypatch.setattr("retrieve.browser_fetch.run_with_browser", fake_run_with_browser)
    return calls


def test_the_page_is_returned_and_waits_at_least_the_configured_time(monkeypatch):
    apply_browser_config(BrowserConfig(wait_seconds=90.0))
    calls = use_async_fetch(monkeypatch, PAGE)

    assert fetch_html_via_browser(ENTRY_URL, timeout_seconds=30.0) == PAGE
    assert calls == [(ENTRY_URL, 90.0)]


def test_a_longer_requested_timeout_wins(monkeypatch):
    apply_browser_config(BrowserConfig(wait_seconds=90.0))
    calls = use_async_fetch(monkeypatch, PAGE)

    fetch_html_via_browser(ENTRY_URL, timeout_seconds=120.0)

    assert calls == [(ENTRY_URL, 120.0)]


def test_a_missing_browser_is_reported_before_any_work(monkeypatch):
    monkeypatch.setattr("retrieve.browser_fetch.ensure_browser_ready", lambda: False)

    with pytest.raises(RuntimeError, match="No Chrome/Chromium/Brave browser binary"):
        fetch_html_via_browser(ENTRY_URL)


def test_unexpected_driver_errors_name_the_url(monkeypatch):
    use_async_fetch(monkeypatch, ValueError("websocket closed"))

    with pytest.raises(RuntimeError, match=f"Browser fetch failed for {ENTRY_URL}: websocket"):
        fetch_html_via_browser(ENTRY_URL)


def test_reported_browser_errors_are_passed_through_unchanged(monkeypatch):
    use_async_fetch(monkeypatch, RuntimeError("Browser fetch timed out for " + ENTRY_URL))

    with pytest.raises(RuntimeError, match="^Browser fetch timed out"):
        fetch_html_via_browser(ENTRY_URL)
