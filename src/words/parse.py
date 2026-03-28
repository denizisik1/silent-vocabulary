import csv
from pathlib import Path

from words.constants import ARTICLE_PREFIXES, HEADER_ALIASES, ROW_FIELD_COUNT


def empty_field(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped


def word_key(word: str) -> str:
    return word.casefold()


def split_article(word_field: str) -> tuple[str | None, str]:
    text = word_field.strip()
    for prefix in ARTICLE_PREFIXES:
        prefix_with_space = f"{prefix} "
        if text.startswith(prefix_with_space):
            return prefix, text.removeprefix(prefix_with_space)
    return None, text


def normalize_row(row: tuple) -> tuple:
    padded = row + (None,) * (ROW_FIELD_COUNT - len(row))
    return padded[:ROW_FIELD_COUNT]


def row_from_mapping(values: dict[str, str | None], default_classification: str) -> tuple | None:
    article = empty_field(values.get("article"))
    word = empty_field(values.get("word"))
    meaning = empty_field(values.get("meaning"))
    if word is None:
        return None

    if article is None and word:
        article, word = split_article(word)

    pronunciation = empty_field(values.get("pronunciation"))
    classification = empty_field(values.get("classification")) or default_classification
    source = empty_field(values.get("source"))
    example = empty_field(values.get("example"))
    translation = empty_field(values.get("translation"))
    plural = empty_field(values.get("plural"))
    return (
        article,
        word,
        meaning,
        pronunciation,
        classification,
        source,
        example,
        translation,
        plural,
    )


def legacy_row(word_field: str, meaning_field: str, default_classification: str) -> tuple | None:
    return row_from_mapping(
        {
            "word": word_field,
            "meaning": meaning_field,
        },
        default_classification,
    )


def is_header_row(row: list[str]) -> bool:
    if not row:
        return False
    first_cell = row[0].strip().lower()
    return first_cell in HEADER_ALIASES or first_cell == "word"


def normalize_header_row(row: list[str]) -> list[str]:
    return [cell.strip().lower() for cell in row]


def read_csv_rows(path: Path, default_classification: str) -> list[tuple]:
    rows: list[tuple] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header_names: list[str] | None = None

        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue

            if header_names is None and is_header_row(row):
                header_names = normalize_header_row(row)
                continue

            if header_names is not None:
                values = {
                    header_names[index]: empty_field(row[index])
                    for index in range(min(len(header_names), len(row)))
                }
                parsed = row_from_mapping(values, default_classification)
            elif len(row) >= 2:
                parsed = legacy_row(row[0], row[1], default_classification)
            else:
                continue

            if parsed is not None:
                rows.append(parsed)

    return rows


def read_removals(path: Path) -> set[str]:
    if not path.is_file():
        return set()

    removals: set[str] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue
            first = row[0].strip()
            if first.lower() == "word":
                continue
            removals.add(word_key(first))
    return removals
