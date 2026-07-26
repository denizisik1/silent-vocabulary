from functools import cache
from pathlib import Path

from lxml import html as html_parser  # type: ignore[import-untyped]

from words.ipa_runs import example_html_from_cell

CHART_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "reference"
_CHART_FILES = ("consonants.html", "vowels.html")


def _large_symbols(cell) -> list[str]:
    symbols: list[str] = []
    for span in cell.xpath(".//span"):
        style = (span.get("style") or "").replace(" ", "")
        if "font-size:large" not in style:
            continue
        text = "".join(span.itertext()).strip()
        if text:
            symbols.append(text)
    return symbols


def _parse_chart_file(path: Path) -> dict[str, str]:
    document = html_parser.fromstring(path.read_text(encoding="utf-8"))
    examples: dict[str, str] = {}
    pending_html = ""
    for row in document.xpath(".//tr"):
        cells = row.xpath("./td")
        symbols: list[str] = []
        extra_cells = []
        for cell in cells:
            cell_symbols = _large_symbols(cell)
            if cell_symbols:
                symbols.extend(cell_symbols)
            else:
                extra_cells.append(cell)
        if not symbols:
            continue
        if extra_cells:
            pending_html = example_html_from_cell(extra_cells[-1])
        if not pending_html:
            continue
        for symbol in symbols:
            if symbol not in examples:
                examples[symbol] = pending_html
    return examples


@cache
def load_ipa_examples() -> dict[str, str]:
    examples: dict[str, str] = {}
    for filename in _CHART_FILES:
        for symbol, example_html in _parse_chart_file(CHART_DIR / filename).items():
            if symbol not in examples:
                examples[symbol] = example_html
    return examples
