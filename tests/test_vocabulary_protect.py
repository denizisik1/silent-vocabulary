import os
import stat

from vocabulary_protect import (
    apply_base_vocabulary_protection,
    is_writable,
    protect_base_vocabulary,
    unprotect_base_vocabulary,
)


def _writable_csv(tmp_path):
    path = tmp_path / "nouns.csv"
    path.write_text("word,meaning\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    return path


def test_protect_makes_writable_files_readonly(tmp_path):
    path = _writable_csv(tmp_path)
    assert is_writable(path)

    changed = protect_base_vocabulary(tmp_path)

    assert changed == 1
    assert not is_writable(path)
    assert protect_base_vocabulary(tmp_path) == 0


def test_unprotect_restores_user_write(tmp_path):
    path = _writable_csv(tmp_path)
    protect_base_vocabulary(tmp_path)
    assert not is_writable(path)

    changed = unprotect_base_vocabulary(tmp_path)

    assert changed == 1
    assert is_writable(path)


def test_apply_base_vocabulary_protection_toggle(tmp_path):
    path = _writable_csv(tmp_path)

    assert apply_base_vocabulary_protection(True, tmp_path) == 1
    assert not os.access(path, os.W_OK)
    assert apply_base_vocabulary_protection(False, tmp_path) == 1
    assert os.access(path, os.W_OK)
