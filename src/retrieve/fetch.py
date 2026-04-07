import requests  # type: ignore[import-untyped]

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_html(url: str, *, timeout_seconds: float = 20.0) -> str:
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


def probe_url(url: str, *, timeout_seconds: float = 10.0) -> tuple[bool, str]:
    try:
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout_seconds,
            allow_redirects=True,
        )
    except requests.RequestException as error:
        return False, str(error)

    if response.status_code >= 400:
        return False, f"HTTP {response.status_code}"
    return True, f"HTTP {response.status_code}"
