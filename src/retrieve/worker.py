from PySide6.QtCore import QObject, Signal

from retrieve import check_source_capabilities, retrieve_ipa
from words import upsert_pronunciation


class RetrieveWorker(QObject):
    progress = Signal(int)
    finished_ok = Signal(str, object)
    finished_error = Signal(str)

    def __init__(
        self,
        *,
        mode: str,
        language_key: str,
        word: str,
        primary_url: str,
        primary_find: str,
        backup_url: str,
        backup_find: str,
    ) -> None:
        super().__init__()
        self._mode = mode
        self._language_key = language_key
        self._word = word
        self._primary_url = primary_url
        self._primary_find = primary_find
        self._backup_url = backup_url
        self._backup_find = backup_find

    def run(self) -> None:
        try:
            if self._mode == "check":
                self._run_check()
                return
            self._run_retrieve()
        except Exception as error:  # noqa: BLE001 - surface unexpected worker errors
            self.finished_error.emit(str(error))

    def _run_check(self) -> None:
        self.progress.emit(20)
        primary = check_source_capabilities(
            base_url=self._primary_url,
            find_by=self._primary_find,
            sample_word=self._word or "Abend",
            source_label="primary",
        )
        self.progress.emit(60)
        backup = check_source_capabilities(
            base_url=self._backup_url,
            find_by=self._backup_find,
            sample_word=self._word or "Abend",
            source_label="backup",
        )
        self.progress.emit(100)
        lines = [
            (
                f"Primary: reachable={primary.reachable} "
                f"ipa={primary.ipa_found} detail={primary.detail}"
                + (f" sample={primary.sample_ipa}" if primary.sample_ipa else "")
            ),
            (
                f"Backup: reachable={backup.reachable} "
                f"ipa={backup.ipa_found} detail={backup.detail}"
                + (f" sample={backup.sample_ipa}" if backup.sample_ipa else "")
            ),
        ]
        self.finished_ok.emit("\n".join(lines), None)

    def _run_retrieve(self) -> None:
        sources = [
            ("primary", self._primary_url, self._primary_find),
            ("backup", self._backup_url, self._backup_find),
        ]

        errors: list[str] = []
        total = len(sources)
        for index, (label, url, find_by) in enumerate(sources, start=1):
            self.progress.emit(int((index - 1) / total * 100))
            try:
                result = retrieve_ipa(
                    base_url=url,
                    find_by=find_by,
                    word=self._word,
                    source_label=label,
                )
                row = upsert_pronunciation(
                    self._language_key,
                    result.word,
                    result.pronunciation,
                    source=result.url,
                )
                self.progress.emit(100)
                message = f"Retrieved via {label}: {result.word} {result.pronunciation}"
                self.finished_ok.emit(message, row)
                return
            except (ValueError, RuntimeError, OSError) as error:
                errors.append(f"{label}: {error}")

        self.progress.emit(100)
        self.finished_error.emit(" | ".join(errors) if errors else "Retrieve failed")
