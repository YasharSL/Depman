"""Globally installed Node.js packages (npm -g)."""

from __future__ import annotations

import json

from depman.core.manager import ManagerError, PackageManager
from depman.core.models import Action, Details, Package

_USER_SCOPE = "user"
_SYSTEM_SCOPE = "system"


class Npm(PackageManager):
    id = "npm"
    title = "Node.js"
    icon = "text-x-script-symbolic"
    probe = ("npm", "--version")

    def list_packages(self) -> list[Package]:
        packages = []
        for name, info in self._globals().items():
            scope = _USER_SCOPE if self._runner.writable(info.get("path", "")) else _SYSTEM_SCOPE
            packages.append(
                Package(
                    self.id, name, info.get("version", ""), info.get("description", ""), scope=scope
                )
            )
        return sorted(packages, key=lambda package: package.name.lower())

    def details(self, package: Package) -> Details:
        info = self._globals().get(package.name)
        if info is None:
            raise ManagerError(f"{package.name} is no longer installed.")
        commands = _commands(package.name, info.get("bin"))
        bin_dir = self._output("npm", "prefix", "-g").strip() + "/bin"
        rows = [
            ("License", _text(info.get("license"))),
            ("Author", _text(info.get("author"))),
            ("Homepage", _text(info.get("homepage"))),
            ("Repository", _text(info.get("repository"))),
            ("Commands", ", ".join(commands)),
            ("Depends on", ", ".join(info.get("dependencies", {}))),
        ]
        return Details(
            package=package,
            fields=tuple((label, value) for label, value in rows if value),
            locations=(info.get("path", ""), bin_dir),
            files=tuple(f"{bin_dir}/{command}" for command in commands),
        )

    def actions(self, package: Package) -> list[Action]:
        needs_root = package.scope == _SYSTEM_SCOPE
        return [
            Action(
                "uninstall",
                "Uninstall",
                ("npm", "uninstall", "-g", package.name),
                "Removes the package from the global node_modules folder.",
                needs_root=needs_root,
                destructive=True,
            ),
            Action(
                "update",
                "Update",
                ("npm", "install", "-g", f"{package.name}@latest"),
                "Installs the newest version from the npm registry.",
                needs_root=needs_root,
            ),
        ]

    def _globals(self) -> dict[str, dict]:
        output = self._output("npm", "ls", "-g", "--depth=0", "--json", "--long")
        return json.loads(output).get("dependencies", {})


def _text(value: object) -> str:
    """npm metadata fields are either a string or an object with a name/url/type."""
    if isinstance(value, dict):
        return str(value.get("url") or value.get("name") or value.get("type") or "")
    return str(value or "")


def _commands(name: str, bins: object) -> list[str]:
    if isinstance(bins, dict):
        return sorted(bins)
    return [name.rpartition("/")[2]] if bins else []
