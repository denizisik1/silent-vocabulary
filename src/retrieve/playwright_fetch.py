def playwright_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        return False
    return True


def fetch_html_playwright(url: str, *, timeout_seconds: float = 30.0) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError(
            "Playwright is not installed. Install it with: pip install playwright"
        ) from error

    timeout_ms = int(timeout_seconds * 1000)
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception as error:
            raise RuntimeError(
                "Playwright browser is missing. Run: playwright install chromium"
            ) from error

        try:
            page = browser.new_page()
            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=timeout_ms,
            )
            if response is not None and response.status >= 400:
                raise RuntimeError(f"HTTP {response.status} for {url}")
            return page.content()
        finally:
            browser.close()
