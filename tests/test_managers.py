"""Every manager, driven through its interface with recorded command output."""

from __future__ import annotations

import pytest

from depman.core.manager import ManagerError
from depman.core.models import format_size
from depman.core.registry import detect_managers
from depman.managers.apt import Apt
from depman.managers.cargo import Cargo
from depman.managers.flatpak import Flatpak
from depman.managers.npm import Npm
from depman.managers.pip import Pip
from depman.managers.pipx import Pipx
from depman.managers.snap import Snap
from tests.fake_runner import FAKE_HOME, FakeRunner, demo_runner
from tests.lookup import action, find


def test_detects_only_working_managers():
    runner = FakeRunner({"snap version": "snap 2.77", "cargo --version": "cargo 1.81"})
    assert [manager.id for manager in detect_managers(runner)] == ["snap", "cargo"]


def test_detection_rejects_a_binary_whose_probe_fails():
    # Like Windows npm leaking into WSL's PATH without node: found, but it cannot run.
    runner = FakeRunner(binaries=["npm"])
    assert detect_managers(runner) == []


def test_all_managers_detected_on_demo_system():
    ids = [manager.id for manager in detect_managers(demo_runner())]
    assert ids == ["apt", "snap", "flatpak", "pip", "pipx", "npm", "cargo"]


def test_failed_command_becomes_manager_error():
    with pytest.raises(ManagerError, match="command not found"):
        Snap(FakeRunner()).list_packages()


class TestApt:
    manager = Apt(demo_runner())

    def test_lists_installed_packages_only(self):
        names = [package.name for package in self.manager.list_packages()]
        assert "bash" in names
        assert "libc6:amd64" in names
        assert "oldpkg" not in names  # removed, config files remain

    def test_list_carries_version_and_summary(self):
        bash = find(self.manager, "bash")
        assert bash.version == "5.2.21-2ubuntu4"
        assert bash.summary == "GNU Bourne Again SHell"

    def test_details(self):
        details = self.manager.details(find(self.manager, "bash"))
        fields = dict(details.fields)
        assert fields["Installed size"] == "1.9 MB"
        assert fields["Installed"] == "Manually"
        assert fields["Homepage"].startswith("http")
        assert "/usr/bin/bash" in details.files
        assert "/usr/bin" not in details.files  # directories are not files
        assert "/usr/bin" in details.locations
        assert "required by the system" in details.note
        assert details.description
        assert not details.description.startswith("GNU Bourne Again SHell")

    def test_actions_need_root_and_preview_removal(self):
        bash = find(self.manager, "bash")
        purge = action(self.manager, bash, "purge")
        assert purge.argv == ("apt-get", "purge", "-y", "bash")
        assert purge.needs_root
        assert purge.destructive
        assert purge.preview_argv == ("apt-get", "-s", "purge", "bash")
        assert self.manager.actions(bash)[0].id == "remove"


class TestSnap:
    manager = Snap(demo_runner())

    def test_list(self):
        nmap = find(self.manager, "nmap")
        assert nmap.version == "7.95"
        assert "maxiberta" in nmap.summary
        assert find(self.manager, "core24").scope == "base"

    def test_details(self):
        details = self.manager.details(find(self.manager, "nmap"))
        fields = dict(details.fields)
        assert details.package.summary.endswith("security auditing")  # wrapped line joined
        assert fields["License"] == "GPL-2.0"
        assert fields["Installed"] == "7.95 (5184) 12.9MB -"
        assert details.description.startswith("Nmap is a utility")
        assert "/snap/nmap/current" in details.locations
        assert f"{FAKE_HOME}/snap/nmap" in details.locations
        assert "/snap/bin/nmap.ncat" in details.files

    def test_purge_action(self):
        purge = action(self.manager, find(self.manager, "nmap"), "purge")
        assert purge.argv == ("snap", "remove", "--purge", "nmap")
        assert purge.needs_root


class TestFlatpak:
    manager = Flatpak(demo_runner())

    def test_list_uses_human_name_and_falls_back_to_branch(self):
        firefox = find(self.manager, "org.mozilla.firefox")
        assert firefox.title == "Firefox"
        assert firefox.scope == "system"
        assert find(self.manager, "org.gnome.Platform").version == "46"

    def test_details(self):
        details = self.manager.details(find(self.manager, "org.mozilla.firefox"))
        fields = dict(details.fields)
        assert fields["Origin"] == "flathub"
        assert fields["Installed"] == "367.6 MB"
        assert "ID" not in fields
        assert details.locations == (
            "/var/lib/flatpak/app/org.mozilla.firefox",
            f"{FAKE_HOME}/.var/app/org.mozilla.firefox",
        )

    def test_actions_target_the_right_installation(self):
        spotify = find(self.manager, "com.spotify.Client")
        purge = action(self.manager, spotify, "purge")
        assert purge.argv == (
            "flatpak",
            "uninstall",
            "-y",
            "--delete-data",
            "--user",
            "app/com.spotify.Client/x86_64/stable",
        )
        assert not purge.needs_root


