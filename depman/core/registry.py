"""The list of package managers DepMan knows, in tab order."""

from __future__ import annotations

from depman.core.manager import PackageManager
from depman.core.runner import Runner
from depman.managers.apt import Apt
from depman.managers.cargo import Cargo
from depman.managers.flatpak import Flatpak
from depman.managers.npm import Npm
from depman.managers.pacman import Pacman
from depman.managers.pip import Pip
from depman.managers.pipx import Pipx
from depman.managers.rpm import Dnf, Zypper
from depman.managers.snap import Snap

KNOWN_MANAGERS: tuple[type[PackageManager], ...] = (
    Apt,
    Pacman,
    Dnf,
    Zypper,
    Snap,
    Flatpak,
    Pip,
    Pipx,
    Npm,
    Cargo,
)


def detect_managers(runner: Runner) -> list[PackageManager]:
    """Instantiate every known manager that is installed and working on this system."""
    candidates = [manager_class(runner) for manager_class in KNOWN_MANAGERS]
    return [manager for manager in candidates if manager.detect()]
