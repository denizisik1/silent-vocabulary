import pytest

from retrieve import build_entry_url


def test_appends_word_to_base_without_trailing_slash():
    url = build_entry_url("https://en.pons.com/translate/german-english", "Abend")

    assert url == "https://en.pons.com/translate/german-english/Abend"


def test_keeps_single_separator_when_base_ends_with_slash():
    url = build_entry_url("https://en.pons.com/translate/german-english/", "Abend")

    assert url == "https://en.pons.com/translate/german-english/Abend"


def test_trims_whitespace_around_base_and_word():
    url = build_entry_url("  https://example.com/dict/  ", "  Abend  ")

    assert url == "https://example.com/dict/Abend"


def test_percent_encodes_spaces():
    url = build_entry_url("https://example.com/dict/", "der Abend")

    assert url == "https://example.com/dict/der%20Abend"


def test_percent_encodes_non_ascii_letters():
    url = build_entry_url("https://example.com/dict/", "Grüße")

    assert url == "https://example.com/dict/Gr%C3%BC%C3%9Fe"


def test_rejects_empty_base_url():
    with pytest.raises(ValueError, match="Source URL is empty"):
        build_entry_url("   ", "Abend")


def test_rejects_empty_word():
    with pytest.raises(ValueError, match="Word input is empty"):
        build_entry_url("https://example.com/dict/", "   ")
