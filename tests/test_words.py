import pytest

from words import format_word_row, get_random_words


def test_get_random_words_returns_requested_count():
    words = get_random_words("german", 5)

    assert len(words) == 5


def test_get_random_words_rejects_unknown_language():
    with pytest.raises(ValueError, match="Unsupported language"):
        get_random_words("french", 1)


def test_get_random_words_rejects_non_positive_count():
    with pytest.raises(ValueError, match="Count must be at least 1"):
        get_random_words("german", 0)


def test_format_word_row_includes_article_and_meaning():
    row = ("der", "Abend", "evening", None, "noun", None, None, None)

    formatted = format_word_row(row)

    assert formatted == "der Abend - evening"


def test_format_word_row_includes_pronunciation_when_present():
    row = ("die", "Zeit", "time", "[tsaɪt]", "noun", None, None, None)

    formatted = format_word_row(row)

    assert formatted == "die Zeit - time ([tsaɪt])"


def test_format_word_row_respects_include_flags():
    row = (
        "das",
        "Haus",
        "house",
        "[haʊs]",
        "noun",
        "Das Haus ist groß.",
        "The house is big.",
        "Häuser",
    )
    include = {
        "article": False,
        "word": True,
        "meaning": False,
        "pronunciation": True,
        "example": True,
        "translation": True,
        "plural": True,
    }

    formatted = format_word_row(row, include)

    assert formatted == "Haus ([haʊs]) [pl. Häuser]; e.g. Das Haus ist groß.; tr. The house is big."


def test_format_word_row_omits_unchecked_fields():
    row = ("der", "Abend", "evening", "[aːbənt]", "noun", None, None, None)
    include = {
        "article": True,
        "word": True,
        "meaning": False,
        "pronunciation": False,
        "example": False,
        "translation": False,
        "plural": False,
    }

    formatted = format_word_row(row, include)

    assert formatted == "der Abend"
