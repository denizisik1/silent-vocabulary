from collections.abc import Callable
from functools import partial
from typing import Any

from browser_config import get_browser_config
from browser_support import find_browser_path
from retrieve.browser_page import read_ready_page
from retrieve.browser_session import run_with_browser
from retrieve.headword import WantedIpa

_EnsureCallback = Callable[[], bool]
_ensure_callback: _EnsureCallback | None = None  # pylint: disable=invalid-name
_install_declined = False  # pylint: disable=invalid-name

_MISSING_BROWSER_MESSAGE = (
    "No Chrome/Chromium/Brave browser binary was found for browser fetch. "
    "Install one from Settings, or set a browser path there."
)


def browser_available() -> bool:
    return find_browser_path() is not None


def set_browser_ensure_callback(callback: _EnsureCallback | None) -> None:
    global _ensure_callback  # pylint: disable=global-statement
    _ensure_callback = callback


def reset_browser_ensure_state() -> None:
    global _install_declined  # pylint: disable=global-statement
    _install_declined = False


def ensure_browser_ready() -> bool:
    global _install_declined  # pylint: disable=global-statement
    if browser_available():
        return True
    if _install_declined:
        return False
    if _ensure_callback is None:
        return False
    approved = _ensure_callback()
    if not approved:
        _install_declined = True
        return False
    return browser_available()


async def _open_and_read(
    browser: Any,
    *,
    url: str,
    timeout_seconds: float,
    wanted: WantedIpa | None,
) -> str:
    page = await browser.get(url)
    return await read_ready_page(page, url, timeout_seconds=timeout_seconds, wanted=wanted)


def _browser_wait_seconds(timeout_seconds: float | None) -> float:
    configured = get_browser_config().wait_seconds
    if timeout_seconds is None:
        return configured
    return max(timeout_seconds, configured)


def fetch_html_via_browser(
    url: str,
    *,
    timeout_seconds: float | None = None,
    wanted: WantedIpa | None = None,
) -> str:
    if not ensure_browser_ready():
        raise RuntimeError(_MISSING_BROWSER_MESSAGE)

    work = partial(
        _open_and_read,
        url=url,
        timeout_seconds=_browser_wait_seconds(timeout_seconds),
        wanted=wanted,
    )
    try:
        return run_with_browser(work)
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(f"Browser fetch failed for {url}: {error}") from error
