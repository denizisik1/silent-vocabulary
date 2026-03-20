from words import CSV_COLUMNS, get_random_words, vocabulary_dir


def test_vocabulary_directory_exists():
    assert vocabulary_dir().is_dir()


def test_german_vocabulary_files_exist():
    expected_files = ("nouns.csv", "verbs.csv", "adjectives.csv", "adverbs.csv")
    root = vocabulary_dir()

    for filename in expected_files:
        assert (root / filename).is_file(), f"Missing vocabulary file: {filename}"


def test_german_vocabulary_has_rows():
    words = get_random_words("german", 1)

    assert len(words) == 1
    article, word, meaning, pronunciation, classification = words[0]
    assert word
    assert classification in {"noun", "verb", "adjective", "adverb"}


def test_header_csv_format(tmp_path, monkeypatch):
    vocabulary_root = tmp_path / "vocabulary"
    vocabulary_root.mkdir()
    csv_path = vocabulary_root / "nouns.csv"
    csv_path.write_text(
        ",".join(CSV_COLUMNS) + "\n" "der,Abend,evening,[aːbənt],noun,,,,\n",
        encoding="utf-8",
    )
    for filename in ("verbs.csv", "adjectives.csv", "adverbs.csv"):
        (vocabulary_root / filename).write_text("word,meaning\n", encoding="utf-8")

    monkeypatch.setenv("VIPA_VOCABULARY_DIR", str(vocabulary_root))

    words = get_random_words("german", 1)
    assert words[0][0:4] == ("der", "Abend", "evening", "[aːbənt]")
