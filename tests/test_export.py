import zipfile
from datetime import datetime, timezone

import pytest

from words.export import (
    collect_overlay_files,
    default_export_filename,
    export_user_vocabulary,
)


def test_default_export_filename_uses_utc_stamp():
    when = datetime(2026, 7, 22, 9, 58, 0, tzinfo=timezone.utc)

    assert default_export_filename(when=when) == "vipa-vocabulary-20260722-095800.zip"


def test_collect_overlay_files_ignores_empty_and_missing(tmp_path):
    german = tmp_path / "german"
    german.mkdir()
    (german / "additions.csv").write_text("word,meaning\nAbend,evening\n", encoding="utf-8")
    (german / "removals.csv").write_text("", encoding="utf-8")
    (tmp_path / "empty_lang").mkdir()

    files = collect_overlay_files(tmp_path)

    assert files == [german / "additions.csv"]


def test_export_user_vocabulary_writes_zip(tmp_path):
    german = tmp_path / "user" / "german"
    german.mkdir(parents=True)
    (german / "additions.csv").write_text(
        "article,word,meaning,pronunciation,classification,source,example,translation,plural\n"
        "der,Abend,evening,[aːbənt],noun,,,,\n",
        encoding="utf-8",
    )
    (german / "removals.csv").write_text("word\nZeit\n", encoding="utf-8")
    destination = tmp_path / "backup" / "overlay.zip"

    written = export_user_vocabulary(destination, user_root=tmp_path / "user")

    assert written == destination
    assert written.is_file()
    with zipfile.ZipFile(written) as archive:
        names = set(archive.namelist())
        assert names == {"german/additions.csv", "german/removals.csv"}
        assert "Abend" in archive.read("german/additions.csv").decode("utf-8")


def test_export_user_vocabulary_requires_overlay(tmp_path):
    destination = tmp_path / "empty.zip"

    with pytest.raises(FileNotFoundError, match="No user vocabulary overlay"):
        export_user_vocabulary(destination, user_root=tmp_path / "missing")
