import html
from functools import cache

from words.constants import DEFAULT_INCLUDE
from words.format import format_word_row
from words.ipa_chart import load_ipa_examples
from words.parse import normalize_row

_SKIP_MARKS = frozenset("ˈˌ.")


def _symbol_variants(symbol: str) -> tuple[str, ...]:
    variants = [symbol]
    if "ː" in symbol:
        variants.append(symbol.replace("ː", ":"))
    if symbol == "ɡ":
        variants.append("g")
    return tuple(variants)


@cache
def _matchers() -> tuple[tuple[str, str], ...]:
    matchers: list[tuple[str, str]] = []
    seen = set()
    for symbol in load_ipa_examples():
        for variant in _symbol_variants(symbol):
            if variant in seen:
                continue
            seen.add(variant)
            matchers.append((variant, symbol))
    return tuple(sorted(matchers, key=lambda item: len(item[0]), reverse=True))


def ipa_letters_in(pronunciation: str) -> list[str]:
    matchers = _matchers()
    letters: list[str] = []
    seen = set()
    index = 0
    while index < len(pronunciation):
        matched_symbol = None
        for variant, symbol in matchers:
            if pronunciation.startswith(variant, index):
                matched_symbol = symbol
                index += len(variant)
                break
        if matched_symbol is None:
            index += 1
            continue
        if matched_symbol in _SKIP_MARKS or matched_symbol in seen:
            continue
        seen.add(matched_symbol)
        letters.append(matched_symbol)
    return letters


def ipa_example_lines(pronunciation: str) -> list[str]:
    examples = load_ipa_examples()
    lines: list[str] = []
    for symbol in ipa_letters_in(pronunciation):
        example = examples.get(symbol)
        if not example:
            continue
        lines.append(f"{html.escape(symbol, quote=False)}  {example}")
    return lines


def format_notification_body(
    row: tuple,
    include: dict[str, bool] | None = None,
) -> str:
    flags = DEFAULT_INCLUDE if include is None else include
    line = format_word_row(row, include)
    pronunciation = normalize_row(row)[3]
    if not flags.get("pronunciation") or not pronunciation:
        return line

    example_lines = ipa_example_lines(pronunciation)
    if not example_lines:
        return line
    return html.escape(line, quote=False) + "\n" + "\n".join(example_lines)
