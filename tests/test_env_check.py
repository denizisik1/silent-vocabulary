from universal.env_check import check_env_files


def test_check_env_files_matching_keys_and_values(tmp_path, monkeypatch, capsys):
    example = tmp_path / ".env.example"
    env_file = tmp_path / ".env"
    example.write_text("FOO=1\nBAR=2\n", encoding="utf-8")
    env_file.write_text("FOO=1\nBAR=2\n", encoding="utf-8")
    monkeypatch.setattr("universal.env_check._send_notification", lambda *_: None)

    assert check_env_files(tmp_path) is True
    assert capsys.readouterr().err == ""


def test_check_env_files_warns_on_key_drift(tmp_path, monkeypatch, capsys):
    example = tmp_path / ".env.example"
    env_file = tmp_path / ".env"
    example.write_text("FOO=1\nBAR=2\n", encoding="utf-8")
    env_file.write_text("FOO=1\nBAZ=3\n", encoding="utf-8")
    monkeypatch.setattr("universal.env_check._send_notification", lambda *_: None)

    assert check_env_files(tmp_path) is False
    err = capsys.readouterr().err
    assert "Missing in .env: BAR" in err
    assert "Only in .env: BAZ" in err
    assert "\033[31m" in err


def test_check_env_files_warns_on_value_drift(tmp_path, monkeypatch, capsys):
    example = tmp_path / ".env.example"
    env_file = tmp_path / ".env"
    example.write_text("FOO=1\nBAR=2\n", encoding="utf-8")
    env_file.write_text("FOO=1\nBAR=changed\n", encoding="utf-8")
    monkeypatch.setattr("universal.env_check._send_notification", lambda *_: None)

    assert check_env_files(tmp_path) is False
    err = capsys.readouterr().err
    assert "Different values: BAR" in err
    assert "\033[31m" in err


def test_check_env_files_warns_when_env_missing(tmp_path, monkeypatch, capsys):
    (tmp_path / ".env.example").write_text("FOO=1\n", encoding="utf-8")
    monkeypatch.setattr("universal.env_check._send_notification", lambda *_: None)

    assert check_env_files(tmp_path) is False
    assert ".env is missing" in capsys.readouterr().err
