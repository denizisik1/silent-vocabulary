from stealth_config import StealthConfig, apply_stealth_config
from retrieve.stealth_fetch import (
    ensure_stealth_ready,
    reset_stealth_ensure_state,
    set_stealth_ensure_callback,
)
from stealth_browser import (
    browser_install_command,
    browser_remove_command,
    find_stealth_browser_path,
)


def test_ensure_stealth_ready_prompts_when_browser_missing(monkeypatch) -> None:
    reset_stealth_ensure_state()
    calls = {"n": 0}
    monkeypatch.setattr(
        "retrieve.stealth_fetch.stealth_browser_available",
        lambda: calls["n"] > 0,
    )

    def approve() -> bool:
        calls["n"] += 1
        return True

    set_stealth_ensure_callback(approve)
    try:
        assert ensure_stealth_ready()
        assert calls["n"] == 1
    finally:
        set_stealth_ensure_callback(None)
        reset_stealth_ensure_state()


def test_ensure_stealth_ready_remembers_decline(monkeypatch) -> None:
    reset_stealth_ensure_state()
    calls = {"n": 0}
    monkeypatch.setattr(
        "retrieve.stealth_fetch.stealth_browser_available",
        lambda: False,
    )

    def decline() -> bool:
        calls["n"] += 1
        return False

    set_stealth_ensure_callback(decline)
    try:
        assert not ensure_stealth_ready()
        assert not ensure_stealth_ready()
        assert calls["n"] == 1
    finally:
        set_stealth_ensure_callback(None)
        reset_stealth_ensure_state()


def test_find_stealth_browser_path_uses_config(tmp_path) -> None:
    browser = tmp_path / "chromium"
    browser.write_text("#!/bin/sh\n", encoding="utf-8")
    browser.chmod(0o755)
    apply_stealth_config(StealthConfig(browser_path=str(browser)))
    try:
        assert find_stealth_browser_path() == str(browser.resolve())
    finally:
        apply_stealth_config(StealthConfig())


def test_browser_install_command_for_fedora(monkeypatch) -> None:
    monkeypatch.setattr(
        "stealth_browser.read_os_release",
        lambda: {"ID": "fedora", "ID_LIKE": ""},
    )
    assert browser_install_command() == ["pkexec", "dnf", "install", "-y", "chromium"]
    assert browser_remove_command() == ["pkexec", "dnf", "remove", "-y", "chromium"]
