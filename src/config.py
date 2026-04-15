from dataclasses import dataclass, field
from pathlib import Path

import tomlkit
from platformdirs import user_config_dir

from themes import DEFAULT_THEME, THEMES
from zoom import DEFAULT_ZOOM_PERCENT, clamp_zoom_percent

CONFIG_DIR = Path(user_config_dir("vipa", appauthor=False))
CONFIG_PATH = CONFIG_DIR / "vipa.toml"

DEFAULT_WINDOW_WIDTH = 720
DEFAULT_WINDOW_HEIGHT = 560
MIN_WINDOW_WIDTH = 560
MIN_WINDOW_HEIGHT = 420


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

    return AppConfig(
        theme=theme,
        zoom_percent=zoom_percent,
        protect_base_vocabulary=protect_base_vocabulary,
        minimize_to_tray_on_daemon=minimize_to_tray_on_daemon,
        window=window,
    )


def save_config(config: AppConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    config_data = {
        "theme": config.theme,
        "zoom_percent": clamp_zoom_percent(config.zoom_percent),
        "protect_base_vocabulary": config.protect_base_vocabulary,
        "minimize_to_tray_on_daemon": config.minimize_to_tray_on_daemon,
        "window": {
            "width": config.window.width,
            "height": config.window.height,
        },
    }
    CONFIG_PATH.write_text(tomlkit.dumps(config_data), encoding="utf-8")
