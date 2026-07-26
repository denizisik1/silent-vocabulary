import html
import re

_TRANSCRIPTION_SUFFIX = re.compile(r"\s*(?:\[[^\]]*\]|/[^/]+/)\s*$")


def _is_citation(element) -> bool:
    if element.tag != "a":
        return False
    href = element.get("href") or ""
    name = element.get("name") or ""
    style = (element.get("style") or "").replace(" ", "")
    return "cite" in href or "cite_ref" in name or "vertical-align:super" in style


def _is_bold(style: str) -> bool:
    compact = style.replace(" ", "")
    return "font-weight:700" in compact or "font-weight:bold" in compact


def _collect_runs(element, runs: list[tuple[str, bool]]) -> bool:
    if _is_citation(element):
        return False
    if element.tag == "br":
        return True

    bold = _is_bold(element.get("style") or "")
    if element.text:
        runs.append((element.text, bold))
    for child in element:
        if _collect_runs(child, runs):
            return True
        if child.tail:
            runs.append((child.tail, bold))
    return False


def _slice_runs(runs: list[tuple[str, bool]], start: int, end: int) -> list[tuple[str, bool]]:
    sliced: list[tuple[str, bool]] = []
    cursor = 0
    for part, bold in runs:
        part_end = cursor + len(part)
        keep_start = max(cursor, start)
        keep_end = min(part_end, end)
        if keep_start < keep_end:
            begin = keep_start - cursor
            finish = keep_end - cursor
            sliced.append((part[begin:finish], bold))
        cursor = part_end
        if cursor >= end:
            break
    return sliced


def _trim_runs(runs: list[tuple[str, bool]]) -> list[tuple[str, bool]]:
    text = "".join(part for part, _bold in runs)
    start = len(text) - len(text.lstrip())
    end = len(text.rstrip())
    if start >= end:
        return []
    return _slice_runs(runs, start, end)


def _is_word_character(character: str) -> bool:
    return character.isalpha() or character in "-'"


def _first_bold_span(runs: list[tuple[str, bool]]) -> tuple[int, int] | None:
    cursor = 0
    start = None
    end = None
    for part, bold in runs:
        if bold:
            inner_start = len(part) - len(part.lstrip())
            inner_end = len(part.rstrip())
            if inner_start < inner_end:
                if start is None:
                    start = cursor + inner_start
                end = cursor + inner_end
        elif start is not None:
            break
        cursor += len(part)
    if start is None or end is None:
        return None
    return start, end


def _strip_transcription(runs: list[tuple[str, bool]]) -> list[tuple[str, bool]]:
    text = "".join(part for part, _bold in runs)
    match = _TRANSCRIPTION_SUFFIX.search(text)
    if match is None:
        return runs
    return _trim_runs(_slice_runs(runs, 0, match.start()))


def _english_example_runs(runs: list[tuple[str, bool]]) -> list[tuple[str, bool]]:
    cleaned = _strip_transcription(_trim_runs(runs))
    span = _first_bold_span(cleaned)
    if span is None:
        return []
    start, end = span
    text = "".join(part for part, _bold in cleaned)
    while start > 0 and _is_word_character(text[start - 1]):
        start -= 1
    while end < len(text) and _is_word_character(text[end]):
        end += 1
    return _trim_runs(_slice_runs(cleaned, start, end))


def example_html_from_cell(cell) -> str:
    runs: list[tuple[str, bool]] = []
    _collect_runs(cell, runs)
    parts: list[str] = []
    for text, bold in _english_example_runs(runs):
        escaped = html.escape(text, quote=False)
        parts.append(f"<b>{escaped}</b>" if bold else escaped)
    return "".join(parts)
