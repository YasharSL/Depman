"""Rust binaries installed with `cargo install`."""

from __future__ import annotations

import re

from depman.core.manager import ManagerError, PackageManager
from depman.core.models import Action, Details, Package

# A crate line names the crate, its version and, for local or git installs, the source.
_CRATE_LINE = re.compile(r"^(?P<name>\S+) v(?P<version>\S+?)(?: \((?P<source>.+)\))?:$")
_BIN_DIR = "~/.cargo/bin"
_REGISTRY_SOURCE = "crates.io"


class Cargo(PackageManager):
    id = "cargo"
    title = "Rust"
    icon = "applications-engineering-symbolic"
    probe = ("cargo", "--version")

    def list_packages(self) -> list[Package]:
        packages = []
        for name, (version, source, binaries) in self._crates().items():
            summary = f"Provides {', '.join(binaries)}" if binaries else ""
            packages.append(Package(self.id, name, version, summary, ref=source))
        return sorted(packages, key=lambda package: package.name.lower())

    def details(self, package: Package) -> Details:
        crate = self._crates().get(package.name)
        if crate is None:
            raise ManagerError(f"{package.name} is no longer installed.")
        _version, source, binaries = crate
        bin_dir = self._runner.expand(_BIN_DIR)
        return Details(
            package=package,
            fields=(
                ("Installed from", source),
                ("Commands", ", ".join(binaries)),
                ("Crate page", f"https://crates.io/crates/{package.name}"),
            ),
            locations=(bin_dir,),
            files=tuple(f"{bin_dir}/{binary}" for binary in binaries),
        )

    def actions(self, package: Package) -> list[Action]:
        actions = [
            Action(
                "uninstall",
                "Uninstall",
                ("cargo", "uninstall", package.name),
                "Removes the crate's binaries from ~/.cargo/bin.",
                destructive=True,
            )
        ]
        if package.ref == _REGISTRY_SOURCE:
            actions.append(
                Action(
                    "update",
                    "Update",
                    ("cargo", "install", "--force", package.name),
                    "Downloads and compiles the newest version. This can take several minutes.",
                )
            )
        return actions

    def _crates(self) -> dict[str, tuple[str, str, list[str]]]:
        """Map crate name to (version, source, binaries) from `cargo install --list`."""
        crates: dict[str, tuple[str, str, list[str]]] = {}
        binaries: list[str] = []
        for line in self._output("cargo", "install", "--list").splitlines():
            match = _CRATE_LINE.match(line)
            if match:
                binaries = []
                source = match["source"] or _REGISTRY_SOURCE
                crates[match["name"]] = (match["version"], source, binaries)
            elif line.strip():
                binaries.append(line.strip())
        return crates
