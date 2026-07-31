import pytest

import ui_disambiguate
import ui_words
from ui_disambiguate import choose_entry
from ui_words import remove_chosen_entry
from words import WordFields, add_word, get_random_words

LAKE = ("der", "See", "lake", None, "noun", None, None, None, None)
SEA = ("die", "See", "sea", None, "noun", None, None, None, None)


class FakeInputDialog:
    def __init__(self, answer, *, accepted=True):
        self.answer = answer
        self.accepted = accepted
        self.prompts = []
        self.offered = []

    def getItem(  # pylint: disable=invalid-name
        self, _parent, _title, prompt, labels, _current, _editable
    ):
        self.prompts.append(prompt)
        self.offered.append(list(labels))
        if not self.accepted:
            return "", False
        return labels[self.answer], True


def use_dialog(monkeypatch, dialog):
    monkeypatch.setattr(ui_disambiguate, "QInputDialog", dialog)
    return dialog


def test_a_single_candidate_is_chosen_without_asking(monkeypatch):
    dialog = use_dialog(monkeypatch, FakeInputDialog(0))

    assert choose_entry(None, "See", [LAKE]) == LAKE
    assert not dialog.prompts


def test_no_candidate_leaves_nothing_to_choose(monkeypatch):
    dialog = use_dialog(monkeypatch, FakeInputDialog(0))

    assert choose_entry(None, "See", []) is None
    assert not dialog.prompts


def test_the_candidates_are_offered_by_their_description(monkeypatch):
    dialog = use_dialog(monkeypatch, FakeInputDialog(1))

    chosen = choose_entry(None, "See", [LAKE, SEA])

    assert chosen == SEA
    assert dialog.offered == [["noun: der See - lake", "noun: die See - sea"]]
    assert "See" in dialog.prompts[0]


def test_cancelling_the_dialog_chooses_nothing(monkeypatch):
    use_dialog(monkeypatch, FakeInputDialog(0, accepted=False))

    assert choose_entry(None, "See", [LAKE, SEA]) is None


@pytest.fixture(name="two_seas")
def two_seas_fixture(tmp_path, monkeypatch):
    vocabulary_root = tmp_path / "vocabulary"
    vocabulary_root.mkdir()
    (vocabulary_root / "nouns.csv").write_text("der See,lake\ndie See,sea\n", encoding="utf-8")
    for filename in ("verbs.csv", "adjectives.csv", "adverbs.csv"):
        (vocabulary_root / filename).write_text("", encoding="utf-8")
    monkeypatch.setenv("SILENT_VOCABULARY_DIR", str(vocabulary_root))
    monkeypatch.setenv("SILENT_VOCABULARY_USER_DIR", str(tmp_path / "user-vocabulary"))


def use_choice(monkeypatch, chosen):
    asked = []

    def fake_choose(_window, word, candidates):
        asked.append((word, candidates))
        return chosen

    monkeypatch.setattr(ui_words, "choose_entry", fake_choose)
    return asked


@pytest.mark.usefixtures("two_seas")
def test_removing_an_ambiguous_word_asks_before_removing(monkeypatch):
    asked = use_choice(monkeypatch, SEA)

    removed = remove_chosen_entry(None, "german", "See")

    assert removed[2] == "sea"
    assert asked[0][0] == "See"
    assert sorted(row[2] for row in asked[0][1]) == ["lake", "sea"]
    assert [row[2] for row in get_random_words("german", 1)] == ["lake"]


@pytest.mark.usefixtures("two_seas")
def test_declining_the_question_removes_nothing(monkeypatch):
    use_choice(monkeypatch, None)

    assert remove_chosen_entry(None, "german", "See") is None
    assert len(get_random_words("german", 2)) == 2


@pytest.mark.usefixtures("two_seas")
def test_an_unambiguous_word_is_removed_without_asking(monkeypatch):
    asked = use_choice(monkeypatch, None)
    add_word("german", WordFields(word="schnell", meaning="quickly"))

    removed = remove_chosen_entry(None, "german", "schnell")

    assert removed[1] == "schnell"
    assert not asked
