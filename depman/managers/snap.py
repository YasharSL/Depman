"""Snap packages."""

from __future__ import annotations

from depman.core.manager import PackageManager, key_value_lines
from depman.core.models import Action, Details, Package

_LIST_COLUMNS = 6
_INFO_FIELDS = (
    ("Publisher", "publisher"),
    ("Installed", "installed"),
    ("Channel", "tracking"),
    ("Last refreshed", "refresh-date"),
    ("License", "license"),
    ("Store page", "store-url"),
    ("Contact", "contact"),
    ("Snap ID", "snap-id"),
)


class Snap(PackageManager):
    id = "snap"
    title = "Snap"
    icon = "application-x-addon-symbolic"
    probe = ("snap", "version")

    def list_packages(self) -> list[Package]:
        rows = self._output("snap", "list").splitlines()[1:]
        packages = []
        for row in rows:
            columns = row.split()
            if len(columns) < _LIST_COLUMNS:
                continue
            name, version, _revision, tracking, publisher, notes = columns[:_LIST_COLUMNS]
            summary = f"Published by {publisher.rstrip('*')} · {tracking}"
            packages.append(Package(self.id, name, version, summary, scope=notes.strip("-")))
        return sorted(packages, key=lambda package: package.name)

    def details(self, package: Package) -> Details:
        info = self._output("snap", "info", package.name)
        values = key_value_lines(info)
        fields = tuple(
            (label, " ".join(values[key].split())) for label, key in _INFO_FIELDS if key in values
        )
        summary = " ".join(_block(info, "summary").split()) or package.summary
        return Details(
            package=Package(self.id, package.name, package.version, summary, scope=package.scope),
            fields=fields,
            description=_block(info, "description"),
            locations=(
                f"/snap/{package.name}/current",
                f"/var/snap/{package.name}",
                self._runner.expand(f"~/snap/{package.name}"),
            ),
            files=tuple(f"/snap/bin/{command}" for command in _commands(info)),
        )

    def actions(self, package: Package) -> list[Action]:
        name = package.name
        return [
            Action(
                "remove",
                "Uninstall",
                ("snap", "remove", name),
                "Removes the snap. A snapshot of its data is kept for a while.",
                needs_root=True,
                destructive=True,
            ),
            Action(
                "purge",
                "Purge",
                ("snap", "remove", "--purge", name),
                "Removes the snap and all of its data, without keeping a snapshot.",
                needs_root=True,
                destructive=True,
            ),
            Action(
                "refresh",
                "Update",
                ("snap", "refresh", name),
                "Updates the snap to the newest revision in its channel.",
                needs_root=True,
            ),
        ]


def _block(info: str, key: str) -> str:
    """Return a key's value from snap info output, including its indented continuation lines."""
    lines = info.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            first = line.partition(":")[2].strip()
            body = [] if first in ("", "|") else [first]
            for following in lines[index + 1 :]:
                if following and not following.startswith(" "):
                    break
                body.append(following.strip())
            return "\n".join(body).strip()
    return ""


def _commands(info: str) -> list[str]:
    return [line.removeprefix("- ") for line in _block(info, "commands").splitlines()]
