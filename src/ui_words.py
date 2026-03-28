from functools import partial

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
)
from words import (
    DEFAULT_INCLUDE,
    WordFields,
    add_word,
    format_word_row,
    get_random_words,
    remove_word,
)

_INCLUDE_CHECKBOXES = {
    "article": "checkBox",
    "word": "checkBox_2",
    "meaning": "checkBox_3",
    "pronunciation": "checkBox_4",
    "example": "checkBox_5",
    "translation": "checkBox_6",
    "plural": "checkBox_7",
}

_ADD_LINE_EDITS = (
    "lineEdit_add_article",
    "lineEdit_2",
    "lineEdit_add_meaning",
    "lineEdit_add_pronunciation",
    "lineEdit_add_source",
    "lineEdit_add_example",
    "lineEdit_add_translation",
    "lineEdit_add_plural",
)


def language_key_from_combo(language_text: str) -> str:
    return language_text.strip().lower()


def include_flags(window: QMainWindow) -> dict[str, bool]:
    flags = dict(DEFAULT_INCLUDE)
    for field_name, object_name in _INCLUDE_CHECKBOXES.items():
        checkbox = window.findChild(QCheckBox, object_name)
        if checkbox is None:
            raise RuntimeError(f"Missing include control: {object_name}")
        flags[field_name] = checkbox.isChecked()
    return flags


def apply_default_include(window: QMainWindow) -> None:
    for field_name, object_name in _INCLUDE_CHECKBOXES.items():
        checkbox = window.findChild(QCheckBox, object_name)
        if checkbox is None:
            raise RuntimeError(f"Missing include control: {object_name}")
        checkbox.setChecked(DEFAULT_INCLUDE[field_name])


def on_get_words(window: QMainWindow) -> None:
    count_input = window.findChild(QSpinBox, "spinBox")
    language_combo = window.findChild(QComboBox, "comboBox")
    results = window.findChild(QTextEdit, "textEdit_3")
    if count_input is None or language_combo is None or results is None:
        raise RuntimeError("Missing Get Word(s) controls")

    count = count_input.value()
    language_key = language_key_from_combo(language_combo.currentText())
    include = include_flags(window)
    try:
        words = get_random_words(language_key, count)
    except (ValueError, FileNotFoundError, OSError) as error:
        results.setPlainText(str(error))
        return

    lines = [format_word_row(row, include) for row in words]
    results.setPlainText("\n".join(lines))


def wire_get_words(window: QMainWindow) -> None:
    button = window.findChild(QPushButton, "pushButton")
    if button is None:
        raise RuntimeError("Missing Get Word(s) button: pushButton")
    handler = partial(on_get_words, window)
    button.clicked.connect(handler)


def _line_text(window: QMainWindow, object_name: str) -> str:
    editor = window.findChild(QLineEdit, object_name)
    if editor is None:
        raise RuntimeError(f"Missing Add Word control: {object_name}")
    return editor.text()


def read_word_fields(window: QMainWindow) -> WordFields:
    classification = window.findChild(QComboBox, "comboBox_add_classification")
    if classification is None:
        raise RuntimeError("Missing Add Word control: comboBox_add_classification")

    return WordFields(
        article=_line_text(window, "lineEdit_add_article"),
        word=_line_text(window, "lineEdit_2"),
        meaning=_line_text(window, "lineEdit_add_meaning"),
        pronunciation=_line_text(window, "lineEdit_add_pronunciation"),
        classification=classification.currentText(),
        source=_line_text(window, "lineEdit_add_source"),
        example=_line_text(window, "lineEdit_add_example"),
        translation=_line_text(window, "lineEdit_add_translation"),
        plural=_line_text(window, "lineEdit_add_plural"),
    )


def clear_add_word_fields(window: QMainWindow) -> None:
    for object_name in _ADD_LINE_EDITS:
        editor = window.findChild(QLineEdit, object_name)
        if editor is None:
            raise RuntimeError(f"Missing Add Word control: {object_name}")
        editor.clear()

    classification = window.findChild(QComboBox, "comboBox_add_classification")
    if classification is None:
        raise RuntimeError("Missing Add Word control: comboBox_add_classification")
    classification.setCurrentIndex(0)


def on_add_word(window: QMainWindow) -> None:
    language_combo = window.findChild(QComboBox, "comboBox")
    results = window.findChild(QTextEdit, "textEdit_3")
    if language_combo is None or results is None:
        raise RuntimeError("Missing Add Word controls")

    language_key = language_key_from_combo(language_combo.currentText())
    include = include_flags(window)
    try:
        row = add_word(language_key, read_word_fields(window))
    except (ValueError, FileNotFoundError, OSError) as error:
        results.setPlainText(str(error))
        return

    clear_add_word_fields(window)
    results.setPlainText(f"Added: {format_word_row(row, include)}")


def on_remove_word(window: QMainWindow) -> None:
    word_input = window.findChild(QLineEdit, "lineEdit_2")
    language_combo = window.findChild(QComboBox, "comboBox")
    results = window.findChild(QTextEdit, "textEdit_3")
    if word_input is None or language_combo is None or results is None:
        raise RuntimeError("Missing Remove Word controls")

    language_key = language_key_from_combo(language_combo.currentText())
    try:
        removed = remove_word(language_key, word_input.text())
    except (ValueError, FileNotFoundError, OSError) as error:
        results.setPlainText(str(error))
        return

    word_input.clear()
    results.setPlainText(f"Removed: {removed}")


def wire_add_remove_word(window: QMainWindow) -> None:
    add_button = window.findChild(QPushButton, "pushButton_3")
    remove_button = window.findChild(QPushButton, "pushButton_remove_word")
    word_input = window.findChild(QLineEdit, "lineEdit_2")
    if add_button is None or remove_button is None or word_input is None:
        raise RuntimeError("Missing Add / Remove Word controls")

    add_handler = partial(on_add_word, window)
    remove_handler = partial(on_remove_word, window)
    add_button.clicked.connect(add_handler)
    remove_button.clicked.connect(remove_handler)
    word_input.returnPressed.connect(add_handler)
