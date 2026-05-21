import asyncio
import os
import time


def stealth_available() -> bool:
    try:
        import zendriver  # noqa: F401
    except ImportError:
        return False
    return True


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _stealth_headless() -> bool:
    return _env_bool("VIPA_STEALTH_HEADLESS", False)


def _stealth_wait_seconds(timeout_seconds: float) -> float:
    configured = os.environ.get("VIPA_STEALTH_WAIT_SECONDS")
    if configured is None:
        return max(timeout_seconds, 60.0)
    return float(configured)


def _page_looks_ready(title: str | None, html: str) -> bool:
    cleaned_title = (title or "").strip().lower()
    if "just a moment" in cleaned_title:
        return False
    if "cf-challenge" in html.lower() and "class=\"pron\"" not in html:
        return False
    return (
        'class="pron"' in html
        or "class='pron'" in html
        or "phonetics" in html
        or len(html) > 80_000
    )


async def _fetch_html_stealth_async(url: str, *, timeout_seconds: float) -> str:
    import zendriver as zd

    browser = await zd.start(headless=_stealth_headless())
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
    if not stealth_available():
        raise RuntimeError(
            "zendriver is not installed. Install it with: pip install zendriver"
        )
    wait_seconds = _stealth_wait_seconds(timeout_seconds)
    try:
        return asyncio.run(
            _fetch_html_stealth_async(url, timeout_seconds=wait_seconds)
        )
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(f"Stealth fetch failed for {url}: {error}") from error
