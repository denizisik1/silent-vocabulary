import pytest

from browser_config import BrowserConfig, apply_browser_config
from browser_support import (
    browser_install_command,
    browser_remove_command,
    find_browser_path,
    install_browser,
    read_os_release,
    remove_browser,
)


@pytest.fixture(autouse=True)
def default_browser_config():
    apply_browser_config(BrowserConfig())
    yield
    apply_browser_config(BrowserConfig())


class CompletedCommand:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def use_os_release(monkeypatch, values):
    monkeypatch.setattr("browser_support.read_os_release", lambda: values)


def executable(tmp_path, name):
    path = tmp_path / name
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_a_configured_browser_path_wins(tmp_path, monkeypatch):
    browser = executable(tmp_path, "chromium")
    monkeypatch.setattr("browser_support.shutil.which", lambda name: "/usr/bin/google-chrome")
    apply_browser_config(BrowserConfig(browser_path=str(browser)))

    assert find_browser_path() == str(browser.resolve())


def test_a_configured_path_that_is_not_executable_is_ignored(tmp_path, monkeypatch):
    not_a_browser = tmp_path / "chromium"
    not_a_browser.write_text("", encoding="utf-8")
    not_a_browser.chmod(0o644)
    monkeypatch.setattr("browser_support.shutil.which", lambda name: "/usr/bin/chromium")
    apply_browser_config(BrowserConfig(browser_path=str(not_a_browser)))

    assert find_browser_path() == "/usr/bin/chromium"


def test_the_first_known_browser_on_the_path_is_used(monkeypatch):
    monkeypatch.setattr(
        "browser_support.shutil.which",
        lambda name: "/usr/bin/brave" if name == "brave-browser" else None,
    )

    assert find_browser_path() == "/usr/bin/brave"


def test_os_release_is_parsed_into_unquoted_values(tmp_path, monkeypatch):
    release = tmp_path / "os-release"
    release.write_text('ID="fedora"\nVERSION_ID=44\nPRETTY_NAME="Fedora Linux"\n', "utf-8")
    monkeypatch.setattr("browser_support.Path", lambda _path: release)

    assert read_os_release() == {
        "ID": "fedora",
        "VERSION_ID": "44",
        "PRETTY_NAME": "Fedora Linux",
    }


def test_a_missing_os_release_yields_no_values(tmp_path, monkeypatch):
    monkeypatch.setattr("browser_support.Path", lambda _path: tmp_path / "absent")

    assert not read_os_release()


@pytest.mark.parametrize(
    ("release", "install", "remove"),
    [
        ({"ID": "fedora"}, ["dnf", "install", "-y"], ["dnf", "remove", "-y"]),
        ({"ID": "ubuntu"}, ["apt-get", "install", "-y"], ["apt-get", "remove", "-y"]),
        ({"ID": "manjaro"}, ["pacman", "-S", "--noconfirm"], ["pacman", "-R", "--noconfirm"]),
    ],
)
def test_each_distribution_family_gets_its_package_manager(monkeypatch, release, install, remove):
    use_os_release(monkeypatch, release)

    assert browser_install_command() == ["pkexec", *install, "chromium"]
    assert browser_remove_command() == ["pkexec", *remove, "chromium"]


def test_a_derivative_is_recognised_through_id_like(monkeypatch):
    use_os_release(monkeypatch, {"ID": "linuxmint", "ID_LIKE": "ubuntu debian"})

    assert browser_install_command() == ["pkexec", "apt-get", "install", "-y", "chromium"]


def test_an_unknown_distribution_has_no_command(monkeypatch):
    use_os_release(monkeypatch, {"ID": "plan9"})

    assert browser_install_command() is None
    assert browser_remove_command() is None


def test_install_explains_that_it_cannot_help_an_unknown_distribution(monkeypatch):
    use_os_release(monkeypatch, {})

    with pytest.raises(RuntimeError, match="No automatic browser install"):
        install_browser()


def test_removal_explains_that_it_cannot_help_an_unknown_distribution(monkeypatch):
    use_os_release(monkeypatch, {})

    with pytest.raises(RuntimeError, match="No automatic browser removal"):
        remove_browser()


def test_a_successful_install_runs_the_package_manager(monkeypatch):
    use_os_release(monkeypatch, {"ID": "fedora"})
    commands = []

    def fake_run(command, **_options):
        commands.append(command)
        return CompletedCommand(0, stdout="done")

    monkeypatch.setattr("browser_support.subprocess.run", fake_run)

    install_browser()

    assert commands == [["pkexec", "dnf", "install", "-y", "chromium"]]


def test_a_failed_install_reports_what_the_package_manager_printed(monkeypatch):
    use_os_release(monkeypatch, {"ID": "fedora"})

    def fake_run(_command, **_options):
        return CompletedCommand(1, stderr="  not authorised  ")

    monkeypatch.setattr("browser_support.subprocess.run", fake_run)

    with pytest.raises(RuntimeError, match="^not authorised$"):
        install_browser()
