"""Distribution package managers, driven by output captured in real containers."""

from __future__ import annotations

from depman.core.registry import detect_managers
from depman.managers.pacman import Pacman
from depman.managers.rpm import Dnf, Zypper
from tests.fake_runner import arch_runner, fedora_runner
from tests.lookup import action, find


class TestPacman:
    manager = Pacman(arch_runner())

    def test_list_marks_foreign_packages(self):
        bash = find(self.manager, "bash")
        assert bash.summary == "The GNU Bourne Again shell"
        assert bash.scope == ""
        assert find(self.manager, "pacman").scope == "foreign"
        assert len(self.manager.list_packages()) == 3

    def test_details(self):
        details = self.manager.details(find(self.manager, "bash"))
        fields = dict(details.fields)
        assert fields["Installed size"].endswith("MiB")
        assert fields["Homepage"] == "https://www.gnu.org/software/bash/bash.html"
        assert "Groups" not in fields  # "None" values are dropped
        assert "/etc/bash.bashrc" in details.files
        assert "/etc" not in details.files
        assert details.locations

    def test_actions(self):
        bash = find(self.manager, "bash")
        purge = action(self.manager, bash, "purge")
        assert purge.argv == ("pacman", "-Rns", "--noconfirm", "bash")
        assert purge.needs_root
        assert purge.preview_argv == ("pacman", "-Rs", "--print", "bash")
        assert [item.id for item in self.manager.actions(bash)] == ["remove", "purge", "reinstall"]

    def test_foreign_package_cannot_be_reinstalled(self):
        foreign = find(self.manager, "pacman")
        assert [item.id for item in self.manager.actions(foreign)] == ["remove", "purge"]
        assert "AUR" in self.manager.details(find(self.manager, "pacman")).note


class TestRpm:
    manager = Dnf(fedora_runner())

    def test_list_skips_signing_keys(self):
        names = [package.name for package in self.manager.list_packages()]
        assert "bash" in names
        assert "gpg-pubkey" not in names

    def test_details(self):
        bash = find(self.manager, "bash")
        details = self.manager.details(bash)
        fields = dict(details.fields)
        assert fields["Architecture"] == "x86_64"
        assert fields["Installed size"].endswith("MB")
        assert fields["Full name"] == bash.ref
        assert details.description.startswith("The GNU Bourne Again shell")
        assert "\n" not in details.description.split("\n\n")[0]
        assert "/usr/bin/bash" in details.files
        assert "/usr/bin" in details.locations

    def test_dnf_actions_use_the_exact_installed_build(self):
        bash = find(self.manager, "bash")
        assert action(self.manager, bash, "remove").argv == ("dnf", "remove", "-y", bash.ref)
        assert action(self.manager, bash, "upgrade").argv == ("dnf", "upgrade", "-y", "bash")

    def test_zypper_shares_the_database_but_has_its_own_actions(self):
        zypper = Zypper(fedora_runner("zypper"))
        bash = find(zypper, "bash")
        purge = action(zypper, bash, "purge")
        assert purge.argv == ("zypper", "--non-interactive", "remove", "--clean-deps", "bash")
        assert [manager.id for manager in detect_managers(fedora_runner("zypper"))] == ["zypper"]
