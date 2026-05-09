import os

import requests  # type: ignore[import-untyped]

from retrieve.playwright_fetch import fetch_html_playwright, playwright_available

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


def _fetch_html_requests(url: str, *, timeout_seconds: float) -> str:
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


def fetch_html(url: str, *, timeout_seconds: float = _FETCH_TIMEOUT_SECONDS) -> str:
    requests_error: Exception | None = None
    try:
        return _fetch_html_requests(url, timeout_seconds=timeout_seconds)
    except (RuntimeError, requests.RequestException) as error:
        requests_error = error

    if not playwright_available():
        detail = str(requests_error) if requests_error else "requests failed"
        raise RuntimeError(f"Fetch failed via requests ({detail})") from requests_error

    try:
        return fetch_html_playwright(
            url,
            timeout_seconds=timeout_seconds + _PLAYWRIGHT_EXTRA_TIMEOUT_SECONDS,
        )
    except Exception as playwright_error:
        requests_detail = str(requests_error) if requests_error else "unknown"
        raise RuntimeError(
            "Fetch failed via requests "
            f"({requests_detail}) and playwright ({playwright_error})"
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
