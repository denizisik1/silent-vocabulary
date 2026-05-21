from urllib.parse import urlparse, urlunparse
import os


_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def origin_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Cannot derive origin from URL: {url}")
    return urlunparse((parsed.scheme, parsed.netloc, "/", "", "", ""))


def browser_headers(url: str) -> dict[str, str]:
    referer = os.environ.get("VIPA_HTTP_REFERER", "").strip() or origin_url(url)
    user_agent = os.environ.get("VIPA_HTTP_USER_AGENT", _DEFAULT_USER_AGENT)
    accept = os.environ.get(
        "VIPA_HTTP_ACCEPT",
        (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
    )
    accept_language = os.environ.get(
        "VIPA_HTTP_ACCEPT_LANGUAGE",
        "en-US,en;q=0.9",
    )
    return {
        "User-Agent": user_agent,
        "Accept": accept,
        "Accept-Language": accept_language,
        "Accept-Encoding": os.environ.get(
            "VIPA_HTTP_ACCEPT_ENCODING",
            "gzip, deflate, br, zstd",
        ),
        "Referer": referer,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin" if referer.startswith(origin_url(url)) else "cross-site",
        "Sec-Fetch-User": "?1",
        "Sec-CH-UA": os.environ.get(
            "VIPA_HTTP_SEC_CH_UA",
            '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        ),
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": os.environ.get("VIPA_HTTP_SEC_CH_UA_PLATFORM", '"Linux"'),
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "DNT": "1",
    }


def browser_locale(accept_language: str | None = None) -> str:
    raw = accept_language or os.environ.get("VIPA_HTTP_ACCEPT_LANGUAGE", "en-US,en;q=0.9")
    primary = raw.split(",")[0].strip()
    if not primary:
        return "en-US"
    if ";" in primary:
        primary = primary.split(";", 1)[0].strip()
    return primary or "en-US"
