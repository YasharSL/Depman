"""Pacman: Arch Linux and its derivatives (Manjaro, EndeavourOS, ...)."""

from __future__ import annotations

from depman.core.manager import PackageManager, busiest_directories, key_value_lines, leaf_paths
from depman.core.models import Action, Details, Package

_FOREIGN_SCOPE = "foreign"
_EMPTY_VALUE = "None"
_DETAIL_FIELDS = (
    ("Installed size", "Installed Size"),
    ("Architecture", "Architecture"),
    ("Installed", "Install Reason"),
    ("Install date", "Install Date"),
    ("Licenses", "Licenses"),
    ("Homepage", "URL"),
    ("Groups", "Groups"),
    ("Packager", "Packager"),
    ("Depends on", "Depends On"),
    ("Required by", "Required By"),
)


class Pacman(PackageManager):
    id = "pacman"
    title = "Pacman"
    icon = "system-software-install-symbolic"
    probe = ("pacman", "--version")

    def list_packages(self) -> list[Package]:
        # Foreign packages come from the AUR or a local build; the command fails when none exist.
        foreign = set(self._runner.run(("pacman", "-Qmq")).stdout.split())
        packages = []
        for block in self._output("pacman", "-Qi").split("\n\n"):
            values = key_value_lines(block)
            if "Name" in values:
                name = values["Name"]
                scope = _FOREIGN_SCOPE if name in foreign else ""
                packages.append(
                    Package(
                        self.id,
                        name,
                        values.get("Version", ""),
                        values.get("Description", ""),
                        scope=scope,
                    )
                )
        return sorted(packages, key=lambda package: package.name)

    def details(self, package: Package) -> Details:
        values = key_value_lines(self._output("pacman", "-Qi", package.name))
        files = leaf_paths(self._output("pacman", "-Qlq", package.name).splitlines())
        fields = tuple(
            (label, " ".join(values[key].split()))
            for label, key in _DETAIL_FIELDS
            if values.get(key, _EMPTY_VALUE) != _EMPTY_VALUE
        )
        return Details(
            package=package,
            fields=fields,
            locations=busiest_directories(files),
            files=files,
            note=_foreign_note(package),
        )

    def actions(self, package: Package) -> list[Action]:
        name = package.name
        actions = [
            Action(
                "remove",
                "Uninstall",
                ("pacman", "-R", "--noconfirm", name),
                "Removes the package but keeps its configuration backups and dependencies.",
                needs_root=True,
                destructive=True,
                preview_argv=("pacman", "-R", "--print", name),
            ),
            Action(
                "purge",
                "Purge",
                ("pacman", "-Rns", "--noconfirm", name),
                "Removes the package, its configuration files and the dependencies "
                "nothing else needs.",
                needs_root=True,
                destructive=True,
                # --print cannot be combined with -n, so the preview shows the -s part.
                preview_argv=("pacman", "-Rs", "--print", name),
            ),
        ]
        if package.scope != _FOREIGN_SCOPE:
            actions.append(
                Action(
                    "reinstall",
                    "Reinstall",
                    ("pacman", "-S", "--noconfirm", name),
                    "Installs the version from your synced package database again.",
                    needs_root=True,
                )
            )
        return actions


def _foreign_note(package: Package) -> str:
    if package.scope != _FOREIGN_SCOPE:
        return ""
    return (
        "This package is not in your pacman repositories. It was installed from the AUR "
        "or built locally, so pacman cannot reinstall or update it."
    )
