import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"
for root in (PROJECT_ROOT, SOURCE_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

load_dotenv(PROJECT_ROOT / ".env")


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    if not isinstance(application, QApplication):
        raise RuntimeError(
            "A QCoreApplication already exists; create QApplication via the qapp "
            "fixture before any QCoreApplication."
        )
    return application


@pytest.fixture
def without_app_environment(monkeypatch):
    for name in list(os.environ):
        if name.startswith("SILENT_VOCABULARY_"):
            monkeypatch.delenv(name, raising=False)


class FakeResponse:
    def __init__(self, body="", *, status_code=200, encoding="utf-8", apparent_encoding=None):
        self.status_code = status_code
        self.content = body.encode(encoding) if isinstance(body, str) else body
        self.encoding = encoding
        self.apparent_encoding = apparent_encoding


class FakeCall:
    def __init__(self, url, headers, timeout):
        self.url = url
        self.headers = headers
        self.timeout = timeout


class FakeHttp:
    def __init__(self):
        self._outcomes = {}
        self.calls = []

    def respond(self, url, body="", **response_options):
        self._outcomes[url] = FakeResponse(body, **response_options)

    def fail(self, url, error):
        self._outcomes[url] = error

    def requested_urls(self):
        return [call.url for call in self.calls]

    def handle(self, url, headers, timeout):
        self.calls.append(FakeCall(url, dict(headers or {}), timeout))
        if url not in self._outcomes:
            raise AssertionError(f"Unexpected HTTP request: {url}")
        outcome = self._outcomes[url]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture
def fake_http(monkeypatch):
    http = FakeHttp()

    class FakeSession:
        def __init__(self):
            self.headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *_exception):
            return False

        def get(self, url, timeout=None, **_options):
            return http.handle(url, self.headers, timeout)

    def fake_get(url, headers=None, timeout=None, **_options):
        return http.handle(url, headers, timeout)

    monkeypatch.setattr("retrieve.fetch.requests.Session", FakeSession)
    monkeypatch.setattr("retrieve.fetch.requests.get", fake_get)
    return http
