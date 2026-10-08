"""APT / dpkg: Debian and Ubuntu system packages."""

from __future__ import annotations

from depman.core.manager import PackageManager, busiest_directories, leaf_paths
from depman.core.models import Action, Details, Package, format_size

_INSTALLED_STATUS = "ii"
_LIST_FORMAT = "${binary:Package}\t${Version}\t${db:Status-Abbrev}\t${binary:Summary}\n"
_FIELD_SEPARATOR = "\x1f"
_DETAIL_FIELDS = (
    "Architecture",
    "Section",
    "Priority",
    "Essential",
    "Installed-Size",
    "Maintainer",
    "Homepage",
    "Source",
    "Depends",
    "Description",
)
_DETAIL_FORMAT = _FIELD_SEPARATOR.join(f"${{{field}}}" for field in _DETAIL_FIELDS)
_KIB = 1024


class Apt(PackageManager):
    id = "apt"
    title = "APT"
    icon = "system-software-install-symbolic"
    probe = ("dpkg-query", "--version")

    def list_packages(self) -> list[Package]:
        output = self._output("dpkg-query", "-W", f"-f={_LIST_FORMAT}")
        packages = []
        for line in output.splitlines():
            name, version, status, summary = (line.split("\t") + ["", "", ""])[:4]
            if status.startswith(_INSTALLED_STATUS):
                packages.append(Package(self.id, name, version, summary))
        return sorted(packages, key=lambda package: package.name)

    def details(self, package: Package) -> Details:
        raw = self._output("dpkg-query", "-W", f"-f={_DETAIL_FORMAT}", package.name)
        values = dict(zip(_DETAIL_FIELDS, raw.split(_FIELD_SEPARATOR), strict=False))
        files = leaf_paths(self._output("dpkg-query", "-L", package.name).splitlines())
        manual = self._runner.run(("apt-mark", "showmanual", package.name)).stdout.strip()
        return Details(
            package=package,
            fields=_fields(values, manually_installed=bool(manual)),
            description=_description_body(values.get("Description", "")),
            locations=busiest_directories(files),
            files=files,
            note=_essential_note(values),
        )

    def actions(self, package: Package) -> list[Action]:
        name = package.name
        return [
            Action(
                "remove",
                "Uninstall",
                ("apt-get", "remove", "-y", name),
                "Removes the package but keeps its system configuration files.",
                needs_root=True,
                destructive=True,
                preview_argv=("apt-get", "-s", "remove", name),
            ),
            Action(
                "purge",
                "Purge",
                ("apt-get", "purge", "-y", name),
                "Removes the package together with its system configuration files.",
                needs_root=True,
                destructive=True,
                preview_argv=("apt-get", "-s", "purge", name),
            ),
            Action(
                "upgrade",
                "Update",
                ("apt-get", "install", "--only-upgrade", "-y", name),
                "Installs the newest version available from your software sources.",
                needs_root=True,
            ),
            Action(
                "reinstall",
                "Reinstall",
                ("apt-get", "install", "--reinstall", "-y", name),
                "Downloads the package again and restores its files.",
                needs_root=True,
            ),
        ]


def _fields(values: dict[str, str], manually_installed: bool) -> tuple[tuple[str, str], ...]:
    size_kib = values.get("Installed-Size", "")
    rows = [
        ("Installed size", format_size(int(size_kib) * _KIB) if size_kib.isdigit() else ""),
        ("Architecture", values.get("Architecture", "")),
        ("Section", values.get("Section", "")),
        ("Priority", values.get("Priority", "")),
        ("Installed", "Manually" if manually_installed else "Automatically, as a dependency"),
        ("Source package", values.get("Source", "")),
        ("Maintainer", values.get("Maintainer", "")),
        ("Homepage", values.get("Homepage", "")),
        ("Depends on", values.get("Depends", "")),
    ]
    return tuple((label, value) for label, value in rows if value)


def _description_body(description: str) -> str:
    """Drop the synopsis line and re-flow dpkg's hard-wrapped paragraphs."""
    lines = [line.strip() for line in description.splitlines()[1:]]
    paragraphs = "\n".join(lines).split("\n.\n")
    return "\n\n".join(" ".join(paragraph.split()) for paragraph in paragraphs).strip()


def _essential_note(values: dict[str, str]) -> str:
    if values.get("Essential") == "yes" or values.get("Priority") == "required":
        return "This package is required by the system. Removing it can break your installation."
    return ""
