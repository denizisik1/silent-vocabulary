from dataclasses import dataclass, field
from pathlib import Path

import tomlkit
from platformdirs import user_config_dir

from themes import DEFAULT_THEME, THEMES

CONFIG_DIR = Path(user_config_dir("vipa", appauthor=False))
CONFIG_PATH = CONFIG_DIR / "vipa.toml"

DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 600
MIN_WINDOW_WIDTH = 520
MIN_WINDOW_HEIGHT = 400


@dataclass
class WindowConfig:
    width: int = DEFAULT_WINDOW_WIDTH
    height: int = DEFAULT_WINDOW_HEIGHT


@dataclass
class AppConfig:
    theme: str = DEFAULT_THEME
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


def load_config() -> AppConfig:
    if not CONFIG_PATH.is_file():
        return AppConfig()

    config_document = tomlkit.parse(CONFIG_PATH.read_text(encoding="utf-8"))
    window = _parse_window_table(config_document.get("window"))
    theme = _parse_theme_name(config_document.get("theme", DEFAULT_THEME))

    return AppConfig(theme=theme, window=window)


def save_config(config: AppConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    config_data = {
        "theme": config.theme,
        "window": {
            "width": config.window.width,
            "height": config.window.height,
        },
    }
    CONFIG_PATH.write_text(tomlkit.dumps(config_data), encoding="utf-8")
