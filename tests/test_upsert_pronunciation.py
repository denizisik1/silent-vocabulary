from words import WordFields, add_word, get_random_words, upsert_pronunciation, user_vocabulary_dir


def _prepare_dirs(tmp_path, monkeypatch) -> None:
    vocabulary_root = tmp_path / "vocabulary"
    vocabulary_root.mkdir()
    (vocabulary_root / "nouns.csv").write_text("der Abend,evening\n", encoding="utf-8")
    for filename in ("verbs.csv", "adjectives.csv", "adverbs.csv"):
        (vocabulary_root / filename).write_text("word,meaning\n", encoding="utf-8")
    monkeypatch.setenv("VIPA_VOCABULARY_DIR", str(vocabulary_root))
    monkeypatch.setenv("VIPA_USER_VOCABULARY_DIR", str(tmp_path / "user-vocabulary"))


def test_upsert_pronunciation_writes_overlay(tmp_path, monkeypatch):
    _prepare_dirs(tmp_path, monkeypatch)

    row = upsert_pronunciation("german", "Abend", "[ˈa:bn̩t]", source="pons")

    assert row[1] == "Abend"
    assert row[3] == "[ˈa:bn̩t]"
    assert row[5] == "pons"
    additions = (user_vocabulary_dir() / "german" / "additions.csv").read_text(encoding="utf-8")
    assert "[ˈa:bn̩t]" in additions
    assert get_random_words("german", 1)[0][3] == "[ˈa:bn̩t]"


def test_upsert_pronunciation_updates_user_added_word(tmp_path, monkeypatch):
    _prepare_dirs(tmp_path, monkeypatch)
    add_word("german", WordFields(article="die", word="Zeit", meaning="time"))

    row = upsert_pronunciation("german", "Zeit", "[tsaɪt]")

    assert row[0:4] == ("die", "Zeit", "time", "[tsaɪt]")