class TestPip:
    manager = Pip(demo_runner())

    def test_scopes(self):
        assert find(self.manager, "PyGObject").scope == "distro"
        assert find(self.manager, "dnf").scope == "distro"  # Fedora: /usr/lib64/.../site-packages
        assert find(self.manager, "requests").scope == "user"
        assert find(self.manager, "ansible").scope == "system"

    def test_distro_owned_package_has_no_actions(self):
        pygobject = find(self.manager, "PyGObject")
        assert self.manager.actions(pygobject) == []

    def test_user_package_actions(self):
        requests = find(self.manager, "requests")
        uninstall = action(self.manager, requests, "uninstall")
        assert uninstall.argv[:5] == ("python3", "-m", "pip", "uninstall", "-y")
        assert uninstall.argv[-1] == "requests"
        assert not uninstall.needs_root
        assert "--user" in action(self.manager, requests, "upgrade").argv

    def test_system_package_needs_root(self):
        ansible = find(self.manager, "ansible")
        assert action(self.manager, ansible, "uninstall").needs_root
        assert "--user" not in action(self.manager, ansible, "upgrade").argv

    def test_details(self):
        details = self.manager.details(find(self.manager, "requests"))
        fields = dict(details.fields)
        assert fields["Homepage"] == "https://requests.readthedocs.io"
        assert fields["Scope"] == "Your user account"
        assert details.locations == (f"{FAKE_HOME}/.local/lib/python3.12/site-packages",)
        assert details.files[0].endswith("requests/__init__.py")


class TestPipx:
    manager = Pipx(demo_runner())

    def test_list(self):
        black = find(self.manager, "black")
        assert black.version == "24.8.0"
        assert black.summary == "Provides black, blackd"

    def test_details(self):
        details = self.manager.details(find(self.manager, "httpie"))
        assert dict(details.fields)["Injected packages"] == "httpie-jwt-auth"
        assert details.locations[0] == f"{FAKE_HOME}/.local/share/pipx/venvs/httpie"
        assert details.files == (f"{FAKE_HOME}/.local/share/pipx/venvs/httpie/bin/http",)

    def test_uninstall(self):
        black = find(self.manager, "black")
        assert action(self.manager, black, "uninstall").argv == ("pipx", "uninstall", "black")


class TestNpm:
    manager = Npm(demo_runner())

    def test_list_and_scope(self):
        assert find(self.manager, "typescript").version == "5.6.2"
        assert find(self.manager, "typescript").scope == "user"
        assert find(self.manager, "npm").scope == "system"

    def test_details(self):
        details = self.manager.details(find(self.manager, "npm"))
        fields = dict(details.fields)
        assert fields["Author"] == "GitHub Inc."
        assert fields["Repository"] == "git+https://github.com/npm/cli.git"
        assert fields["Commands"] == "npm, npx"
        assert details.locations[0] == "/usr/lib/node_modules/npm"
        assert f"{FAKE_HOME}/.npm-global/bin/npx" in details.files

    def test_system_wide_uninstall_needs_root(self):
        uninstall = action(self.manager, find(self.manager, "npm"), "uninstall")
        assert uninstall.argv == ("npm", "uninstall", "-g", "npm")
        assert uninstall.needs_root
        scoped = find(self.manager, "@angular/cli")
        assert not action(self.manager, scoped, "uninstall").needs_root


class TestCargo:
    manager = Cargo(demo_runner())

    def test_list(self):
        assert find(self.manager, "ripgrep").version == "14.1.0"
        assert find(self.manager, "cargo-edit").summary.startswith("Provides cargo-add")

    def test_details(self):
        details = self.manager.details(find(self.manager, "ripgrep"))
        assert details.files == (f"{FAKE_HOME}/.cargo/bin/rg",)
        assert dict(details.fields)["Installed from"] == "crates.io"

    def test_only_registry_crates_can_be_updated(self):
        ripgrep = find(self.manager, "ripgrep")
        local = find(self.manager, "mytool")
        assert [item.id for item in self.manager.actions(ripgrep)] == ["uninstall", "update"]
        assert [item.id for item in self.manager.actions(local)] == ["uninstall"]


@pytest.mark.parametrize(
    ("size", "text"),
    [
        (0, "0 B"),
        (900, "900 B"),
        (2048, "2.0 kB"),
        (1900 * 1024, "1.9 MB"),
        (3 * 1024**3, "3.0 GB"),
    ],
)
def test_format_size(size, text):
    assert format_size(size) == text
