from functools import partial

from PySide6.QtCore import QObject, Qt, QThread, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QTextEdit,
)
from retrieve.worker import RetrieveWorker
from ui_words import include_flags, language_key_from_combo
from words import format_word_row

_CONTROLLER_ATTR = "_vipa_retrieve_controller"
_SYNCING_ATTR = "_vipa_word_fields_syncing"


class RetrieveController(QObject):
    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._thread: QThread | None = None
        self._worker: RetrieveWorker | None = None

    def _line(self, object_name: str) -> QLineEdit:
        editor = self._window.findChild(QLineEdit, object_name)
        if editor is None:
            raise RuntimeError(f"Missing control: {object_name}")
        return editor

    def _optional_line(self, object_name: str) -> QLineEdit | None:
        return self._window.findChild(QLineEdit, object_name)

    def _results(self) -> QTextEdit:
        results = self._window.findChild(QTextEdit, "textEdit_3")
        if results is None:
            raise RuntimeError("Missing results view: textEdit_3")
        return results

    def _progress(self) -> QProgressBar:
        bar = self._window.findChild(QProgressBar, "progressBar")
        if bar is None:
            raise RuntimeError("Missing progress bar: progressBar")
        return bar

    def _set_status(self, message: str) -> None:
        status = self._window.findChild(QStatusBar, "statusbar")
        if status is not None:
            status.showMessage(message)

    def _append_results(self, message: str) -> None:
        results = self._results()
        existing = results.toPlainText().strip()
        if existing:
            results.setPlainText(f"{existing}\n{message}")
        else:
            results.setPlainText(message)

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

    def _set_busy(self, busy: bool) -> None:
        for button in self._retrieve_buttons():
            button.setEnabled(not busy)

    def _cleanup_worker(self) -> None:
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(1000)
        self._thread = None
        self._worker = None
        self._set_busy(False)

    def _word_text(self) -> str:
        retrieve_word = self._optional_line("lineEdit_retrieve_word")
        if retrieve_word is not None and retrieve_word.text().strip():
            return retrieve_word.text().strip()
        return self._line("lineEdit_2").text().strip()

    @Slot(int)
    def on_progress(self, value: int) -> None:
        self._progress().setValue(value)

    @Slot(str, object)
    def on_worker_ok(self, message: str, row: object) -> None:
        include = include_flags(self._window)
        if isinstance(row, tuple):
            self._append_results(f"{message}\n{format_word_row(row, include)}")
        else:
            self._append_results(message)
        self._set_status(message)
        self._cleanup_worker()

    @Slot(str)
    def on_worker_error(self, message: str) -> None:
        self._append_results(f"Retrieve error: {message}")
        self._set_status(f"Retrieve error: {message}")
        self._cleanup_worker()

    def start(self, mode: str) -> None:
        if self._thread is not None:
            self._set_status("Retrieve already running")
            return

        language_combo = self._window.findChild(QComboBox, "comboBox")
        if language_combo is None:
            raise RuntimeError("Missing language control: comboBox")

        word = self._word_text()
        if mode != "check" and not word:
            message = "Enter a word on Sources or Vocabulary before retrieving IPA."
            self._append_results(message)
            self._set_status(message)
            return

        language_key = language_key_from_combo(language_combo.currentText())
        worker = RetrieveWorker(
            mode=mode,
            language_key=language_key,
            word=word or "Abend",
            primary_url=self._line("lineEdit_6").text(),
            primary_find=self._line("lineEdit_8").text(),
            backup_url=self._line("lineEdit_9").text(),
            backup_find=self._line("lineEdit_7").text(),
        )
        thread = QThread(self._window)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.on_progress, Qt.ConnectionType.QueuedConnection)
        worker.finished_ok.connect(self.on_worker_ok, Qt.ConnectionType.QueuedConnection)
        worker.finished_error.connect(self.on_worker_error, Qt.ConnectionType.QueuedConnection)
        worker.finished_ok.connect(thread.quit)
        worker.finished_error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._worker = worker
        self._thread = thread
        self._set_busy(True)
        self._progress().setValue(0)
        self._set_status(f"Retrieve {mode} started")
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


def wire_retrieve(window: QMainWindow) -> None:
    fetch = window.findChild(QPushButton, "pushButton_6")
    check = window.findChild(QPushButton, "pushButton_8")
    vocab_fetch = window.findChild(QPushButton, "pushButton_vocab_fetch")
    if fetch is None or check is None:
        raise RuntimeError("Missing retrieve buttons")

    controller = RetrieveController(window)
    setattr(window, _CONTROLLER_ATTR, controller)
    _wire_word_field_sync(window)

    fetch.clicked.connect(partial(controller.start, "retrieve"))
    check.clicked.connect(partial(controller.start, "check"))
    if vocab_fetch is not None:
        vocab_fetch.clicked.connect(partial(controller.start, "retrieve"))

    retrieve_word = window.findChild(QLineEdit, "lineEdit_retrieve_word")
    if retrieve_word is not None:
        retrieve_word.returnPressed.connect(partial(controller.start, "retrieve"))

    controller._progress().setValue(0)
