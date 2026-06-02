RESULT_SEPARATOR = "────────"


class RetrieveResultsLog:
    def __init__(self) -> None:
        self._archive = ""
        self._live = ""
        self._showing_archive = False

    def append(self, message: str, *, begin_session: bool = False) -> None:
        text = message.strip("\n")
        if not text:
            return
        if not self._live.strip():
            self._live = text
            return
        if begin_session:
            self._live = f"{self._live.rstrip()}\n{RESULT_SEPARATOR}\n{text}"
            return
        self._live = f"{self._live.rstrip()}\n{text}"

    def clear(self) -> None:
        live = self._live.strip()
        if live:
            if self._archive.strip():
                self._archive = f"{self._archive.rstrip()}\n{RESULT_SEPARATOR}\n{live}"
            else:
                self._archive = live
        self._live = ""
        self._showing_archive = False

    def toggle_show_cleared(self) -> bool:
        if not self._archive.strip():
            self._showing_archive = False
            return False
        self._showing_archive = not self._showing_archive
        return self._showing_archive

    def has_archive(self) -> bool:
        return bool(self._archive.strip())

    def showing_archive(self) -> bool:
        return self._showing_archive

    def display_text(self) -> str:
        live = self._live.strip()
        archive = self._archive.strip()
        if self._showing_archive and archive:
            if live:
                return f"{archive}\n{RESULT_SEPARATOR}\n{live}"
            return archive
        return live
