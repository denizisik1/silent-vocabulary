import asyncio
import time
from collections.abc import Callable

from stealth_config import get_stealth_config
from stealth_browser import find_stealth_browser_path

_EnsureCallback = Callable[[], bool]
_ensure_callback: _EnsureCallback | None = None
_install_declined = False

_MISSING_BROWSER_MESSAGE = (
    "No Chrome/Chromium/Brave browser binary was found for stealth fetch. "
    "Install one from Settings, or set a browser path there."
)


def stealth_browser_available() -> bool:
    return find_stealth_browser_path() is not None


def set_stealth_ensure_callback(callback: _EnsureCallback | None) -> None:
    global _ensure_callback
    _ensure_callback = callback


def reset_stealth_ensure_state() -> None:
    global _install_declined
    _install_declined = False


def ensure_stealth_ready() -> bool:
    global _install_declined
    if stealth_browser_available():
        return True
    if _install_declined:
        return False
    if _ensure_callback is None:
        return False
    approved = _ensure_callback()
    if not approved:
        _install_declined = True
        return False
    return stealth_browser_available()


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


async def _fetch_html_stealth_async(url: str, *, timeout_seconds: float) -> str:
    import zendriver as zd

    stealth = get_stealth_config()
    browser_path = find_stealth_browser_path()
    start_kwargs: dict[str, object] = {
        "headless": stealth.headless,
        "sandbox": stealth.sandbox,
        "browser_connection_timeout": stealth.connect_timeout_seconds,
        "browser_connection_max_tries": stealth.connect_tries,
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
                raise RuntimeError(f"Stealth browser failed reading {url}: {error}") from error

            if _page_looks_ready(last_title, last_html):
                return last_html
            await asyncio.sleep(1.0)

        raise RuntimeError(
            f"Stealth browser timed out for {url} "
            f"(title={last_title!r}, bytes={len(last_html)})"
        )
    finally:
        await browser.stop()


def fetch_html_stealth(url: str, *, timeout_seconds: float | None = None) -> str:
    if not ensure_stealth_ready():
        raise RuntimeError(_MISSING_BROWSER_MESSAGE)
    stealth = get_stealth_config()
    wait_seconds = (
        stealth.wait_seconds
        if timeout_seconds is None
        else max(timeout_seconds, stealth.wait_seconds)
    )
    try:
        return asyncio.run(
            _fetch_html_stealth_async(url, timeout_seconds=wait_seconds)
        )
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(f"Stealth fetch failed for {url}: {error}") from error
