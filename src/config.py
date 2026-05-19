from dataclasses import dataclass, field
from pathlib import Path
import os

import tomlkit
from platformdirs import user_config_dir

from daemon import parse_interval_minutes
from notify import NotifyBackend
from retrieve.strategy import (
    DEFAULT_RETRIEVE_STRATEGY,
    normalize_retrieve_strategy,
)
from themes import DEFAULT_THEME, THEMES
from words.constants import DEFAULT_INCLUDE, LANGUAGE_VOCABULARY_FILES
from zoom import DEFAULT_ZOOM_PERCENT, clamp_zoom_percent

CONFIG_DIR = Path(user_config_dir("vipa", appauthor=False))
CONFIG_PATH = CONFIG_DIR / "vipa.toml"

DEFAULT_WINDOW_WIDTH = int(os.environ.get("VIPA_DEFAULT_WINDOW_WIDTH", "720"))
DEFAULT_WINDOW_HEIGHT = int(os.environ.get("VIPA_DEFAULT_WINDOW_HEIGHT", "560"))
MIN_WINDOW_WIDTH = int(os.environ.get("VIPA_MIN_WINDOW_WIDTH", "560"))
MIN_WINDOW_HEIGHT = int(os.environ.get("VIPA_MIN_WINDOW_HEIGHT", "420"))
DEFAULT_DAEMON_INTERVAL_MINUTES = int(
    os.environ.get("VIPA_DEFAULT_DAEMON_INTERVAL_MINUTES", "15")
)
DEFAULT_NOTIFY_BACKEND = os.environ.get(
    "VIPA_DEFAULT_NOTIFY_BACKEND",
    NotifyBackend.DESKTOP.value,
)
DEFAULT_LANGUAGE = os.environ.get("VIPA_DEFAULT_LANGUAGE", "german")
INCLUDE_FIELD_NAMES = tuple(DEFAULT_INCLUDE.keys())


@dataclass
class WindowConfig:
    width: int = DEFAULT_WINDOW_WIDTH
    height: int = DEFAULT_WINDOW_HEIGHT


@dataclass
class AppConfig:
    theme: str = DEFAULT_THEME
    zoom_percent: int = DEFAULT_ZOOM_PERCENT
    protect_base_vocabulary: bool = True
    minimize_to_tray_on_daemon: bool = True
    daemon_interval_minutes: int = DEFAULT_DAEMON_INTERVAL_MINUTES
    notify_backend: str = DEFAULT_NOTIFY_BACKEND
    language: str = DEFAULT_LANGUAGE
    retrieve_strategy: str = DEFAULT_RETRIEVE_STRATEGY
    include_fields: dict[str, bool] = field(default_factory=lambda: dict(DEFAULT_INCLUDE))
    window: WindowConfig = field(default_factory=WindowConfig)


def _clamp_dimension(value: int, minimum: int, default: int) -> int:
    if value < minimum:
        return default
    return value


def _is_valid_theme_name(theme_name: str) -> bool:
    return theme_name in THEMES


def _parse_window_table(window_table) -> WindowConfig:
    if not isinstance(window_table, dict):
        return WindowConfig()

    width = window_table.get("width", DEFAULT_WINDOW_WIDTH)
    height = window_table.get("height", DEFAULT_WINDOW_HEIGHT)
    if not isinstance(width, int) or not isinstance(height, int):
        return WindowConfig()

    return WindowConfig(
        width=_clamp_dimension(width, MIN_WINDOW_WIDTH, DEFAULT_WINDOW_WIDTH),
        height=_clamp_dimension(height, MIN_WINDOW_HEIGHT, DEFAULT_WINDOW_HEIGHT),
    )


def _parse_theme_name(theme_value) -> str:
    if not isinstance(theme_value, str):
        return DEFAULT_THEME
    if not _is_valid_theme_name(theme_value):
        return DEFAULT_THEME
    return theme_value


def _parse_zoom_percent(zoom_value) -> int:
    if not isinstance(zoom_value, int):
        return DEFAULT_ZOOM_PERCENT
    return clamp_zoom_percent(zoom_value)


