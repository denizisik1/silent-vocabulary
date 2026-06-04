from functools import partial
import os

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Slot
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QTextEdit,
)
from config import AppConfig, save_config
from retrieve.strategy import (
    STRATEGY_BASIC_FIRST,
    STRATEGY_PRIMARY_FIRST,
    normalize_retrieve_strategy,
)
from retrieve.worker import RetrieveWorker
from ui_retrieve_log import RetrieveResultsLog
from ui_stealth_browser import wire_stealth_browser_prompt
from ui_words import include_flags, language_key_from_combo, populate_add_form_from_row
from words import format_word_row

_CONTROLLER_ATTR = "_vipa_retrieve_controller"
_SYNCING_ATTR = "_vipa_word_fields_syncing"
_RESULT_FLASH_MS = int(os.environ.get("VIPA_RETRIEVE_FLASH_MS", "1200"))
_RESULTS_OBJECT_NAMES = (
    "textEdit_retrieve_results",
    "textEdit_vocab_retrieve_results",
)
_CLEAR_BUTTON_NAMES = (
    "pushButton_retrieve_clear",
    "pushButton_vocab_retrieve_clear",
)
_SHOW_CLEARED_BUTTON_NAMES = (
    "pushButton_retrieve_show_cleared",
    "pushButton_vocab_retrieve_show_cleared",
)
_STRATEGY_RADIOS = {
    STRATEGY_PRIMARY_FIRST: (
        "radioButton_retrievePrimaryFirst",
        "radioButton_vocabRetrievePrimaryFirst",
    ),
    STRATEGY_BASIC_FIRST: (
        "radioButton_retrieveBasicFirst",
        "radioButton_vocabRetrieveBasicFirst",
    ),
}


