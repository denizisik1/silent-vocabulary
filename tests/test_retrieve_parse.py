import pytest

from retrieve.parse import clean_ipa_text, extract_ipa_from_html


def test_clean_keeps_square_bracket_notation():
    assert clean_ipa_text("[ˈa:bn̩t]") == "[ˈa:bn̩t]"


def test_clean_converts_slashes_and_parentheses_to_brackets():
    assert clean_ipa_text("/ˈaːbənt/") == "[ˈaːbənt]"
    assert clean_ipa_text("(ˈaːbənt)") == "[ˈaːbənt]"


def test_clean_extracts_notation_from_surrounding_text():
    assert clean_ipa_text("Aussprache: [ˈaːbənt] anhören") == "[ˈaːbənt]"


def test_clean_collapses_inner_whitespace():
    assert clean_ipa_text("[  ˈaː   bənt  ]") == "[ˈaː bənt]"


def test_clean_accepts_bare_notation_with_ipa_characters():
    assert clean_ipa_text("ˈaːbənt") == "[ˈaːbənt]"


def test_clean_rejects_empty_and_plain_text():
    assert clean_ipa_text("") is None
    assert clean_ipa_text("   \n  ") is None
    assert clean_ipa_text("evening") is None


def test_clean_rejects_empty_delimiters():
    assert clean_ipa_text("[]") is None
    assert clean_ipa_text("[   ]") is None


def test_extract_by_bare_class_token():
    page_html = "<html><body><span class='phonetics'>[ˈa:bn̩t]</span></body></html>"

    assert extract_ipa_from_html(page_html, "phonetics") == "[ˈa:bn̩t]"


def test_extract_by_dotted_class_token():
    page_html = "<html><body><span class='pron'>/ˈaːbənt/</span></body></html>"

    assert extract_ipa_from_html(page_html, ".pron") == "[ˈaːbənt]"


def test_extract_by_id_token():
    page_html = "<html><body><div id='pronunciation'>[ˈaːbənt]</div></body></html>"

    assert extract_ipa_from_html(page_html, "#pronunciation") == "[ˈaːbənt]"


def test_extract_finds_token_among_several_classes():
    page_html = "<html><body><span class='entry pron large'>[ˈaːbənt]</span></body></html>"

    assert extract_ipa_from_html(page_html, "pron") == "[ˈaːbənt]"


def test_extract_skips_matching_nodes_without_pronunciation():
    page_html = """
    <html><body>
      <span class="pron">listen</span>
      <span class="pron"></span>
      <span class="pron">[ˈaːbənt]</span>
    </body></html>
    """

    assert extract_ipa_from_html(page_html, "pron") == "[ˈaːbənt]"


def test_extract_joins_text_of_nested_elements():
    page_html = "<div class='pron'><b>[</b><i>ˈaːbənt</i><b>]</b></div>"

    assert extract_ipa_from_html(page_html, "pron") == "[ˈaːbənt]"


def test_extract_tolerates_unclosed_tags():
    assert extract_ipa_from_html("<span class='pron'>[ˈaːbənt]", "pron") == "[ˈaːbənt]"


def test_extract_rejects_empty_selector():
    with pytest.raises(ValueError, match="Find-by selector is empty"):
        extract_ipa_from_html("<html></html>", "   ")


def test_extract_rejects_selector_without_usable_characters():
    with pytest.raises(ValueError, match="Invalid find-by token"):
        extract_ipa_from_html("<html></html>", "!!!")


def test_extract_reports_selector_when_nothing_matches():
    page_html = "<html><body><span class='other'>hello</span></body></html>"

    with pytest.raises(ValueError, match="No IPA found for selector: phonetics"):
        extract_ipa_from_html(page_html, "phonetics")
