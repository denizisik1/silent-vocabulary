import os

from PySide6.QtCore import QObject, Signal

from retrieve import check_source_capabilities
from retrieve.service import SourceEndpoint, retrieve_ipa_with_strategy
from retrieve.strategy import DEFAULT_RETRIEVE_STRATEGY, normalize_retrieve_strategy
from words import upsert_pronunciation


class RetrieveWorker(QObject):
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
        retrieve_strategy: str = DEFAULT_RETRIEVE_STRATEGY,
    ) -> None:
        super().__init__()
        self._mode = mode
        self._language_key = language_key
        self._word = word
        self._primary_url = primary_url
        self._primary_find = primary_find
        self._backup_url = backup_url
        self._backup_find = backup_find
        self._retrieve_strategy = normalize_retrieve_strategy(retrieve_strategy)

    def run(self) -> None:
        try:
            if self._mode == "check":
                self._run_check()
                return
            self._run_retrieve()
        except Exception as error:  # noqa: BLE001 - surface unexpected worker errors
            self.finished_error.emit(str(error))

    def _run_check(self) -> None:
        word = self._word or os.environ.get("VIPA_SAMPLE_WORD", "Abend")
        primary = check_source_capabilities(
            base_url=self._primary_url,
            find_by=self._primary_find,
            sample_word=word,
            source_label="primary",
        )
        backup = check_source_capabilities(
            base_url=self._backup_url,
            find_by=self._backup_find,
            sample_word=word,
            source_label="backup",
        )
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
            f"Strategy: {self._retrieve_strategy}",
        ]
        self.finished_ok.emit("\n".join(lines), None)

    def _run_retrieve(self) -> None:
        try:
            result = retrieve_ipa_with_strategy(
                word=self._word,
                primary=SourceEndpoint(
                    label="primary",
                    base_url=self._primary_url,
                    find_by=self._primary_find,
                ),
                backup=SourceEndpoint(
                    label="backup",
                    base_url=self._backup_url,
                    find_by=self._backup_find,
                ),
                strategy=self._retrieve_strategy,
            )
        except (ValueError, RuntimeError, OSError) as error:
            self.finished_error.emit(str(error))
            return

        row = upsert_pronunciation(
            self._language_key,
            result.word,
            result.pronunciation,
            source=result.url,
        )
        message = (
            f"Retrieved via {result.source_label} ({result.fetch_method}): "
            f"{result.word} {result.pronunciation}"
        )
        self.finished_ok.emit(message, row)
