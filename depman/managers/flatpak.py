"""Flatpak applications and runtimes."""

from __future__ import annotations

from depman.core.manager import PackageManager, key_value_lines
from depman.core.models import Action, Details, Package

_COLUMNS = "application,name,version,branch,installation,ref,description"
_COLUMN_COUNT = 7
_SCOPE_FLAGS = {"user": "--user", "system": "--system"}
_SKIPPED_INFO_KEYS = {"ID", "Version"}


class Flatpak(PackageManager):
    id = "flatpak"
    title = "Flatpak"
    icon = "application-x-executable-symbolic"
    probe = ("flatpak", "--version")

    def list_packages(self) -> list[Package]:
        output = self._output("flatpak", "list", f"--columns={_COLUMNS}")
        packages = []
        for line in output.splitlines():
            columns = line.split("\t")
            if len(columns) < _COLUMN_COUNT:
                continue
            app_id, name, version, branch, installation, ref, description = columns[:_COLUMN_COUNT]
            packages.append(
                Package(
                    self.id,
                    app_id,
                    version or branch,
                    description,
                    display_name=name,
                    scope=installation,
                    ref=ref,
                )
            )
        return sorted(packages, key=lambda package: package.title.lower())

    def details(self, package: Package) -> Details:
        scope = _scope_flag(package)
        values = key_value_lines(self._output("flatpak", "info", scope, package.ref))
        location = self._output("flatpak", "info", "--show-location", scope, package.ref).strip()
        fields = tuple(
            (key, value) for key, value in values.items() if key not in _SKIPPED_INFO_KEYS
        )
        return Details(
            package=package,
            fields=fields,
            locations=(location, self._runner.expand(f"~/.var/app/{package.name}")),
        )

    def actions(self, package: Package) -> list[Action]:
        scope = _scope_flag(package)
        return [
            Action(
                "uninstall",
                "Uninstall",
                ("flatpak", "uninstall", "-y", scope, package.ref),
                "Removes the application but keeps your data in ~/.var/app.",
                destructive=True,
            ),
            Action(
                "purge",
                "Purge",
                ("flatpak", "uninstall", "-y", "--delete-data", scope, package.ref),
                "Removes the application and deletes its data in ~/.var/app.",
                destructive=True,
            ),
            Action(
                "update",
                "Update",
                ("flatpak", "update", "-y", scope, package.ref),
                "Updates to the newest version from its remote.",
            ),
        ]


def _scope_flag(package: Package) -> str:
    return _SCOPE_FLAGS.get(package.scope, f"--installation={package.scope}")
