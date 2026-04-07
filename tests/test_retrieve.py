from retrieve.parse import clean_ipa_text, extract_ipa_from_html
from retrieve.url import build_entry_url


def test_build_entry_url_appends_word():
    url = build_entry_url("https://en.pons.com/translate/german-english", "Abend")

    assert url == "https://en.pons.com/translate/german-english/Abend"


def test_build_entry_url_quotes_spaces():
    url = build_entry_url("https://example.com/dict/", "der Abend")

    assert url.endswith("/der%20Abend")


def test_clean_ipa_text_brackets():
    assert clean_ipa_text("[ˈa:bn̩t]") == "[ˈa:bn̩t]"
    assert clean_ipa_text("/ˈaːbənt/") == "[ˈaːbənt]"


def test_extract_ipa_from_html_by_class():
    page_html = """
    <html><body>
      <span class="phonetics">[ˈa:bn̩t]</span>
      <span class="other">noise</span>
    </body></html>
    """

    assert extract_ipa_from_html(page_html, "phonetics") == "[ˈa:bn̩t]"


def test_extract_ipa_from_html_missing_raises():
    page_html = "<html><body><span class='x'>hello</span></body></html>"

    try:
        extract_ipa_from_html(page_html, "phonetics")
        assert False, "expected ValueError"
    except ValueError as error:
        assert "No IPA found" in str(error)
