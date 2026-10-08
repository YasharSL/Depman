"""Value objects shared by every manager and the UI."""

from __future__ import annotations

from dataclasses import dataclass

_SIZE_STEP = 1024
_SIZE_UNITS = ("B", "kB", "MB", "GB", "TB")


@dataclass(frozen=True)
class Package:
    """One installed package as shown in a manager's list."""

    manager_id: str
    name: str
    version: str
    summary: str = ""
    display_name: str = ""
    scope: str = ""
    # Manager-specific handle used in commands when the name is not enough.
    ref: str = ""

    @property
    def title(self) -> str:
        return self.display_name or self.name


@dataclass(frozen=True)
class Details:
    """Everything shown on a package's own page."""

    package: Package
    fields: tuple[tuple[str, str], ...] = ()
    description: str = ""
    locations: tuple[str, ...] = ()
    files: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class Action:
    """One command the user can run on a package after confirming it."""

    id: str
    label: str
    argv: tuple[str, ...]
    description: str = ""
    needs_root: bool = False
    destructive: bool = False
    # Read-only command whose output shows what the action would do.
    preview_argv: tuple[str, ...] = ()


def format_size(size_bytes: float) -> str:
    """Render a byte count the way software centres do: 1.4 MB, 12 kB."""
    value = float(size_bytes)
    for unit in _SIZE_UNITS[:-1]:
        if value < _SIZE_STEP:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= _SIZE_STEP
    return f"{value:.1f} {_SIZE_UNITS[-1]}"
