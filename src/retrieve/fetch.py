import os

import requests  # type: ignore[import-untyped]

from retrieve.http_headers import browser_headers, origin_url
from retrieve.stealth_fetch import ensure_stealth_ready, fetch_html_stealth
from retrieve.strategy import FETCH_METHOD_BASIC, FETCH_METHOD_STEALTH

_FETCH_TIMEOUT_SECONDS = float(os.environ.get("VIPA_FETCH_TIMEOUT_SECONDS", "20"))
_PROBE_TIMEOUT_SECONDS = float(os.environ.get("VIPA_PROBE_TIMEOUT_SECONDS", "10"))
_STEALTH_EXTRA_TIMEOUT_SECONDS = float(
    os.environ.get("VIPA_STEALTH_EXTRA_TIMEOUT_SECONDS", "40")
)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _warmup_enabled() -> bool:
    return _env_bool("VIPA_HTTP_WARMUP", True)


def fetch_html_basic(url: str, *, timeout_seconds: float = _FETCH_TIMEOUT_SECONDS) -> str:
    headers = browser_headers(url)
    with requests.Session() as session:
        session.headers.update(headers)
        if _warmup_enabled():
            try:
                session.get(
                    origin_url(url),
                    timeout=min(timeout_seconds, 10.0),
                    allow_redirects=True,
                )
            except requests.RequestException:
                pass
            session.headers["Sec-Fetch-Site"] = "same-origin"
            session.headers["Referer"] = origin_url(url)

        response = session.get(
            url,
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
    if not ensure_stealth_ready():
        raise RuntimeError(
            "Stealth fetch needs Chrome, Chromium, or Brave. "
            "Install one, or set VIPA_STEALTH_BROWSER_PATH."
        )
    return fetch_html_stealth(
        url,
        timeout_seconds=timeout_seconds + _STEALTH_EXTRA_TIMEOUT_SECONDS,
    )


def fetch_html_with_method(
    url: str,
    method: str,
    *,
    timeout_seconds: float = _FETCH_TIMEOUT_SECONDS,
) -> str:
    if method == FETCH_METHOD_BASIC:
        return fetch_html_basic(url, timeout_seconds=timeout_seconds)
    if method == FETCH_METHOD_STEALTH:
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
    except Exception as stealth_error:
        basic_detail = str(basic_error) if basic_error else "unknown"
        raise RuntimeError(
            "Fetch failed via basic "
            f"({basic_detail}) and stealth ({stealth_error})"
        ) from stealth_error


def probe_url(url: str, *, timeout_seconds: float = _PROBE_TIMEOUT_SECONDS) -> tuple[bool, str]:
    try:
        response = requests.get(
            url,
            headers=browser_headers(url),
            timeout=timeout_seconds,
            allow_redirects=True,
        )
    except requests.RequestException as error:
        return _probe_with_stealth(url, timeout_seconds, f"requests: {error}")

    if response.status_code >= 400:
        return _probe_with_stealth(
            url,
            timeout_seconds,
            f"requests: HTTP {response.status_code}",
        )
    return True, f"HTTP {response.status_code}"


def _probe_with_stealth(
    url: str,
    timeout_seconds: float,
    requests_detail: str,
) -> tuple[bool, str]:
    if not ensure_stealth_ready():
        return False, requests_detail

    try:
        fetch_html_stealth(
            url,
            timeout_seconds=timeout_seconds + _STEALTH_EXTRA_TIMEOUT_SECONDS,
        )
    except Exception as error:
        return False, f"{requests_detail}; stealth: {error}"
    return True, f"{requests_detail}; stealth: ok"
