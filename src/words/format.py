from words.constants import DEFAULT_INCLUDE
from words.parse import normalize_row


def format_word_row(row: tuple, include: dict[str, bool] | None = None) -> str:
    (
        article,
        word,
        meaning,
        pronunciation,
        _classification,
        _source,
        example,
        translation,
        plural,
    ) = normalize_row(row)
    flags = DEFAULT_INCLUDE if include is None else include

    head_parts: list[str] = []
    if flags.get("article") and article:
        head_parts.append(article)
    if flags.get("word") and word:
        head_parts.append(word)

    line = " ".join(head_parts)
    if flags.get("meaning") and meaning:
        line = f"{line} - {meaning}" if line else meaning
    if flags.get("pronunciation") and pronunciation:
        line = f"{line} ({pronunciation})" if line else pronunciation
    if flags.get("plural") and plural:
        line = f"{line} [pl. {plural}]" if line else f"[pl. {plural}]"
    if flags.get("example") and example:
        line = f"{line}; e.g. {example}" if line else example
    if flags.get("translation") and translation:
        line = f"{line}; tr. {translation}" if line else translation
    return line
