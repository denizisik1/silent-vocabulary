import config
from config import AppConfig, WindowConfig


def test_load_returns_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "vipa.toml")

    loaded = config.load_config()

    assert loaded == AppConfig()


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    saved = AppConfig(theme="dark", window=WindowConfig(width=960, height=720))
    config.save_config(saved)
    loaded = config.load_config()

    assert loaded == saved


def test_load_ignores_invalid_theme(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    config_path.write_text('theme = "neon"\n', encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    loaded = config.load_config()

    assert loaded.theme == config.DEFAULT_THEME


def test_load_clamps_small_window(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    config_path.write_text("[window]\nwidth = 100\nheight = 100\n", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    loaded = config.load_config()

    assert loaded.window.width == config.DEFAULT_WINDOW_WIDTH
    assert loaded.window.height == config.DEFAULT_WINDOW_HEIGHT
