from words.load import load_language_words
from words.parse import empty_field, normalize_row, word_key


class AmbiguousWordError(ValueError):
    def __init__(self, word: str, candidates: list[tuple]) -> None:
        self.word = word
        self.candidates = candidates
        listed = "; ".join(describe_entry(row) for row in candidates)
        super().__init__(f"{word} matches more than one entry: {listed}")


def describe_entry(row: tuple) -> str:
    article, word, meaning, _pronunciation, classification = normalize_row(row)[:5]
    head = f"{article} {word}" if article else word
    label = f"{classification}: {head}" if classification else head
    return f"{label} - {meaning}" if meaning else label


def find_word_entries(language_key: str, word: str) -> list[tuple]:
    cleaned = empty_field(word)
    if cleaned is None:
        return []
    try:
        rows = load_language_words(language_key)
    except (FileNotFoundError, ValueError):
        return []
    needle = word_key(cleaned)
    return [row for row in rows if word_key(row[1]) == needle]


def _matches(row: tuple, classification: str | None, article: str | None) -> bool:
    if classification is not None and word_key(row[4] or "") != word_key(classification):
        return False
    if article is not None and word_key(row[0] or "") != word_key(article):
        return False
    return True


def resolve_entry(
    language_key: str,
    word: str,
    *,
    classification: str | None = None,
    article: str | None = None,
) -> tuple:
    cleaned = empty_field(word)
    if cleaned is None:
        raise ValueError("Word input is empty.")

    candidates = [
        row
        for row in find_word_entries(language_key, cleaned)
        if _matches(row, empty_field(classification), empty_field(article))
    ]
    if not candidates:
        raise ValueError(f"Word not found: {cleaned}")
    if len(candidates) > 1:
        raise AmbiguousWordError(cleaned, candidates)
    return candidates[0]
