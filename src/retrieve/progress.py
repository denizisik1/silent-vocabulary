from collections.abc import Callable, Iterator
from contextlib import contextmanager

KIND_HEADER = "header"
KIND_GOOD = "good"
KIND_BAD = "bad"
KIND_NOTE = "note"
KIND_DETAIL = "detail"

_MARKERS = {
    KIND_HEADER: "",
    KIND_GOOD: "  + ",
    KIND_BAD: "  - ",
    KIND_NOTE: "  ~ ",
    KIND_DETAIL: "    ",
}

ReportCallback = Callable[[str, str], None]

_reporter: ReportCallback | None = None  # pylint: disable=invalid-name  # current run hook


def set_retrieve_reporter(report: ReportCallback | None) -> None:
    global _reporter  # pylint: disable=global-statement  # current run hook
    _reporter = report


@contextmanager
def retrieve_reporter(report: ReportCallback | None) -> Iterator[None]:
    previous = _reporter
    set_retrieve_reporter(report)
    try:
        yield
    finally:
        set_retrieve_reporter(previous)


def report_progress(message: str, kind: str = KIND_DETAIL) -> None:
    if _reporter is None:
        return
    _reporter(message, kind)


def decorate(message: str, kind: str) -> str:
    return f"{_MARKERS.get(kind, _MARKERS[KIND_DETAIL])}{message}"
