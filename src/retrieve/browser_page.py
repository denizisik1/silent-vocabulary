import asyncio
import time
from typing import Any

from retrieve.headword import WantedIpa
from retrieve.parse import extract_ipa_from_html, looks_like_challenge, page_title
from retrieve.progress import KIND_NOTE, report_progress

_CONSENT_LABELS = ("Accept all", "Alle akzeptieren", "Accept", "Zustimmen")
_POLL_SECONDS = 1.0
_CHALLENGE_TIMEOUT_SECONDS = 15.0
_SETTLED_POLLS = 2


class PageNotReady(RuntimeError):
    """The page never showed what was asked for. The browser itself is still fine."""


def page_holds_wanted(html: str, wanted: WantedIpa | None) -> bool:
    if wanted is None or not wanted.find_by:
        return False
    try:
        extract_ipa_from_html(html, wanted.find_by, wanted.word)
    except Exception:  # pylint: disable=broad-exception-caught
        return False
    return True


async def read_page_title(page: Any) -> str:
    try:
        evaluated = await page.evaluate("document.title")
    except Exception:  # pylint: disable=broad-exception-caught
        return ""
    return evaluated if isinstance(evaluated, str) else ""


async def read_page_html(page: Any, url: str) -> str:
    try:
        return await page.get_content()
    except Exception as error:
        raise RuntimeError(f"Browser fetch failed reading {url}: {error}") from error


async def dismiss_consent_dialog(page: Any) -> str | None:
    for label in _CONSENT_LABELS:
        try:
            element = await page.find(label, best_match=True, timeout=1)
        except Exception:  # nosec B112 # pylint: disable=broad-exception-caught
            continue
        if element is None:
            continue
        try:
            await element.click()
        except Exception:  # nosec B112 # pylint: disable=broad-exception-caught
            continue
        return label
    return None


async def tick_cloudflare_checkbox(page: Any, timeout_seconds: float) -> bool:
    if timeout_seconds < 1:
        return False
    try:
        await page.verify_cf(timeout=min(timeout_seconds, _CHALLENGE_TIMEOUT_SECONDS))
    except Exception:  # pylint: disable=broad-exception-caught
        return False
    return True


async def _nudge_stuck_page(
    page: Any,
    html: str,
    tried: set[str],
    remaining_seconds: float,
) -> str | None:
    if "consent" not in tried:
        tried.add("consent")
        label = await dismiss_consent_dialog(page)
        if label is not None:
            return f"browser clicked away a consent dialog ({label})"

    if "challenge" not in tried and looks_like_challenge(html):
        tried.add("challenge")
        if await tick_cloudflare_checkbox(page, remaining_seconds):
            return "browser ticked the Cloudflare checkbox"
    return None


async def read_ready_page(
    page: Any,
    url: str,
    *,
    timeout_seconds: float,
    wanted: WantedIpa | None = None,
) -> str:
    deadline = time.monotonic() + timeout_seconds
    tried: set[str] = set()
    waits = 0
    settled_polls = 0
    last_size = -1
    title = ""
    html = ""

    while time.monotonic() < deadline:
        html = await read_page_html(page, url)
        title = await read_page_title(page) or page_title(html)
        if page_holds_wanted(html, wanted):
            report_progress(f"browser read the pronunciation from {len(html)} bytes")
            return html

        remaining = deadline - time.monotonic()
        nudge = await _nudge_stuck_page(page, html, tried, remaining)
        if nudge is not None:
            report_progress(nudge, KIND_NOTE)
            continue

        if looks_like_challenge(html):
            settled_polls = 0
        elif len(html) == last_size:
            settled_polls += 1
            if settled_polls >= _SETTLED_POLLS:
                report_progress(f"browser settled at {len(html)} bytes, title {title!r}")
                return html
        else:
            settled_polls = 0
        last_size = len(html)

        waits += 1
        if waits == 1:
            report_progress(
                f"browser waiting on {title!r} ({len(html)} bytes so far, "
                f"up to {timeout_seconds:.0f}s)",
                KIND_NOTE,
            )
        await asyncio.sleep(_POLL_SECONDS)

    raise PageNotReady(f"Browser fetch timed out for {url} (title={title!r}, bytes={len(html)})")
