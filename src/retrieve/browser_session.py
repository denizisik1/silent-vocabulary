import asyncio
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from browser_config import get_browser_config
from browser_support import browser_profile_dir, find_browser_path
from retrieve.browser_page import PageNotReady
from retrieve.progress import KIND_BAD, KIND_NOTE, report_progress

BrowserWork = Callable[[Any], Awaitable[str]]

BULK_PROFILE_NAME = "bulk"
APP_PROFILE_NAME = "app"

_session_loop: asyncio.AbstractEventLoop | None = None  # pylint: disable=invalid-name,line-too-long  # mutable module state  # noqa: E501  # fmt: skip
_session_browser: Any = None  # pylint: disable=invalid-name  # mutable module state
_session_wanted = False  # pylint: disable=invalid-name  # mutable module state


def current_profile_dir() -> Path:
    name = BULK_PROFILE_NAME if _session_wanted else APP_PROFILE_NAME
    return browser_profile_dir(name)


async def _start_browser() -> Any:
    import zendriver as zd  # pylint: disable=import-outside-toplevel  # only if a session starts

    browser_settings = get_browser_config()
    profile = current_profile_dir()
    profile.mkdir(parents=True, exist_ok=True)
    return await zd.start(
        headless=browser_settings.headless,
        sandbox=browser_settings.sandbox,
        browser_executable_path=find_browser_path(),
        browser_connection_timeout=browser_settings.connect_timeout_seconds,
        browser_connection_max_tries=browser_settings.connect_tries,
        user_data_dir=str(profile),
    )


def is_browser_session_open() -> bool:
    return _session_browser is not None


def _open_session() -> None:
    global _session_loop, _session_browser  # pylint: disable=global-statement  # one reused browser
    loop = asyncio.new_event_loop()
    try:
        browser = loop.run_until_complete(_start_browser())
    except BaseException:
        loop.close()
        raise
    _session_loop = loop
    _session_browser = browser
    report_progress("browser started, it stays open for the rest of the run", KIND_NOTE)
    report_progress(f"browser profile {current_profile_dir()}, it keeps the site cookies")


def close_browser_session() -> None:
    global _session_loop, _session_browser  # pylint: disable=global-statement  # one reused browser
    loop = _session_loop
    browser = _session_browser
    _session_loop = None
    _session_browser = None
    if loop is None or browser is None:
        return

    try:
        loop.run_until_complete(browser.stop())
    except Exception as error:  # pylint: disable=broad-exception-caught  # still close the loop
        report_progress(f"browser close failed: {error}", KIND_NOTE)
    finally:
        loop.close()
    report_progress("browser closed", KIND_NOTE)


@contextmanager
def reused_browser_session() -> Iterator[None]:
    global _session_wanted  # pylint: disable=global-statement  # bulk vs one-shot profile
    previous = _session_wanted
    _session_wanted = True
    try:
        yield
    finally:
        _session_wanted = previous
        close_browser_session()


async def _run_in_own_browser(work: BrowserWork) -> str:
    browser = await _start_browser()
    try:
        return await work(browser)
    finally:
        await browser.stop()


def _run_in_session(work: BrowserWork) -> str:
    if _session_browser is None:
        _open_session()
    else:
        report_progress("browser reused, no new window needed", KIND_NOTE)

    loop = _session_loop
    assert loop is not None
    try:
        return loop.run_until_complete(work(_session_browser))
    except PageNotReady:
        raise
    except BaseException:
        close_browser_session()
        report_progress("browser looks broken, the next word starts a fresh one", KIND_BAD)
        raise


def run_with_browser(work: BrowserWork) -> str:
    if _session_wanted:
        return _run_in_session(work)
    return asyncio.run(_run_in_own_browser(work))