class RetrieveController(QObject):
    def __init__(self, window: QMainWindow, config: AppConfig) -> None:
        super().__init__(window)
        self._window = window
        self._config = config
        self._thread: QThread | None = None
        self._worker: RetrieveWorker | None = None
        self._active_button: QPushButton | None = None
        self._busy = False
        self._results_log = RetrieveResultsLog()
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._finish_feedback)

    def _line(self, object_name: str) -> QLineEdit:
        editor = self._window.findChild(QLineEdit, object_name)
        if editor is None:
            raise RuntimeError(f"Missing control: {object_name}")
        return editor

    def _optional_line(self, object_name: str) -> QLineEdit | None:
        return self._window.findChild(QLineEdit, object_name)

    def _result_views(self) -> list[QTextEdit]:
        views: list[QTextEdit] = []
        for object_name in _RESULTS_OBJECT_NAMES:
            results = self._window.findChild(QTextEdit, object_name)
            if results is not None:
                views.append(results)
        if not views:
            raise RuntimeError(
                f"Missing results view: one of {_RESULTS_OBJECT_NAMES}"
            )
        return views

    def _show_cleared_buttons(self) -> list[QPushButton]:
        buttons: list[QPushButton] = []
        for object_name in _SHOW_CLEARED_BUTTON_NAMES:
            button = self._window.findChild(QPushButton, object_name)
            if button is not None:
                buttons.append(button)
        return buttons

    def _scroll_results_to_bottom(self, results: QTextEdit) -> None:
        cursor = results.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        results.setTextCursor(cursor)
        scrollbar = results.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _refresh_results_views(self) -> None:
        text = self._results_log.display_text()
        for results in self._result_views():
            results.setPlainText(text)
            self._scroll_results_to_bottom(results)
        QTimer.singleShot(0, self._scroll_all_results_to_bottom)
        self._sync_show_cleared_buttons()

    def _scroll_all_results_to_bottom(self) -> None:
        for results in self._result_views():
            self._scroll_results_to_bottom(results)

    def _sync_show_cleared_buttons(self) -> None:
        has_archive = self._results_log.has_archive()
        showing = self._results_log.showing_archive()
        label = "Hide cleared" if showing else "Show cleared"
        for button in self._show_cleared_buttons():
            button.setEnabled(has_archive)
            button.setText(label)

    def _append_results(self, message: str, *, begin_session: bool = False) -> None:
        self._results_log.append(message, begin_session=begin_session)
        self._refresh_results_views()

    def clear_results(self) -> None:
        self._results_log.clear()
        self._refresh_results_views()

    def toggle_show_cleared(self) -> None:
        self._results_log.toggle_show_cleared()
        self._refresh_results_views()

    def _retrieve_buttons(self) -> list[QPushButton]:
        buttons: list[QPushButton] = []
        for object_name in (
            "pushButton_6",
            "pushButton_8",
            "pushButton_vocab_fetch",
        ):
            button = self._window.findChild(QPushButton, object_name)
            if button is not None:
                buttons.append(button)
        return buttons

    def _set_buttons_enabled(self, enabled: bool) -> None:
        for button in self._retrieve_buttons():
            button.setEnabled(enabled)

    def _apply_button_state(self, button: QPushButton | None, state: str | None) -> None:
        if button is None:
            return
        button.setProperty("retrieveState", state)
        style = button.style()
        style.unpolish(button)
        style.polish(button)
        button.update()

    def _finish_feedback(self) -> None:
        self._apply_button_state(self._active_button, None)
        self._active_button = None

    def _flash_result(self, succeeded: bool) -> None:
        self._busy = False
        self._set_buttons_enabled(True)
        if self._active_button is None:
            return
        state = "ok" if succeeded else "error"
        self._apply_button_state(self._active_button, state)
        self._flash_timer.start(_RESULT_FLASH_MS)

    def _cleanup_worker(self) -> None:
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(1000)
        self._thread = None
        self._worker = None

    def _word_text(self) -> str:
        retrieve_word = self._optional_line("lineEdit_retrieve_word")
        if retrieve_word is not None and retrieve_word.text().strip():
            return retrieve_word.text().strip()
        return self._line("lineEdit_2").text().strip()

    @Slot(str, object)
    def on_worker_ok(self, message: str, row: object) -> None:
        include = include_flags(self._window)
        if isinstance(row, tuple):
            self._append_results(f"{message}\n{format_word_row(row, include)}")
            populate_add_form_from_row(self._window, row)
        else:
            self._append_results(message)
        self._cleanup_worker()
        self._flash_result(True)

    @Slot(str)
    def on_worker_error(self, message: str) -> None:
        self._append_results(f"Retrieve error: {message}")
        self._cleanup_worker()
        self._flash_result(False)

    def start(self, mode: str, button: QPushButton | None = None) -> None:
        if self._busy:
            self._append_results("Retrieve already running", begin_session=True)
            return

        language_combo = self._window.findChild(QComboBox, "comboBox")
        if language_combo is None:
            raise RuntimeError("Missing language control: comboBox")

        word = self._word_text()
        if mode != "check" and not word:
            message = "Enter a word on Sources or Vocabulary before retrieving IPA."
            self._append_results(message, begin_session=True)
            return

        self._flash_timer.stop()
        self._apply_button_state(self._active_button, None)
        self._busy = True
        self._set_buttons_enabled(False)

        language_key = language_key_from_combo(language_combo.currentText())
        worker = RetrieveWorker(
            mode=mode,
            language_key=language_key,
            word=word or os.environ.get("VIPA_SAMPLE_WORD", "Abend"),
            primary_url=self._line("lineEdit_6").text(),
            primary_find=self._line("lineEdit_8").text(),
            backup_url=self._line("lineEdit_9").text(),
            backup_find=self._line("lineEdit_7").text(),
            retrieve_strategy=self._config.retrieve_strategy,
        )
        thread = QThread(self._window)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished_ok.connect(self.on_worker_ok, Qt.ConnectionType.QueuedConnection)
        worker.finished_error.connect(self.on_worker_error, Qt.ConnectionType.QueuedConnection)
        worker.finished_ok.connect(thread.quit)
        worker.finished_error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._worker = worker
        self._thread = thread
        self._active_button = button
        self._apply_button_state(button, "running")
        self._append_results(f"Retrieve {mode} started", begin_session=True)
        thread.start()


def _sync_word_fields(window: QMainWindow, source_name: str, text: str) -> None:
    if getattr(window, _SYNCING_ATTR, False):
        return
    target_name = (
        "lineEdit_2" if source_name == "lineEdit_retrieve_word" else "lineEdit_retrieve_word"
    )
    target = window.findChild(QLineEdit, target_name)
    if target is None:
        return
    setattr(window, _SYNCING_ATTR, True)
    try:
        if target.text() != text:
            target.setText(text)
    finally:
        setattr(window, _SYNCING_ATTR, False)


def _wire_word_field_sync(window: QMainWindow) -> None:
    vocabulary_word = window.findChild(QLineEdit, "lineEdit_2")
    retrieve_word = window.findChild(QLineEdit, "lineEdit_retrieve_word")
    if vocabulary_word is None or retrieve_word is None:
        return

    retrieve_word.setText(vocabulary_word.text())
    vocabulary_word.textChanged.connect(
        partial(_sync_word_fields, window, "lineEdit_2")
    )
    retrieve_word.textChanged.connect(
        partial(_sync_word_fields, window, "lineEdit_retrieve_word")
    )


