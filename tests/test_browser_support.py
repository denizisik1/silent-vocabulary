from browser_config import BrowserConfig, apply_browser_config
from retrieve.browser_fetch import (
    ensure_browser_ready,
    reset_browser_ensure_state,
    set_browser_ensure_callback,
)
from browser_support import (
    browser_install_command,
    browser_remove_command,
    find_browser_path,
)


def test_ensure_browser_ready_prompts_when_browser_missing(monkeypatch) -> None:
    reset_browser_ensure_state()
    calls = {"n": 0}
    monkeypatch.setattr(
        "retrieve.browser_fetch.browser_available",
        lambda: calls["n"] > 0,
    )

    def approve() -> bool:
        calls["n"] += 1
        return True

    set_browser_ensure_callback(approve)
    try:
        assert ensure_browser_ready()
        assert calls["n"] == 1
    finally:
        set_browser_ensure_callback(None)
        reset_browser_ensure_state()


def test_ensure_browser_ready_remembers_decline(monkeypatch) -> None:
    reset_browser_ensure_state()
    calls = {"n": 0}
    monkeypatch.setattr(
        "retrieve.browser_fetch.browser_available",
        lambda: False,
    )

    def decline() -> bool:
        calls["n"] += 1
        return False

    set_browser_ensure_callback(decline)
    try:
        assert not ensure_browser_ready()
        assert not ensure_browser_ready()
        assert calls["n"] == 1
    finally:
        set_browser_ensure_callback(None)
        reset_browser_ensure_state()


def test_find_browser_path_uses_config(tmp_path) -> None:
    browser = tmp_path / "chromium"
    browser.write_text("#!/bin/sh\n", encoding="utf-8")
    browser.chmod(0o755)
    apply_browser_config(BrowserConfig(browser_path=str(browser)))
    try:
        assert find_browser_path() == str(browser.resolve())
    finally:
        apply_browser_config(BrowserConfig())


def test_browser_install_command_for_fedora(monkeypatch) -> None:
    monkeypatch.setattr(
        "browser_support.read_os_release",
        lambda: {"ID": "fedora", "ID_LIKE": ""},
    )
    assert browser_install_command() == ["pkexec", "dnf", "install", "-y", "chromium"]
    assert browser_remove_command() == ["pkexec", "dnf", "remove", "-y", "chromium"]
