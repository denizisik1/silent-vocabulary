import os

import requests  # type: ignore[import-untyped]

from retrieve.playwright_fetch import fetch_html_playwright, playwright_available
from retrieve.strategy import FETCH_METHOD_BASIC, FETCH_METHOD_PLAYWRIGHT

DEFAULT_HEADERS = {
    "User-Agent": os.environ.get(
        "VIPA_HTTP_USER_AGENT",
        (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
    ),
    "Accept": os.environ.get(
        "VIPA_HTTP_ACCEPT",
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    ),
    "Accept-Language": os.environ.get("VIPA_HTTP_ACCEPT_LANGUAGE", "en-US,en;q=0.9"),
}

_FETCH_TIMEOUT_SECONDS = float(os.environ.get("VIPA_FETCH_TIMEOUT_SECONDS", "20"))
_PROBE_TIMEOUT_SECONDS = float(os.environ.get("VIPA_PROBE_TIMEOUT_SECONDS", "10"))
_PLAYWRIGHT_EXTRA_TIMEOUT_SECONDS = float(
    os.environ.get("VIPA_PLAYWRIGHT_EXTRA_TIMEOUT_SECONDS", "10")
)


def fetch_html_basic(url: str, *, timeout_seconds: float = _FETCH_TIMEOUT_SECONDS) -> str:
    response = requests.get(
        url,
        headers=DEFAULT_HEADERS,
        timeout=timeout_seconds,
        allow_redirects=True,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code} for {url}")

    encoding = response.apparent_encoding or response.encoding or "utf-8"
    return response.content.decode(encoding, errors="replace")


def fetch_html_browser(
    url: str,
    *,
    timeout_seconds: float = _FETCH_TIMEOUT_SECONDS,
) -> str:
    if not playwright_available():
        raise RuntimeError(
            "Playwright is not installed. Install it with: pip install playwright"
        )
    return fetch_html_playwright(
        url,
        timeout_seconds=timeout_seconds + _PLAYWRIGHT_EXTRA_TIMEOUT_SECONDS,
    )


def fetch_html_with_method(
    url: str,
    method: str,
    *,
    timeout_seconds: float = _FETCH_TIMEOUT_SECONDS,
) -> str:
    if method == FETCH_METHOD_BASIC:
        return fetch_html_basic(url, timeout_seconds=timeout_seconds)
    if method == FETCH_METHOD_PLAYWRIGHT:
        return fetch_html_browser(url, timeout_seconds=timeout_seconds)
    raise ValueError(f"Unknown fetch method: {method}")


def fetch_html(url: str, *, timeout_seconds: float = _FETCH_TIMEOUT_SECONDS) -> str:
    basic_error: Exception | None = None
    try:
        return fetch_html_basic(url, timeout_seconds=timeout_seconds)
    except (RuntimeError, requests.RequestException) as error:
        basic_error = error

    try:
        return fetch_html_browser(url, timeout_seconds=timeout_seconds)
    except Exception as playwright_error:
        basic_detail = str(basic_error) if basic_error else "unknown"
        raise RuntimeError(
            "Fetch failed via basic "
            f"({basic_detail}) and playwright ({playwright_error})"
        ) from playwright_error


def probe_url(url: str, *, timeout_seconds: float = _PROBE_TIMEOUT_SECONDS) -> tuple[bool, str]:
    try:
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout_seconds,
            allow_redirects=True,
        )
    except requests.RequestException as error:
        return _probe_with_playwright(url, timeout_seconds, f"requests: {error}")

    if response.status_code >= 400:
        return _probe_with_playwright(
            url,
            timeout_seconds,
            f"requests: HTTP {response.status_code}",
        )
    return True, f"HTTP {response.status_code}"


def _probe_with_playwright(
    url: str,
    timeout_seconds: float,
    requests_detail: str,
) -> tuple[bool, str]:
    if not playwright_available():
        return False, requests_detail

    try:
        fetch_html_playwright(
            url,
            timeout_seconds=timeout_seconds + _PLAYWRIGHT_EXTRA_TIMEOUT_SECONDS,
        )
    except Exception as error:
        return False, f"{requests_detail}; playwright: {error}"
    return True, f"{requests_detail}; playwright: ok"