def _apply_source_defaults(window: QMainWindow) -> None:
    defaults = {
        "lineEdit_6": os.environ.get(
            "VIPA_PRIMARY_SOURCE_URL",
            "https://en.pons.com/translate/german-english/",
        ),
        "lineEdit_8": os.environ.get("VIPA_PRIMARY_FIND_BY", "phonetics"),
        "lineEdit_9": os.environ.get(
            "VIPA_BACKUP_SOURCE_URL",
            "https://www.collinsdictionary.com/dictionary/german-english/",
        ),
        "lineEdit_7": os.environ.get("VIPA_BACKUP_FIND_BY", "pron"),
    }
    for object_name, value in defaults.items():
        editor = window.findChild(QLineEdit, object_name)
        if editor is not None:
            editor.setText(value)


def _swap_line_edit_text(window: QMainWindow, first_name: str, second_name: str) -> None:
    first = window.findChild(QLineEdit, first_name)
    second = window.findChild(QLineEdit, second_name)
    if first is None or second is None:
        raise RuntimeError(f"Missing source fields: {first_name}, {second_name}")
    first_text = first.text()
    first.setText(second.text())
    second.setText(first_text)


def swap_primary_backup_sources(window: QMainWindow) -> None:
    _swap_line_edit_text(window, "lineEdit_6", "lineEdit_9")
    _swap_line_edit_text(window, "lineEdit_8", "lineEdit_7")


def _wire_swap_sources(window: QMainWindow) -> None:
    button = window.findChild(QPushButton, "pushButton_swap_sources")
    if button is None:
        raise RuntimeError("Missing control: pushButton_swap_sources")
    button.clicked.connect(partial(swap_primary_backup_sources, window))


def selected_retrieve_strategy(window: QMainWindow) -> str:
    for strategy, object_names in _STRATEGY_RADIOS.items():
        for object_name in object_names:
            button = window.findChild(QRadioButton, object_name)
            if button is not None and button.isChecked():
                return strategy
    return STRATEGY_PRIMARY_FIRST


def _select_retrieve_strategy(window: QMainWindow, strategy: str) -> None:
    normalized = normalize_retrieve_strategy(strategy)
    for retrieve_strategy, object_names in _STRATEGY_RADIOS.items():
        checked = retrieve_strategy == normalized
        for object_name in object_names:
            button = window.findChild(QRadioButton, object_name)
            if button is None:
                continue
            button.blockSignals(True)
            button.setChecked(checked)
            button.blockSignals(False)


def _on_retrieve_strategy_toggled(
    window: QMainWindow,
    config: AppConfig,
    strategy: str,
    checked: bool,
) -> None:
    if not checked:
        return
    config.retrieve_strategy = strategy
    _select_retrieve_strategy(window, strategy)
    save_config(config)


def _wire_retrieve_strategy(window: QMainWindow, config: AppConfig) -> None:
    _select_retrieve_strategy(window, config.retrieve_strategy)
    for strategy, object_names in _STRATEGY_RADIOS.items():
        for object_name in object_names:
            button = window.findChild(QRadioButton, object_name)
            if button is None:
                raise RuntimeError(f"Missing retrieve strategy control: {object_name}")
            handler = partial(_on_retrieve_strategy_toggled, window, config, strategy)
            button.toggled.connect(handler)


def _wire_results_actions(window: QMainWindow, controller: RetrieveController) -> None:
    for object_name in _CLEAR_BUTTON_NAMES:
        button = window.findChild(QPushButton, object_name)
        if button is None:
            raise RuntimeError(f"Missing results control: {object_name}")
        button.clicked.connect(controller.clear_results)
    for object_name in _SHOW_CLEARED_BUTTON_NAMES:
        button = window.findChild(QPushButton, object_name)
        if button is None:
            raise RuntimeError(f"Missing results control: {object_name}")
        button.clicked.connect(controller.toggle_show_cleared)
    controller._sync_show_cleared_buttons()


def wire_retrieve(window: QMainWindow, config: AppConfig) -> None:
    fetch = window.findChild(QPushButton, "pushButton_6")
    check = window.findChild(QPushButton, "pushButton_8")
    vocab_fetch = window.findChild(QPushButton, "pushButton_vocab_fetch")
    if fetch is None or check is None:
        raise RuntimeError("Missing retrieve buttons")

    controller = RetrieveController(window, config)
    setattr(window, _CONTROLLER_ATTR, controller)
    _apply_source_defaults(window)
    _wire_word_field_sync(window)
    _wire_retrieve_strategy(window, config)
    _wire_swap_sources(window)
    _wire_results_actions(window, controller)
    wire_stealth_browser_prompt(window)

    fetch.clicked.connect(partial(controller.start, "retrieve", fetch))
    check.clicked.connect(partial(controller.start, "check", check))
    if vocab_fetch is not None:
        vocab_fetch.clicked.connect(partial(controller.start, "retrieve", vocab_fetch))

    retrieve_word = window.findChild(QLineEdit, "lineEdit_retrieve_word")
    if retrieve_word is not None:
        retrieve_word.returnPressed.connect(partial(controller.start, "retrieve", fetch))
