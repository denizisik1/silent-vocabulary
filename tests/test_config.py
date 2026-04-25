import config
from config import AppConfig, WindowConfig
from themes import stylesheet
from zoom import clamp_zoom_percent, scale_px


def test_load_returns_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "vipa.toml")

    loaded = config.load_config()

    assert loaded == AppConfig()


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    saved = AppConfig(
        theme="dark",
        zoom_percent=125,
        protect_base_vocabulary=False,
        minimize_to_tray_on_daemon=False,
        daemon_interval_minutes=30,
        notify_backend="desktop",
        language="german",
        include_fields={
            "article": False,
            "word": True,
            "meaning": True,
            "pronunciation": False,
            "example": True,
            "translation": False,
            "plural": True,
        },
        window=WindowConfig(width=960, height=720),
    )
    config.save_config(saved)
    loaded = config.load_config()

    assert loaded == saved


def test_load_protect_base_vocabulary_default_true(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "vipa.toml")

    loaded = config.load_config()

    assert loaded.protect_base_vocabulary is True


def test_load_protect_base_vocabulary_false(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    config_path.write_text("protect_base_vocabulary = false\n", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    loaded = config.load_config()

    assert loaded.protect_base_vocabulary is False


def test_load_minimize_to_tray_on_daemon_default_true(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "vipa.toml")

    loaded = config.load_config()

    assert loaded.minimize_to_tray_on_daemon is True


def test_load_minimize_to_tray_on_daemon_false(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    config_path.write_text("minimize_to_tray_on_daemon = false\n", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    loaded = config.load_config()

    assert loaded.minimize_to_tray_on_daemon is False


def test_load_daemon_interval_minutes_default(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "vipa.toml")

    loaded = config.load_config()

    assert loaded.daemon_interval_minutes == config.DEFAULT_DAEMON_INTERVAL_MINUTES


def test_load_daemon_interval_minutes_invalid_uses_default(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    config_path.write_text("daemon_interval_minutes = 0\n", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    loaded = config.load_config()

    assert loaded.daemon_interval_minutes == config.DEFAULT_DAEMON_INTERVAL_MINUTES


def test_load_notify_backend_defaults_to_desktop(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "vipa.toml")

    loaded = config.load_config()

    assert loaded.notify_backend == config.DEFAULT_NOTIFY_BACKEND


def test_load_notify_backend_unknown_uses_desktop(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    config_path.write_text('notify_backend = "carrier_pigeon"\n', encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    loaded = config.load_config()

    assert loaded.notify_backend == config.DEFAULT_NOTIFY_BACKEND


def test_load_language_defaults_to_german(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "vipa.toml")

    loaded = config.load_config()

    assert loaded.language == config.DEFAULT_LANGUAGE


def test_load_language_invalid_uses_default(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    config_path.write_text('language = "klingon"\n', encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    loaded = config.load_config()

    assert loaded.language == config.DEFAULT_LANGUAGE


def test_load_include_fields_partial_merge(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    config_path.write_text(
        "[include]\narticle = false\nexample = true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    loaded = config.load_config()

    assert loaded.include_fields["article"] is False
    assert loaded.include_fields["word"] is True
    assert loaded.include_fields["example"] is True


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


def test_load_clamps_zoom_percent(tmp_path, monkeypatch):
    config_path = tmp_path / "vipa.toml"
    config_path.write_text("zoom_percent = 999\n", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    loaded = config.load_config()

    assert loaded.zoom_percent == 150


def test_clamp_zoom_percent():
    assert clamp_zoom_percent(50) == 80
    assert clamp_zoom_percent(100) == 100
    assert clamp_zoom_percent(200) == 150


def test_scale_px():
    assert scale_px(20, 100) == 20
    assert scale_px(20, 150) == 30
    assert scale_px(20, 80) == 16


def test_stylesheet_includes_scaled_font_size():
    css = stylesheet("white", zoom_percent=150)

    assert "font-size: 30px;" in css
    assert "font-size: 21px;" in css
