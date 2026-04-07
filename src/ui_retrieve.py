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

    def _set_busy(self, busy: bool) -> None:
        for object_name in ("pushButton_6", "pushButton_7", "pushButton_8", "pushButton_5"):
            button = self._window.findChild(QPushButton, object_name)
            if button is not None:
                button.setEnabled(not busy)

    def _cleanup_worker(self) -> None:
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(1000)
        self._thread = None
        self._worker = None
        self._set_busy(False)

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

        word = self._line("lineEdit_2").text().strip()
        if mode != "check" and not word:
            message = "Enter a word in Vocabulary before retrieving IPA."
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


def wire_retrieve(window: QMainWindow) -> None:
    primary = window.findChild(QPushButton, "pushButton_6")
    backup = window.findChild(QPushButton, "pushButton_7")
    check = window.findChild(QPushButton, "pushButton_8")
    pull_async = window.findChild(QPushButton, "pushButton_5")
    if primary is None or backup is None or check is None:
        raise RuntimeError("Missing retrieve buttons")

    controller = RetrieveController(window)
    setattr(window, _CONTROLLER_ATTR, controller)
    primary.clicked.connect(partial(controller.start, "primary"))
    backup.clicked.connect(partial(controller.start, "backup"))
    check.clicked.connect(partial(controller.start, "check"))
    if pull_async is not None:
        pull_async.clicked.connect(partial(controller.start, "async"))
    controller._progress().setValue(0)
