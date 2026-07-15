import pytest

from retrieve.headword import headword_of_heading, heading_names_word, plain_text
from retrieve.parse import extract_ipa_from_html

PONS_PAGE = """
<html><body>
  <div><h3>abendOLD [ˈabnt] ADV</h3><span class="phonetics">[ˈabnt]</span></div>
  <div><h3>Abend &lt;-s, -e&gt; [ˈaːbənt] N m</h3>
    <span class="phonetics">[ˈaːbənt]</span></div>
  <div><h3>Diens&#183;tag&#183;abend [diːnstaːk] N m</h3>
    <span class="phonetics">[diːnstaːk]</span></div>
</body></html>
"""

SUGGESTION_PAGE = """
<html><body>
  <div><h3>Zelt &lt;-[e]s, -e&gt; [tsɛlt] N nt</h3><span class="phonetics">[tsɛlt]</span></div>
</body></html>
"""

COLLINS_PAGE = """
<html><body>
  <div class="hom"><span class="orth">Daten</span><span class="pron">[ˈdaːtn]</span></div>
  <div class="hom"><span class="orth">data</span><span class="pron">[ˈdeɪtə]</span></div>
</body></html>
"""

NUMBERED_PAGE = """
<html><body>
  <div><h3>I. lau&#183;fen &lt;läuft&gt; [ˈlaufn̩] VB</h3>
    <span class="phonetics">[ˈlaufn̩]</span></div>
</body></html>
"""


def test_syllable_marks_and_spacing_are_ignored():
    assert plain_text("Diens\u00b7tag\u00adabend") == "Dienstagabend"
    assert plain_text("  Abend   <-s,  -e>  ") == "Abend <-s, -e>"


def test_section_numbers_in_front_of_a_headword_are_ignored():
    assert headword_of_heading("I. lau\u00b7fen <läuft>") == "laufen <läuft>"
    assert headword_of_heading("2) Zeit") == "Zeit"


def test_a_heading_names_a_word_only_at_a_word_boundary():
    assert heading_names_word("Abend <-s, -e> [a] N m", "Abend", ignore_case=False)
    assert not heading_names_word("abendOLD [a] ADV", "Abend", ignore_case=True)
    assert not heading_names_word("Datum <-s, Daten>", "Daten", ignore_case=False)


def test_the_pronunciation_of_the_asked_word_wins_over_its_neighbours():
    assert extract_ipa_from_html(PONS_PAGE, "phonetics", "Abend") == "[ˈaːbənt]"


def test_another_words_pronunciation_is_never_taken():
    with pytest.raises(ValueError, match="No IPA found"):
        extract_ipa_from_html(SUGGESTION_PAGE, "phonetics", "abbrechen")


def test_the_german_entry_wins_over_the_english_translation():
    assert extract_ipa_from_html(COLLINS_PAGE, "pron", "Daten") == "[ˈdaːtn]"


def test_a_numbered_entry_still_counts_as_the_word():
    assert extract_ipa_from_html(NUMBERED_PAGE, "phonetics", "laufen") == "[ˈlaufn̩]"


def test_without_a_word_the_first_pronunciation_is_taken():
    assert extract_ipa_from_html(SUGGESTION_PAGE, "phonetics") == "[tsɛlt]"


def test_a_page_without_any_headword_markup_is_trusted():
    page_html = "<html><body><span class='pron'>[ˈaːbənt]</span></body></html>"

    assert extract_ipa_from_html(page_html, "pron", "Abend") == "[ˈaːbənt]"