def _parse_bool(value, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _parse_daemon_interval_minutes(value) -> int:
    if isinstance(value, int):
        try:
            return parse_interval_minutes(str(value))
        except ValueError:
            return DEFAULT_DAEMON_INTERVAL_MINUTES
    if isinstance(value, str):
        try:
            return parse_interval_minutes(value)
        except ValueError:
            return DEFAULT_DAEMON_INTERVAL_MINUTES
    return DEFAULT_DAEMON_INTERVAL_MINUTES


def _parse_notify_backend(value) -> str:
    if value == NotifyBackend.WINDOWS.value:
        return NotifyBackend.WINDOWS.value
    return NotifyBackend.DESKTOP.value


def _parse_language(value) -> str:
    if not isinstance(value, str):
        return DEFAULT_LANGUAGE
    language_key = value.strip().lower()
    if language_key in LANGUAGE_VOCABULARY_FILES:
        return language_key
    return DEFAULT_LANGUAGE


def _parse_retrieve_strategy(value) -> str:
    if not isinstance(value, str):
        return DEFAULT_RETRIEVE_STRATEGY
    return normalize_retrieve_strategy(value)


def _parse_include_fields(include_table) -> dict[str, bool]:
    include_fields = dict(DEFAULT_INCLUDE)
    if not isinstance(include_table, dict):
        return include_fields
    for field_name in INCLUDE_FIELD_NAMES:
        value = include_table.get(field_name)
        if isinstance(value, bool):
            include_fields[field_name] = value
    return include_fields


def load_config() -> AppConfig:
    if not CONFIG_PATH.is_file():
        return AppConfig()

    config_document = tomlkit.parse(CONFIG_PATH.read_text(encoding="utf-8"))
    window = _parse_window_table(config_document.get("window"))
    theme = _parse_theme_name(config_document.get("theme", DEFAULT_THEME))
    zoom_percent = _parse_zoom_percent(
        config_document.get("zoom_percent", DEFAULT_ZOOM_PERCENT)
    )
    protect_base_vocabulary = _parse_bool(
        config_document.get("protect_base_vocabulary", True),
        True,
    )
    minimize_to_tray_on_daemon = _parse_bool(
        config_document.get("minimize_to_tray_on_daemon", True),
        True,
    )
    daemon_interval_minutes = _parse_daemon_interval_minutes(
        config_document.get("daemon_interval_minutes", DEFAULT_DAEMON_INTERVAL_MINUTES)
    )
    notify_backend = _parse_notify_backend(
        config_document.get("notify_backend", DEFAULT_NOTIFY_BACKEND)
    )
    language = _parse_language(config_document.get("language", DEFAULT_LANGUAGE))
    retrieve_strategy = _parse_retrieve_strategy(
        config_document.get("retrieve_strategy", DEFAULT_RETRIEVE_STRATEGY)
    )
    include_fields = _parse_include_fields(config_document.get("include"))

    return AppConfig(
        theme=theme,
        zoom_percent=zoom_percent,
        protect_base_vocabulary=protect_base_vocabulary,
        minimize_to_tray_on_daemon=minimize_to_tray_on_daemon,
        daemon_interval_minutes=daemon_interval_minutes,
        notify_backend=notify_backend,
        language=language,
        retrieve_strategy=retrieve_strategy,
        include_fields=include_fields,
        window=window,
    )


def save_config(config: AppConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    config_data = {
        "theme": config.theme,
        "zoom_percent": clamp_zoom_percent(config.zoom_percent),
        "protect_base_vocabulary": config.protect_base_vocabulary,
        "minimize_to_tray_on_daemon": config.minimize_to_tray_on_daemon,
        "daemon_interval_minutes": config.daemon_interval_minutes,
        "notify_backend": config.notify_backend,
        "language": config.language,
        "retrieve_strategy": normalize_retrieve_strategy(config.retrieve_strategy),
        "include": {
            field_name: config.include_fields[field_name]
            for field_name in INCLUDE_FIELD_NAMES
        },
        "window": {
            "width": config.window.width,
            "height": config.window.height,
        },
    }
    CONFIG_PATH.write_text(tomlkit.dumps(config_data), encoding="utf-8")
