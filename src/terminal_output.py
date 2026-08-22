import os
import sys
from pathlib import Path
from typing import Any

from retrieve.progress import (
    KIND_BAD,
    KIND_DETAIL,
    KIND_GOOD,
    KIND_HEADER,
    KIND_NOTE,
    decorate,
)
from words.paths import pronunciation_files_line_count

_RESET = "\033[0m"

_COLOR_BY_KIND = {
    KIND_HEADER: "\033[1;36m",
    KIND_GOOD: "\033[32m",
    KIND_BAD: "\033[31m",
    KIND_NOTE: "\033[33m",
    KIND_DETAIL: "\033[90m",
}


def colors_enabled(stream: Any = None) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM", "").strip().lower() == "dumb":
        return False
    if stream is None:
        stream = sys.stdout
    if not hasattr(stream, "isatty"):
        return False
    return bool(stream.isatty())


def paint(text: str, kind: str) -> str:
    color = _COLOR_BY_KIND.get(kind)
    if color is None:
        return text
    return f"{color}{text}{_RESET}"


def _print_line(text: str, kind: str) -> None:
    if colors_enabled():
        text = paint(text, kind)
    print(text, flush=True)


def print_progress(message: str, kind: str = KIND_DETAIL) -> None:
    _print_line(decorate(message, kind), kind)


def print_notice(message: str, kind: str = KIND_HEADER) -> None:
    _print_line(message, kind)


IPA_FILES_HINT = (
    "If you have IPA files from before you can place them under "
    'vocabulary/pronunciation and avoid having to "retrieve" them en masse.'
)
IPA_FILES_HINT_LINE_THRESHOLD = 2000


def print_ipa_files_hint(project_root: Path) -> None:
    if pronunciation_files_line_count(project_root) > IPA_FILES_HINT_LINE_THRESHOLD:
        return
    print_notice(IPA_FILES_HINT, KIND_NOTE)
