"""Python applications installed with pipx."""

from __future__ import annotations

import json
from posixpath import dirname

from depman.core.manager import ManagerError, PackageManager
from depman.core.models import Action, Details, Package


class Pipx(PackageManager):
    id = "pipx"
    title = "pipx"
    icon = "text-x-python-symbolic"
    probe = ("pipx", "--version")

    def list_packages(self) -> list[Package]:
        packages = []
        for name, venv in self._venvs().items():
            main = venv["metadata"]["main_package"]
            apps = ", ".join(main.get("apps", []))
            summary = f"Provides {apps}" if apps else ""
            packages.append(Package(self.id, name, main.get("package_version", ""), summary))
        return sorted(packages, key=lambda package: package.name.lower())

    def details(self, package: Package) -> Details:
        venv = self._venvs().get(package.name)
        if venv is None:
            raise ManagerError(f"{package.name} is no longer installed.")
        metadata = venv["metadata"]
        main = metadata["main_package"]
        app_paths = tuple(path["__Path__"] for path in main.get("app_paths", []))
        venvs_dir = self._output("pipx", "environment", "--value", "PIPX_LOCAL_VENVS").strip()
        rows = [
            ("Python", metadata.get("python_version", "")),
            ("Installed from", main.get("package_or_url", "")),
            ("Commands", ", ".join(main.get("apps", []))),
            ("Injected packages", ", ".join(metadata.get("injected_packages", {}))),
        ]
        locations = [f"{venvs_dir}/{package.name}"]
        locations += sorted({dirname(path) for path in app_paths})
        return Details(
            package=package,
            fields=tuple((label, value) for label, value in rows if value),
            locations=tuple(locations),
            files=app_paths,
        )

    def actions(self, package: Package) -> list[Action]:
        name = package.name
        return [
            Action(
                "uninstall",
                "Uninstall",
                ("pipx", "uninstall", name),
                "Removes the application and its private environment.",
                destructive=True,
            ),
            Action("upgrade", "Update", ("pipx", "upgrade", name), "Installs the newest version."),
            Action(
                "reinstall",
                "Reinstall",
                ("pipx", "reinstall", name),
                "Rebuilds the application's private environment.",
            ),
        ]

    def _venvs(self) -> dict[str, dict]:
        return json.loads(self._output("pipx", "list", "--json")).get("venvs", {})
