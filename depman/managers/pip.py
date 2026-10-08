"""Globally installed Python packages (system and per-user site-packages)."""

from __future__ import annotations

import json

from depman.core.manager import ManagerError, PackageManager
from depman.core.models import Action, Details, Package

_PYTHON = "python3"
_DISTRO_SCOPE = "distro"
_USER_SCOPE = "user"
_SYSTEM_SCOPE = "system"
# Distribution packages install here; pip run as root uses /usr/local on Debian and Fedora.
_DISTRO_SITES = ("/usr/lib/", "/usr/lib64/")
_PIP_INSTALLER = "pip"
_MAX_FILES = 2000
# Old setuptools writes this literal when a project declares no summary.
_NO_SUMMARY = "UNKNOWN"
# Runs inside the system interpreter so the result does not depend on how DepMan was started.
# With a name argument it prints one distribution in full; without, a brief list of all.
_INSPECT_SCRIPT = """
import importlib.metadata as md, json, sys
sys.path[:] = [p for p in sys.path if p]
wanted = sys.argv[1] if len(sys.argv) > 1 else None
norm = lambda n: n.lower().replace('_', '-').replace('.', '-')
seen, out = set(), []
for dist in md.distributions():
    meta = dist.metadata
    name = meta['Name']
    if not name or norm(name) in seen or (wanted and norm(name) != norm(wanted)):
        continue
    seen.add(norm(name))
    item = {'name': name, 'version': dist.version, 'summary': meta['Summary'] or '',
            'location': str(dist.locate_file('')),
            'installer': (dist.read_text('INSTALLER') or '').strip()}
    if wanted:
        item.update(home=meta['Home-page'] or '', license=meta['License'] or '',
                    author=meta['Author'] or meta['Author-email'] or '',
                    requires_python=meta['Requires-Python'] or '',
                    requires=dist.requires or [],
                    project_urls=meta.get_all('Project-URL') or [],
                    files=[str(dist.locate_file(f)) for f in (dist.files or [])])
    out.append(item)
print(json.dumps(out))
"""


class Pip(PackageManager):
    id = "pip"
    title = "Python"
    icon = "text-x-python-symbolic"
    probe = (_PYTHON, "--version")

    def list_packages(self) -> list[Package]:
        packages = [self._package(item) for item in self._inspect()]
        return sorted(packages, key=lambda package: package.name.lower())

    def details(self, package: Package) -> Details:
        items = self._inspect(package.name)
        if not items:
            raise ManagerError(f"{package.name} is no longer installed.")
        item = items[0]
        rows = [
            ("Installed by", item["installer"] or "unknown"),
            ("Scope", _scope_label(package.scope)),
            ("Author", item["author"]),
            ("License", item["license"]),
            ("Homepage", item["home"] or _first_url(item["project_urls"])),
            ("Requires Python", item["requires_python"]),
            ("Depends on", ", ".join(item["requires"])),
        ]
        return Details(
            package=package,
            fields=tuple((label, value) for label, value in rows if value),
            locations=(item["location"],),
            files=tuple(sorted(item["files"])[:_MAX_FILES]),
            note=_distro_note(package),
        )

    def actions(self, package: Package) -> list[Action]:
        if package.scope == _DISTRO_SCOPE:
            return []
        needs_root = package.scope == _SYSTEM_SCOPE
        pip = (_PYTHON, "-m", "pip")
        user_flag = ("--user",) if package.scope == _USER_SCOPE else ()
        return [
            Action(
                "uninstall",
                "Uninstall",
                (*pip, "uninstall", "-y", "--break-system-packages", package.name),
                "Removes the package from this Python environment.",
                needs_root=needs_root,
                destructive=True,
            ),
            Action(
                "upgrade",
                "Update",
                (*pip, "install", "--upgrade", "--break-system-packages", *user_flag, package.name),
                "Installs the newest version from PyPI.",
                needs_root=needs_root,
            ),
        ]

    def _inspect(self, name: str = "") -> list[dict]:
        argv = (_PYTHON, "-c", _INSPECT_SCRIPT, *((name,) if name else ()))
        return json.loads(self._output(*argv))

    def _package(self, item: dict) -> Package:
        location = item["location"]
        if location.startswith(_DISTRO_SITES) and item["installer"] != _PIP_INSTALLER:
            scope = _DISTRO_SCOPE
        elif self._runner.writable(location):
            scope = _USER_SCOPE
        else:
            scope = _SYSTEM_SCOPE
        summary = "" if item["summary"] == _NO_SUMMARY else item["summary"]
        return Package(self.id, item["name"], item["version"], summary, scope=scope)


def _scope_label(scope: str) -> str:
    return {
        _DISTRO_SCOPE: "System, owned by your distribution's package manager",
        _USER_SCOPE: "Your user account",
        _SYSTEM_SCOPE: "System-wide",
    }[scope]


def _first_url(project_urls: list[str]) -> str:
    return project_urls[0].partition(",")[2].strip() if project_urls else ""


def _distro_note(package: Package) -> str:
    if package.scope != _DISTRO_SCOPE:
        return ""
    return (
        "This Python package was installed by your distribution's package manager. "
        f"Remove it from that manager's tab (usually as python3-{package.name.lower()} "
        f"or python-{package.name.lower()}), not with pip."
    )
