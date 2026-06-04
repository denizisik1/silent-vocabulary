import asyncio
import os
import time
from collections.abc import Callable

from stealth_browser import find_stealth_browser_path

_EnsureCallback = Callable[[], bool]
_ensure_callback: _EnsureCallback | None = None
_install_declined = False

_MISSING_BROWSER_MESSAGE = (
    "No Chrome/Chromium/Brave browser binary was found for stealth fetch. "
    "Install one, or set VIPA_STEALTH_BROWSER_PATH."
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


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _stealth_headless() -> bool:
    return _env_bool("VIPA_STEALTH_HEADLESS", False)


def _stealth_sandbox() -> bool:
    return _env_bool("VIPA_STEALTH_SANDBOX", False)


def _stealth_wait_seconds(timeout_seconds: float) -> float:
    configured = os.environ.get("VIPA_STEALTH_WAIT_SECONDS")
    if configured is None:
        return max(timeout_seconds, 60.0)
    return float(configured)


def _stealth_connect_timeout_seconds() -> float:
    return float(os.environ.get("VIPA_STEALTH_BROWSER_CONNECT_TIMEOUT", "1.0"))


def _stealth_connect_tries() -> int:
    return int(os.environ.get("VIPA_STEALTH_BROWSER_CONNECT_TRIES", "40"))


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

    browser_path = find_stealth_browser_path()
    start_kwargs: dict[str, object] = {
        "headless": _stealth_headless(),
        "sandbox": _stealth_sandbox(),
        "browser_connection_timeout": _stealth_connect_timeout_seconds(),
        "browser_connection_max_tries": _stealth_connect_tries(),
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


def fetch_html_stealth(url: str, *, timeout_seconds: float = 60.0) -> str:
    if not ensure_stealth_ready():
        raise RuntimeError(_MISSING_BROWSER_MESSAGE)
    wait_seconds = _stealth_wait_seconds(timeout_seconds)
    try:
        return asyncio.run(
            _fetch_html_stealth_async(url, timeout_seconds=wait_seconds)
        )
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(f"Stealth fetch failed for {url}: {error}") from error
