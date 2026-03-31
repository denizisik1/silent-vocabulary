from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer


def parse_interval_minutes(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        raise ValueError("Interval is empty.")
    try:
        minutes = int(stripped)
    except ValueError as error:
        raise ValueError("Interval must be a whole number of minutes.") from error
    if minutes < 1:
        raise ValueError("Interval must be at least 1 minute.")
    return minutes


class PracticeDaemon(QObject):
    def __init__(self, on_tick: Callable[[], None], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._on_tick = on_tick
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._handle_timeout)
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def start(self, interval_minutes: int, *, fire_immediately: bool = True) -> None:
        if interval_minutes < 1:
            raise ValueError("Interval must be at least 1 minute.")
        self.stop()
        self._timer.setInterval(interval_minutes * 60_000)
        self._timer.start()
        self._running = True
        if fire_immediately:
            self._on_tick()

    def stop(self) -> None:
        self._timer.stop()
        self._running = False

    def _handle_timeout(self) -> None:
        self._on_tick()
