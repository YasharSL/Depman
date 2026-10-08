"""RPM-based systems: DNF (Fedora, RHEL, ...) and Zypper (openSUSE).

Both read the same RPM database; they differ only in the commands that change it.
"""

from __future__ import annotations

from depman.core.manager import PackageManager, busiest_directories, leaf_paths
from depman.core.models import Action, Details, Package, format_size

_LIST_FORMAT = "%{NAME}\\t%{EVR}\\t%{NEVRA}\\t%{SUMMARY}\\n"
_FIELD_SEPARATOR = "\x1f"
_DETAIL_TAGS = (
    "ARCH",
    "SIZE",
    "LICENSE",
    "URL",
    "VENDOR",
    "GROUP",
    "SOURCERPM",
    "INSTALLTIME:date",
    "DESCRIPTION",
)
_DETAIL_FORMAT = _FIELD_SEPARATOR.join(f"%{{{tag}}}" for tag in _DETAIL_TAGS)
_MISSING = "(none)"
# Imported signing keys live in the RPM database but are not software.
_KEY_PACKAGE = "gpg-pubkey"
_LIST_COLUMNS = 4


class _RpmManager(PackageManager):
    """Listing and details from the RPM database, shared by every RPM front end."""

    icon = "system-software-install-symbolic"

    def list_packages(self) -> list[Package]:
        output = self._output("rpm", "-qa", "--qf", _LIST_FORMAT)
        packages = []
        for line in output.splitlines():
            columns = line.split("\t")
            if len(columns) < _LIST_COLUMNS or columns[0] == _KEY_PACKAGE:
                continue
            name, version, nevra, summary = columns[:_LIST_COLUMNS]
            packages.append(Package(self.id, name, version, summary, ref=nevra))
        return sorted(packages, key=lambda package: (package.name, package.version))

    def details(self, package: Package) -> Details:
        raw = self._output("rpm", "-q", "--qf", _DETAIL_FORMAT, package.ref)
        values = dict(zip(_DETAIL_TAGS, raw.split(_FIELD_SEPARATOR), strict=False))
        values = {tag: value for tag, value in values.items() if value != _MISSING}
        files = leaf_paths(self._output("rpm", "-ql", package.ref).splitlines())
        size = values.get("SIZE", "")
        rows = [
            ("Installed size", format_size(int(size)) if size.isdigit() else ""),
            ("Architecture", values.get("ARCH", "")),
            ("Install date", values.get("INSTALLTIME:date", "")),
            ("License", values.get("LICENSE", "")),
            ("Homepage", values.get("URL", "")),
            ("Vendor", values.get("VENDOR", "")),
            ("Group", values.get("GROUP", "")),
            ("Source package", values.get("SOURCERPM", "")),
            ("Full name", package.ref),
        ]
        return Details(
            package=package,
            fields=tuple((label, value) for label, value in rows if value),
            description=_reflow(values.get("DESCRIPTION", "")),
            locations=busiest_directories(files),
            files=files,
        )


class Dnf(_RpmManager):
    id = "dnf"
    title = "DNF"
    probe = ("dnf", "--version")

    def actions(self, package: Package) -> list[Action]:
        return [
            Action(
                "remove",
                "Uninstall",
                ("dnf", "remove", "-y", package.ref),
                "Removes the package and the dependencies nothing else needs.",
                needs_root=True,
                destructive=True,
            ),
            Action(
                "upgrade",
                "Update",
                ("dnf", "upgrade", "-y", package.name),
                "Installs the newest version available from your repositories.",
                needs_root=True,
            ),
            Action(
                "reinstall",
                "Reinstall",
                ("dnf", "reinstall", "-y", package.ref),
                "Downloads the package again and restores its files.",
                needs_root=True,
            ),
        ]


class Zypper(_RpmManager):
    id = "zypper"
    title = "Zypper"
    probe = ("zypper", "--version")

    def actions(self, package: Package) -> list[Action]:
        zypper = ("zypper", "--non-interactive")
        return [
            Action(
                "remove",
                "Uninstall",
                (*zypper, "remove", package.name),
                "Removes the package but keeps the dependencies it pulled in.",
                needs_root=True,
                destructive=True,
            ),
            Action(
                "purge",
                "Purge",
                (*zypper, "remove", "--clean-deps", package.name),
                "Removes the package and the dependencies nothing else needs.",
                needs_root=True,
                destructive=True,
            ),
            Action(
                "update",
                "Update",
                (*zypper, "update", package.name),
                "Installs the newest version available from your repositories.",
                needs_root=True,
            ),
            Action(
                "reinstall",
                "Reinstall",
                (*zypper, "install", "--force", package.name),
                "Downloads the package again and restores its files.",
                needs_root=True,
            ),
        ]


def _reflow(description: str) -> str:
    """Join an RPM description's hard-wrapped lines, keeping blank-line paragraph breaks."""
    paragraphs = description.strip().split("\n\n")
    return "\n\n".join(" ".join(paragraph.split()) for paragraph in paragraphs)
