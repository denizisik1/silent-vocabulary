from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QLineEdit,
    QListView,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
)
from config import AppConfig, save_config
from ui_disambiguate import choose_entry
from words import (
    DEFAULT_INCLUDE,
    AmbiguousWordError,
    WordFields,
    add_word,
    describe_entry,
    format_word_row,
    get_random_words,
    remove_word,
)
from words.constants import LANGUAGE_VOCABULARY_FILES
from words.parse import normalize_row

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

_DEFAULT_FAINT = "#777777"


def language_key_from_combo(language_text: str) -> str:
    return language_text.strip().lower()


def style_language_combo(window: QMainWindow, faint_color: str = _DEFAULT_FAINT) -> None:
    language_combo = window.findChild(QComboBox, "comboBox")
    if language_combo is None:
        raise RuntimeError("Missing language control: comboBox")

    if not isinstance(language_combo.view(), QListView):
        language_combo.setView(QListView(language_combo))

    model = language_combo.model()
    if not isinstance(model, QStandardItemModel):
        return

    faint = QBrush(QColor(faint_color))
    for index in range(language_combo.count()):
        item = model.item(index)
        if item is None:
            continue
        language_key = language_key_from_combo(item.text())
        if language_key in LANGUAGE_VOCABULARY_FILES:
            item.setEnabled(True)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            item.setData(None, Qt.ItemDataRole.ForegroundRole)
            continue
        item.setEnabled(False)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setData(faint, Qt.ItemDataRole.ForegroundRole)


def disable_unavailable_languages(language_combo: QComboBox) -> None:
    window = language_combo.window()
    if isinstance(window, QMainWindow):
        style_language_combo(window)
        return
    raise RuntimeError("Language combo is not inside a main window")


def include_flags(window: QMainWindow) -> dict[str, bool]:
    flags = dict(DEFAULT_INCLUDE)
    for field_name, object_name in _INCLUDE_CHECKBOXES.items():
        checkbox = window.findChild(QCheckBox, object_name)
        if checkbox is None:
            raise RuntimeError(f"Missing include control: {object_name}")
        flags[field_name] = checkbox.isChecked()
    return flags


def apply_include_from_config(window: QMainWindow, include_fields: dict[str, bool]) -> None:
    for field_name, object_name in _INCLUDE_CHECKBOXES.items():
        checkbox = window.findChild(QCheckBox, object_name)
        if checkbox is None:
            raise RuntimeError(f"Missing include control: {object_name}")
        checkbox.blockSignals(True)
        checkbox.setChecked(include_fields.get(field_name, DEFAULT_INCLUDE[field_name]))
        checkbox.blockSignals(False)

    include_group = window.findChild(QGroupBox, "groupBox_13")
    if include_group is not None:
        include_group.setChecked(True)


def apply_language_from_config(window: QMainWindow, language_key: str) -> None:
    language_combo = window.findChild(QComboBox, "comboBox")
    if language_combo is None:
        raise RuntimeError("Missing language control: comboBox")

    disable_unavailable_languages(language_combo)
    if language_key not in LANGUAGE_VOCABULARY_FILES:
        return

    for index in range(language_combo.count()):
        item_text = language_combo.itemText(index)
        if language_key_from_combo(item_text) == language_key:
            language_combo.blockSignals(True)
            language_combo.setCurrentIndex(index)
            language_combo.blockSignals(False)
            return


def apply_session_config(window: QMainWindow, config: AppConfig) -> None:
    apply_include_from_config(window, config.include_fields)
    apply_language_from_config(window, config.language)


def _on_include_toggled(
    window: QMainWindow,
    config: AppConfig,
    field_name: str,
    checked: bool,
) -> None:
    config.include_fields[field_name] = checked
    save_config(config)


def _on_language_changed(window: QMainWindow, config: AppConfig, index: int) -> None:
    if index < 0:
        return
    language_combo = window.findChild(QComboBox, "comboBox")
    if language_combo is None:
        raise RuntimeError("Missing language control: comboBox")
    language_key = language_key_from_combo(language_combo.itemText(index))
    if language_key not in LANGUAGE_VOCABULARY_FILES:
        return
    config.language = language_key
    save_config(config)


def wire_session_config(window: QMainWindow, config: AppConfig) -> None:
    for field_name, object_name in _INCLUDE_CHECKBOXES.items():
        checkbox = window.findChild(QCheckBox, object_name)
        if checkbox is None:
            raise RuntimeError(f"Missing include control: {object_name}")
        handler = partial(_on_include_toggled, window, config, field_name)
        checkbox.toggled.connect(handler)

    language_combo = window.findChild(QComboBox, "comboBox")
    if language_combo is None:
        raise RuntimeError("Missing language control: comboBox")
    disable_unavailable_languages(language_combo)
    language_handler = partial(_on_language_changed, window, config)
    language_combo.currentIndexChanged.connect(language_handler)


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


def populate_add_form_from_row(window: QMainWindow, row: tuple) -> None:
    (
        article,
        word,
        meaning,
        pronunciation,
        classification,
        source,
        example,
        translation,
        plural,
    ) = normalize_row(row)

    field_values = {
        "lineEdit_add_article": article,
        "lineEdit_2": word,
        "lineEdit_add_meaning": meaning,
        "lineEdit_add_pronunciation": pronunciation,
        "lineEdit_add_source": source,
        "lineEdit_add_example": example,
        "lineEdit_add_translation": translation,
        "lineEdit_add_plural": plural,
    }
    for object_name, value in field_values.items():
        editor = window.findChild(QLineEdit, object_name)
        if editor is None:
            raise RuntimeError(f"Missing Add Word control: {object_name}")
        editor.setText(value or "")

    classification_combo = window.findChild(QComboBox, "comboBox_add_classification")
    if classification_combo is None:
        raise RuntimeError("Missing Add Word control: comboBox_add_classification")
    if classification:
        index = classification_combo.findText(classification)
        if index >= 0:
            classification_combo.setCurrentIndex(index)


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
    word = word_input.text()
    try:
        removed = remove_chosen_entry(window, language_key, word)
    except (ValueError, FileNotFoundError, OSError) as error:
        results.setPlainText(str(error))
        return

    if removed is None:
        results.setPlainText("Removal cancelled: no entry chosen")
        return

    word_input.clear()
    results.setPlainText(f"Removed: {describe_entry(removed)}")


def remove_chosen_entry(window: QMainWindow, language_key: str, word: str) -> tuple | None:
    try:
        return remove_word(language_key, word)
    except AmbiguousWordError as ambiguity:
        chosen = choose_entry(window, word, ambiguity.candidates)
        if chosen is None:
            return None
        return remove_word(
            language_key,
            chosen[1],
            classification=chosen[4],
            article=chosen[0],
        )


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
