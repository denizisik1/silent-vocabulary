import sqlite3
import os


def test_database_file_exists():
    assert os.path.exists("pronunciations.db"), "Database file does not exist."  # nosec


def test_basic_query_operations():
    connection = sqlite3.connect("pronunciations.db")
    cursor = connection.cursor()

    cursor.execute("SELECT 1;")
    assert cursor.fetchone()[0] == 1  # nosec

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    first_table = cursor.fetchone()
    assert first_table, "No tables found in database."  # nosec

    table_name = first_table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")  # nosec
    row_count = cursor.fetchone()[0]
    assert row_count >= 0, f"Invalid count from {table_name}"  # nosec

    connection.close()


def test_tables_exist():
    connection = sqlite3.connect("pronunciations.db")
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    connection.close()

    expected = {"german"}
    missing = expected - tables
    assert not missing, f"Missing tables: {missing}"  # nosec
