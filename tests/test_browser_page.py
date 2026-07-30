import asyncio

import pytest

from retrieve.browser_page import dismiss_consent_dialog, read_ready_page
from retrieve.headword import WantedIpa
from retrieve.progress import retrieve_reporter

URL = "https://example.com/dict/Abend"
ENTRY_PAGE = '<html><title>Abend</title><span class="pron">[ˈaːbənt]</span></html>'
CONSENT_PAGE = "<html><title>Privacy</title>loading</html>"
CHALLENGE_PAGE = '<html><title>Wait</title><div class="cf-challenge">verify</div></html>'


class FakeElement:
    def __init__(self, log, label):
        self._log = log
        self._label = label

    async def click(self):
        self._log.append(f"click {self._label}")


class FakePage:
    def __init__(self, pages, *, title="Abend", consent_label=None):
        self._pages = list(pages)
        self._title = title
        self._consent_label = consent_label
        self.log = []

    async def evaluate(self, _script):
        return self._title

    async def get_content(self):
        if len(self._pages) > 1:
            return self._pages.pop(0)
        return self._pages[0]

    async def find(self, text, **_options):
        self.log.append(f"find {text}")
        if text != self._consent_label:
            raise TimeoutError(f"no element for {text}")
        return FakeElement(self.log, text)


class FakeCloudflarePage(FakePage):
    async def verify_cf(self, timeout=15.0):
        self.log.append(f"verify_cf {timeout}")


@pytest.fixture(autouse=True)
def quick_polling(monkeypatch):
    monkeypatch.setattr("retrieve.browser_page._POLL_SECONDS", 0.01)


def read(page, *, timeout_seconds=5.0, wanted=WantedIpa("pron", "Abend")):
    return asyncio.run(read_ready_page(page, URL, timeout_seconds=timeout_seconds, wanted=wanted))


def test_a_page_holding_the_wanted_markup_is_returned_at_once():
    page = FakePage([ENTRY_PAGE])

    assert read(page) == ENTRY_PAGE
    assert not page.log


def test_a_page_that_stops_changing_is_returned_without_the_wanted_markup(progress_log):
    page = FakePage([CONSENT_PAGE])

    with retrieve_reporter(progress_log.record):
        assert read(page) == CONSENT_PAGE

    assert any("settled" in message for message in progress_log.messages())


def test_a_page_still_growing_is_waited_for():
    half_built = '<html><title>Abend</title><span class="pron">'
    page = FakePage([half_built, half_built + " ", ENTRY_PAGE])

    assert read(page) == ENTRY_PAGE


def test_a_consent_dialog_is_clicked_away_before_giving_up(progress_log):
    page = FakePage([CONSENT_PAGE, ENTRY_PAGE], consent_label="Accept all")

    with retrieve_reporter(progress_log.record):
        assert read(page) == ENTRY_PAGE

    assert page.log == ["find Accept all", "click Accept all"]
    assert "browser clicked away a consent dialog (Accept all)" in progress_log.messages()


def test_a_cloudflare_wall_gets_its_checkbox_ticked(progress_log):
    page = FakeCloudflarePage([CHALLENGE_PAGE, ENTRY_PAGE], title="")

    with retrieve_reporter(progress_log.record):
        assert read(page) == ENTRY_PAGE

    assert any(entry.startswith("verify_cf ") for entry in page.log)
    assert "browser ticked the Cloudflare checkbox" in progress_log.messages()


def test_a_browser_that_cannot_tick_the_checkbox_keeps_waiting():
    page = FakePage([CHALLENGE_PAGE, ENTRY_PAGE], title="")

    assert read(page) == ENTRY_PAGE


def test_a_page_that_never_arrives_names_the_title_and_size():
    page = FakePage([CONSENT_PAGE], title="Just a moment...")

    with pytest.raises(RuntimeError, match="Browser fetch timed out"):
        read(page, timeout_seconds=0.0)


def test_a_page_without_any_known_consent_button_is_left_alone():
    page = FakePage([CONSENT_PAGE])

    assert asyncio.run(dismiss_consent_dialog(page)) is None
    assert page.log == ["find Accept all", "find Alle akzeptieren", "find Accept", "find Zustimmen"]
