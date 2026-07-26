from words.ipa import format_notification_body, ipa_example_lines, ipa_letters_in
from words.ipa_chart import load_ipa_examples


def test_chart_example_uses_the_english_approximation():
    examples = load_ipa_examples()

    assert examples["aː"] == "f<b>a</b>ther"
    assert examples["ɛ"] == "b<b>e</b>t"
    assert examples["ç"] == "<b>h</b>ue"
    assert examples["ts"] == "ca<b>ts</b>"
    assert examples["ə"] == "bal<b>a</b>nce"
    assert examples["b"] == "<b>b</b>all"


def test_chart_keeps_the_primary_entry_when_a_symbol_repeats():
    examples = load_ipa_examples()

    assert examples["ɛ"] == "b<b>e</b>t"
    assert examples["r"] == "<b>r</b>ouge"
    assert examples["ɐ̯"] == "sof<b>a</b>"


def test_ipa_letters_in_skips_stress_and_duplicates():
    assert ipa_letters_in("[ˈaːbənt]") == ["aː", "b", "ə", "n", "t"]


def test_ipa_letters_in_keeps_affricates_and_diphthongs():
    assert ipa_letters_in("[tsaɪt]") == ["ts", "aɪ", "t"]
    assert ipa_letters_in("[haʊs]") == ["h", "aʊ", "s"]


def test_ipa_example_lines_pair_each_letter_with_its_chart_word():
    lines = ipa_example_lines("[ˈaːbənt]")

    assert lines == [
        "aː  f<b>a</b>ther",
        "b  <b>b</b>all",
        "ə  bal<b>a</b>nce",
        "n  <b>n</b>ot",
        "t  <b>t</b>all",
    ]


def test_notification_body_appends_example_lines():
    row = ("der", "Abend", "evening", "[ˈaːbənt]", "noun", None, None, None, None)

    body = format_notification_body(row)

    assert body.startswith("der Abend - evening ([ˈaːbənt])\n")
    assert "aː  f<b>a</b>ther" in body
    assert "ə  bal<b>a</b>nce" in body


def test_notification_body_stays_plain_when_ipa_is_hidden():
    row = ("der", "Abend", "evening", "[ˈaːbənt]", "noun", None, None, None, None)
    include = {
        "article": True,
        "word": True,
        "meaning": True,
        "pronunciation": False,
        "example": False,
        "translation": False,
        "plural": False,
    }

    assert format_notification_body(row, include) == "der Abend - evening"
