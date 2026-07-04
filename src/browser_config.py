from dataclasses import dataclass

DEFAULT_FETCH_TIMEOUT_SECONDS = 20.0
DEFAULT_PROBE_TIMEOUT_SECONDS = 10.0
DEFAULT_BROWSER_EXTRA_TIMEOUT_SECONDS = 40.0
DEFAULT_BROWSER_WAIT_SECONDS = 90.0
DEFAULT_BROWSER_CONNECT_TIMEOUT_SECONDS = 1.0
DEFAULT_BROWSER_CONNECT_TRIES = 40


@dataclass
class BrowserConfig:  # pylint: disable=too-many-instance-attributes
    headless: bool = False
    sandbox: bool = False
    wait_seconds: float = DEFAULT_BROWSER_WAIT_SECONDS
    extra_timeout_seconds: float = DEFAULT_BROWSER_EXTRA_TIMEOUT_SECONDS
    connect_timeout_seconds: float = DEFAULT_BROWSER_CONNECT_TIMEOUT_SECONDS
    connect_tries: int = DEFAULT_BROWSER_CONNECT_TRIES
    browser_path: str = ""
    fetch_timeout_seconds: float = DEFAULT_FETCH_TIMEOUT_SECONDS
    probe_timeout_seconds: float = DEFAULT_PROBE_TIMEOUT_SECONDS


_RUNTIME_BROWSER = BrowserConfig()


def get_browser_config() -> BrowserConfig:
    return _RUNTIME_BROWSER


def apply_browser_config(browser: BrowserConfig) -> None:
    global _RUNTIME_BROWSER  # pylint: disable=global-statement
    _RUNTIME_BROWSER = BrowserConfig(
        headless=browser.headless,
        sandbox=browser.sandbox,
        wait_seconds=browser.wait_seconds,
        extra_timeout_seconds=browser.extra_timeout_seconds,
        connect_timeout_seconds=browser.connect_timeout_seconds,
        connect_tries=browser.connect_tries,
        browser_path=browser.browser_path,
        fetch_timeout_seconds=browser.fetch_timeout_seconds,
        probe_timeout_seconds=browser.probe_timeout_seconds,
    )
