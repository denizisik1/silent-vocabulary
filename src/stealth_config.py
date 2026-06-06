from dataclasses import dataclass

DEFAULT_FETCH_TIMEOUT_SECONDS = 20.0
DEFAULT_PROBE_TIMEOUT_SECONDS = 10.0
DEFAULT_STEALTH_EXTRA_TIMEOUT_SECONDS = 40.0
DEFAULT_STEALTH_WAIT_SECONDS = 90.0
DEFAULT_STEALTH_CONNECT_TIMEOUT_SECONDS = 1.0
DEFAULT_STEALTH_CONNECT_TRIES = 40


@dataclass
class StealthConfig:
    headless: bool = False
    sandbox: bool = False
    wait_seconds: float = DEFAULT_STEALTH_WAIT_SECONDS
    extra_timeout_seconds: float = DEFAULT_STEALTH_EXTRA_TIMEOUT_SECONDS
    connect_timeout_seconds: float = DEFAULT_STEALTH_CONNECT_TIMEOUT_SECONDS
    connect_tries: int = DEFAULT_STEALTH_CONNECT_TRIES
    browser_path: str = ""
    fetch_timeout_seconds: float = DEFAULT_FETCH_TIMEOUT_SECONDS
    probe_timeout_seconds: float = DEFAULT_PROBE_TIMEOUT_SECONDS


_RUNTIME_STEALTH = StealthConfig()


def get_stealth_config() -> StealthConfig:
    return _RUNTIME_STEALTH


def apply_stealth_config(stealth: StealthConfig) -> None:
    global _RUNTIME_STEALTH
    _RUNTIME_STEALTH = StealthConfig(
        headless=stealth.headless,
        sandbox=stealth.sandbox,
        wait_seconds=stealth.wait_seconds,
        extra_timeout_seconds=stealth.extra_timeout_seconds,
        connect_timeout_seconds=stealth.connect_timeout_seconds,
        connect_tries=stealth.connect_tries,
        browser_path=stealth.browser_path,
        fetch_timeout_seconds=stealth.fetch_timeout_seconds,
        probe_timeout_seconds=stealth.probe_timeout_seconds,
    )
