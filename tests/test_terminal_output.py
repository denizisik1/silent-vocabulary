from retrieve.progress import KIND_BAD, KIND_DETAIL, KIND_GOOD, KIND_HEADER, decorate
from terminal_output import colors_enabled, paint, print_progress


class FakeStream:
    def __init__(self, a_terminal):
        self._a_terminal = a_terminal

    def isatty(self):
        return self._a_terminal


def test_a_terminal_gets_colors(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)

    assert colors_enabled(FakeStream(True)) is True


def test_a_pipe_gets_no_colors(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)

    assert colors_enabled(FakeStream(False)) is False


def test_no_color_is_honoured(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")

    assert colors_enabled(FakeStream(True)) is False


def test_a_dumb_terminal_gets_no_colors(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "dumb")

    assert colors_enabled(FakeStream(True)) is False


def test_each_kind_is_wrapped_in_its_own_color():
    good = paint("saved", KIND_GOOD)
    bad = paint("failed", KIND_BAD)

    assert good.startswith("\033[") and good.endswith("\033[0m")
    assert "saved" in good
    assert good[:5] != bad[:5]


def test_an_unknown_kind_is_left_alone():
    assert paint("plain", "whatever") == "plain"


def test_the_markers_keep_the_words_apart_from_their_details():
    assert decorate("[1/2] Abend", KIND_HEADER) == "[1/2] Abend"
    assert decorate("saved Abend", KIND_GOOD) == "  + saved Abend"
    assert decorate("failed", KIND_BAD) == "  - failed"
    assert decorate("plain request answered", KIND_DETAIL) == "    plain request answered"


def test_a_progress_line_is_printed_with_its_marker(capsys, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")

    print_progress("saved Abend", KIND_GOOD)

    assert capsys.readouterr().out == "  + saved Abend\n"
