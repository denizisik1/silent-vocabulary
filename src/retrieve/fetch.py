import os

import requests  # type: ignore[import-untyped]

from browser_config import get_browser_config
from retrieve.browser_fetch import ensure_browser_ready, fetch_html_via_browser
from retrieve.headword import WantedIpa
from retrieve.http_headers import browser_headers, origin_url
from retrieve.parse import looks_like_challenge, page_title
from retrieve.progress import report_progress
from retrieve.strategy import FETCH_METHOD_BASIC, FETCH_METHOD_BROWSER


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _warmup_enabled() -> bool:
    return _env_bool("SILENT_VOCABULARY_HTTP_WARMUP", True)


def _fetch_timeout_seconds() -> float:
    return get_browser_config().fetch_timeout_seconds


def _probe_timeout_seconds() -> float:
    return get_browser_config().probe_timeout_seconds


def fetch_html_basic(url: str, *, timeout_seconds: float | None = None) -> str:
    if timeout_seconds is None:
        timeout_seconds = _fetch_timeout_seconds()
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
    page_html = response.content.decode(encoding, errors="replace")
    if looks_like_challenge(page_html):
        raise RuntimeError(
            f"HTTP {response.status_code} but a bot challenge for {url} "
            f"(title={page_title(page_html)!r})"
        )

    report_progress(f"plain request answered {len(page_html)} bytes for {url}")
    return page_html


def fetch_html_browser(
    url: str,
    *,
    timeout_seconds: float | None = None,
    wanted: WantedIpa | None = None,
) -> str:
    if timeout_seconds is None:
        timeout_seconds = _fetch_timeout_seconds()
    if not ensure_browser_ready():
        raise RuntimeError(
            "Browser fetch needs Chrome, Chromium, or Brave. "
            "Install one from Settings, or set a browser path there."
        )
    extra = get_browser_config().extra_timeout_seconds
    return fetch_html_via_browser(
        url,
        timeout_seconds=timeout_seconds + extra,
        wanted=wanted,
    )


def fetch_html_with_method(
    url: str,
    method: str,
    *,
    timeout_seconds: float | None = None,
    wanted: WantedIpa | None = None,
) -> str:
    if method == FETCH_METHOD_BASIC:
        return fetch_html_basic(url, timeout_seconds=timeout_seconds)
    if method == FETCH_METHOD_BROWSER:
        return fetch_html_browser(url, timeout_seconds=timeout_seconds, wanted=wanted)
    raise ValueError(f"Unknown fetch method: {method}")


def fetch_html(
    url: str,
    *,
    timeout_seconds: float | None = None,
    wanted: WantedIpa | None = None,
) -> str:
    basic_error: Exception | None = None
    try:
        return fetch_html_basic(url, timeout_seconds=timeout_seconds)
    except (RuntimeError, requests.RequestException) as error:
        basic_error = error

    try:
        return fetch_html_browser(url, timeout_seconds=timeout_seconds, wanted=wanted)
    except Exception as browser_error:
        basic_detail = str(basic_error) if basic_error else "unknown"
        raise RuntimeError(
            "Fetch failed via basic " f"({basic_detail}) and browser ({browser_error})"
        ) from browser_error


def probe_url(url: str, *, timeout_seconds: float | None = None) -> tuple[bool, str]:
    if timeout_seconds is None:
        timeout_seconds = _probe_timeout_seconds()
    try:
        response = requests.get(
            url,
            headers=browser_headers(url),
            timeout=timeout_seconds,
            allow_redirects=True,
        )
    except requests.RequestException as error:
        return _probe_with_browser(url, timeout_seconds, f"requests: {error}")

    if response.status_code >= 400:
        return _probe_with_browser(
            url,
            timeout_seconds,
            f"requests: HTTP {response.status_code}",
        )
    return True, f"HTTP {response.status_code}"


def _probe_with_browser(
    url: str,
    timeout_seconds: float,
    requests_detail: str,
) -> tuple[bool, str]:
    if not ensure_browser_ready():
        return False, requests_detail

    try:
        fetch_html_via_browser(
            url,
            timeout_seconds=timeout_seconds + get_browser_config().extra_timeout_seconds,
        )
    except Exception as error:  # pylint: disable=broad-exception-caught
        return False, f"{requests_detail}; browser: {error}"
    return True, f"{requests_detail}; browser: ok"
