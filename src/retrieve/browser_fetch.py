import asyncio
import time
from collections.abc import Callable

from browser_config import get_browser_config
from browser_support import find_browser_path

_EnsureCallback = Callable[[], bool]
_ensure_callback: _EnsureCallback | None = None
_install_declined = False

_MISSING_BROWSER_MESSAGE = (
    "No Chrome/Chromium/Brave browser binary was found for browser fetch. "
    "Install one from Settings, or set a browser path there."
)


def browser_available() -> bool:
    return find_browser_path() is not None


def set_browser_ensure_callback(callback: _EnsureCallback | None) -> None:
    global _ensure_callback
    _ensure_callback = callback


def reset_browser_ensure_state() -> None:
    global _install_declined
    _install_declined = False


def ensure_browser_ready() -> bool:
    global _install_declined
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


def _page_looks_ready(title: str | None, html: str) -> bool:
    cleaned_title = (title or "").strip().lower()
    if "just a moment" in cleaned_title:
        return False
    if "cf-challenge" in html.lower() and 'class="pron"' not in html:
        return False
    return (
        'class="pron"' in html
        or "class='pron'" in html
        or "phonetics" in html
        or len(html) > 80_000
    )


async def _fetch_html_browser_async(url: str, *, timeout_seconds: float) -> str:
    import zendriver as zd

    browser_settings = get_browser_config()
    browser_path = find_browser_path()
    start_kwargs: dict[str, object] = {
        "headless": browser_settings.headless,
        "sandbox": browser_settings.sandbox,
        "browser_connection_timeout": browser_settings.connect_timeout_seconds,
        "browser_connection_max_tries": browser_settings.connect_tries,
    }
    if browser_path is not None:
        start_kwargs["browser_executable_path"] = browser_path

    browser = await zd.start(**start_kwargs)
    try:
        page = await browser.get(url)
        deadline = time.monotonic() + timeout_seconds
        last_title = ""
        last_html = ""
        while time.monotonic() < deadline:
            try:
                last_title = await page.evaluate("document.title")
            except Exception:
                last_title = ""
            try:
                last_html = await page.get_content()
            except Exception as error:
                raise RuntimeError(f"Browser fetch failed reading {url}: {error}") from error

            if _page_looks_ready(last_title, last_html):
                return last_html
            await asyncio.sleep(1.0)

        raise RuntimeError(
            f"Browser fetch timed out for {url} " f"(title={last_title!r}, bytes={len(last_html)})"
        )
    finally:
        await browser.stop()


def fetch_html_via_browser(url: str, *, timeout_seconds: float | None = None) -> str:
    if not ensure_browser_ready():
        raise RuntimeError(_MISSING_BROWSER_MESSAGE)
    browser_settings = get_browser_config()
    wait_seconds = (
        browser_settings.wait_seconds
        if timeout_seconds is None
        else max(timeout_seconds, browser_settings.wait_seconds)
    )
    try:
        return asyncio.run(_fetch_html_browser_async(url, timeout_seconds=wait_seconds))
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(f"Browser fetch failed for {url}: {error}") from error
