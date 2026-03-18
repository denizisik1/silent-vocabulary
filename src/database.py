import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "pronunciations.db"

LANGUAGE_TABLES = {
    "german": "german",
}

_WORD_COLUMNS = "article, word, meaning, pronunciation, classification"


def get_random_words(language_key: str, count: int) -> list[tuple]:
    table_name = LANGUAGE_TABLES.get(language_key)
    if table_name is None:
        raise ValueError(f"Unsupported language: {language_key}")
    if count < 1:
        raise ValueError("Count must be at least 1.")

    query = f"""
        SELECT {_WORD_COLUMNS}
        FROM {table_name}
        ORDER BY RANDOM()
        LIMIT ?
    """

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.cursor()
        cursor.execute(query, (count,))
        return cursor.fetchall()
    finally:
        connection.close()


def format_word_row(row: tuple) -> str:
    article, word, meaning, pronunciation, _classification = row
    if article:
        line = f"{article} {word}"
    else:
        line = word
    if meaning:
        line = f"{line} - {meaning}"
    if pronunciation:
        line = f"{line} ({pronunciation})"
    return line
