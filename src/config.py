"""Load and save application settings in ~/.config/vipa/vipa.toml."""

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


def load_config() -> AppConfig:
    if not CONFIG_PATH.is_file():
        return AppConfig()

    doc = tomlkit.parse(CONFIG_PATH.read_text(encoding="utf-8"))
    window_table = doc.get("window")
    window = WindowConfig()
    if isinstance(window_table, dict):
        width = window_table.get("width", DEFAULT_WINDOW_WIDTH)
        height = window_table.get("height", DEFAULT_WINDOW_HEIGHT)
        if isinstance(width, int) and isinstance(height, int):
            window = WindowConfig(
                width=_clamp_dimension(width, MIN_WINDOW_WIDTH, DEFAULT_WINDOW_WIDTH),
                height=_clamp_dimension(height, MIN_WINDOW_HEIGHT, DEFAULT_WINDOW_HEIGHT),
            )

    theme = doc.get("theme", DEFAULT_THEME)
    if not isinstance(theme, str) or theme not in THEMES:
        theme = DEFAULT_THEME

    return AppConfig(theme=theme, window=window)


def save_config(config: AppConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    doc = {
        "theme": config.theme,
        "window": {
            "width": config.window.width,
            "height": config.window.height,
        },
    }
    CONFIG_PATH.write_text(tomlkit.dumps(doc), encoding="utf-8")
