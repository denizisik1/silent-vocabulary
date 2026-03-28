from pathlib import Path

from platformdirs import user_data_dir

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VOCABULARY_DIR = PROJECT_ROOT / "vocabulary"
USER_DATA_DIR = Path(user_data_dir("vipa", appauthor=False))
USER_VOCABULARY_DIR = USER_DATA_DIR / "vocabulary"

CSV_COLUMNS = (
    "article",
    "word",
    "meaning",
    "pronunciation",
    "classification",
    "source",
    "example",
    "translation",
    "plural",
)

DISPLAY_COLUMNS = (
    "article",
    "word",
    "meaning",
    "pronunciation",
    "example",
    "translation",
    "plural",
)

DEFAULT_INCLUDE = {
    "article": True,
    "word": True,
    "meaning": True,
    "pronunciation": True,
    "example": False,
    "translation": False,
    "plural": False,
}

CLASSIFICATIONS = (
    "noun",
    "verb",
    "adjective",
    "adverb",
)

LANGUAGE_VOCABULARY_FILES = {
    "german": {
        "nouns.csv": "noun",
        "verbs.csv": "verb",
        "adjectives.csv": "adjective",
        "adverbs.csv": "adverb",
    },
}

ARTICLE_PREFIXES = (
    "der/die",
    "der",
    "die",
    "das",
    "dem",
    "den",
    "des",
    "ein",
    "eine",
)

HEADER_ALIASES = {
    "article": "article",
    "word": "word",
    "meaning": "meaning",
    "pronunciation": "pronunciation",
    "classification": "classification",
    "source": "source",
    "example": "example",
    "translation": "translation",
    "plural": "plural",
}

ROW_FIELD_COUNT = 9
