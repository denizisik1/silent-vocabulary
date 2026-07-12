import os

from retrieve.service import SourceEndpoint

DEFAULT_PRIMARY_SOURCE_URL = "https://en.pons.com/translate/german-english/"
DEFAULT_PRIMARY_FIND_BY = "phonetics"
DEFAULT_BACKUP_SOURCE_URL = "https://www.collinsdictionary.com/dictionary/german-english/"
DEFAULT_BACKUP_FIND_BY = "pron"
DEFAULT_SAMPLE_WORD = "Abend"


def _configured_text(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or default


def primary_source_url() -> str:
    return _configured_text("SILENT_VOCABULARY_PRIMARY_SOURCE_URL", DEFAULT_PRIMARY_SOURCE_URL)


def primary_find_by() -> str:
    return _configured_text("SILENT_VOCABULARY_PRIMARY_FIND_BY", DEFAULT_PRIMARY_FIND_BY)


def backup_source_url() -> str:
    return _configured_text("SILENT_VOCABULARY_BACKUP_SOURCE_URL", DEFAULT_BACKUP_SOURCE_URL)


def backup_find_by() -> str:
    return _configured_text("SILENT_VOCABULARY_BACKUP_FIND_BY", DEFAULT_BACKUP_FIND_BY)


def sample_word() -> str:
    return _configured_text("SILENT_VOCABULARY_SAMPLE_WORD", DEFAULT_SAMPLE_WORD)


def primary_endpoint() -> SourceEndpoint:
    return SourceEndpoint(
        label="primary",
        base_url=primary_source_url(),
        find_by=primary_find_by(),
    )


def backup_endpoint() -> SourceEndpoint:
    return SourceEndpoint(
        label="backup",
        base_url=backup_source_url(),
        find_by=backup_find_by(),
    )
