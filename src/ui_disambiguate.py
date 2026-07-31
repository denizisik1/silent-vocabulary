from PySide6.QtWidgets import QInputDialog, QWidget

from words import describe_entry

_PROMPT = "'{word}' matches more than one entry.\nChoose the one you mean:"


def choose_entry(parent: QWidget | None, word: str, candidates: list[tuple]) -> tuple | None:
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        return None

    labels = [describe_entry(row) for row in candidates]
    chosen, accepted = QInputDialog.getItem(
        parent,
        "Which word?",
        _PROMPT.format(word=word),
        labels,
        0,
        False,
    )
    if not accepted:
        return None
    return candidates[labels.index(chosen)]
