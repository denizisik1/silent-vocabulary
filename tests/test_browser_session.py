import pytest

from retrieve import browser_session
from retrieve.browser_page import PageNotReady
from retrieve.browser_session import (
    APP_PROFILE_NAME,
    BULK_PROFILE_NAME,
    close_browser_session,
    current_profile_dir,
    is_browser_session_open,
    reused_browser_session,
    run_with_browser,
)


class FakeBrowser:
    def __init__(self, log):
        self._log = log
        self.stopped = False

    async def stop(self):
        self.stopped = True
        self._log.append("stop")


BROWSER_LOG: list[str] = []


@pytest.fixture(autouse=True)
def fake_browser(monkeypatch):
    BROWSER_LOG.clear()

    async def fake_start():
        BROWSER_LOG.append("start")
        return FakeBrowser(BROWSER_LOG)

    monkeypatch.setattr(browser_session, "_start_browser", fake_start)
    yield
    close_browser_session()


def read_page(page_html):
    async def work(browser):
        assert isinstance(browser, FakeBrowser)
        return page_html

    return work


def test_without_a_session_every_fetch_gets_its_own_browser():
    assert run_with_browser(read_page("first")) == "first"
    assert run_with_browser(read_page("second")) == "second"

    assert BROWSER_LOG == ["start", "stop", "start", "stop"]
    assert not is_browser_session_open()


def test_a_session_starts_one_browser_and_keeps_it():
    with reused_browser_session():
        assert run_with_browser(read_page("first")) == "first"
        assert run_with_browser(read_page("second")) == "second"
        assert run_with_browser(read_page("third")) == "third"
        assert is_browser_session_open()

    assert BROWSER_LOG == ["start", "stop"]
    assert not is_browser_session_open()


def test_a_session_starts_no_browser_until_one_is_needed():
    with reused_browser_session():
        assert not is_browser_session_open()

    assert not BROWSER_LOG


def test_a_page_that_never_arrives_keeps_the_browser():
    def stalled_work(_browser):
        raise PageNotReady("Browser fetch timed out")

    with reused_browser_session():
        for _attempt in range(3):
            with pytest.raises(PageNotReady):
                run_with_browser(stalled_work)
        assert is_browser_session_open()

    assert BROWSER_LOG == ["start", "stop"]


def test_a_bulk_run_and_the_app_keep_their_own_lasting_profile():
    app_profile = current_profile_dir()

    with reused_browser_session():
        bulk_profile = current_profile_dir()

    assert app_profile.name == APP_PROFILE_NAME
    assert bulk_profile.name == BULK_PROFILE_NAME
    assert app_profile.parent == bulk_profile.parent


def test_a_broken_browser_is_dropped_so_the_next_one_is_fresh():
    def failing_work(_browser):
        raise RuntimeError("websocket closed")

    with reused_browser_session():
        with pytest.raises(RuntimeError, match="websocket closed"):
            run_with_browser(failing_work)
        assert not is_browser_session_open()

        assert run_with_browser(read_page("after")) == "after"

    assert BROWSER_LOG == ["start", "stop", "start", "stop"]
