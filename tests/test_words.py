import pytest

from database import format_word_row, get_random_words


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
    row = ("der", "Abend", "evening", None, "noun")

    formatted = format_word_row(row)

    assert formatted == "der Abend - evening"


def test_format_word_row_includes_pronunciation_when_present():
    row = ("die", "Zeit", "time", "[tsaɪt]", "noun")

    formatted = format_word_row(row)

    assert formatted == "die Zeit - time ([tsaɪt])"
