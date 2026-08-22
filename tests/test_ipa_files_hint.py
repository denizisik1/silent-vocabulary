from retrieve.progress import KIND_NOTE
from terminal_output import IPA_FILES_HINT, paint, print_ipa_files_hint
from words.paths import pronunciation_files_line_count


def _pronunciation_dir(project_root):
    directory = project_root / "vocabulary" / "pronunciation"
    directory.mkdir(parents=True)
    return directory


def test_missing_pronunciation_files_are_counted_as_zero(tmp_path):
    assert pronunciation_files_line_count(tmp_path) == 0


def test_lines_from_every_file_under_pronunciation_are_added_up(tmp_path):
    directory = _pronunciation_dir(tmp_path)
    (directory / "german.csv").write_text("a\nb\nc\n", encoding="utf-8")
    (directory / "extra.csv").write_text("d\ne\n", encoding="utf-8")

    assert pronunciation_files_line_count(tmp_path) == 5


def test_nested_pronunciation_files_are_counted(tmp_path):
    nested = _pronunciation_dir(tmp_path) / "old"
    nested.mkdir()
    (nested / "german.csv").write_text("a\nb\n", encoding="utf-8")

    assert pronunciation_files_line_count(tmp_path) == 2


def test_the_ipa_files_hint_is_printed_when_there_are_no_pronunciations(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.setenv("NO_COLOR", "1")

    print_ipa_files_hint(tmp_path)

    assert capsys.readouterr().out == IPA_FILES_HINT + "\n"


def test_the_ipa_files_hint_is_printed_when_there_are_not_many_lines(tmp_path, capsys, monkeypatch):
    (_pronunciation_dir(tmp_path) / "german.csv").write_text("x\n" * 2000, encoding="utf-8")
    monkeypatch.setenv("NO_COLOR", "1")

    print_ipa_files_hint(tmp_path)

    assert capsys.readouterr().out == IPA_FILES_HINT + "\n"


def test_the_ipa_files_hint_is_skipped_when_there_are_many_lines(tmp_path, capsys, monkeypatch):
    (_pronunciation_dir(tmp_path) / "german.csv").write_text("x\n" * 2001, encoding="utf-8")
    monkeypatch.setenv("NO_COLOR", "1")

    print_ipa_files_hint(tmp_path)

    assert capsys.readouterr().out == ""


def test_the_ipa_files_hint_is_yellow(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr("terminal_output.colors_enabled", lambda stream=None: True)

    print_ipa_files_hint(tmp_path)

    assert capsys.readouterr().out == paint(IPA_FILES_HINT, KIND_NOTE) + "\n"
    assert paint(IPA_FILES_HINT, KIND_NOTE).startswith("\033[33m")
