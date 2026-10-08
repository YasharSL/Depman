"""The interface every package manager module implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from posixpath import dirname
from typing import ClassVar

from depman.core.models import Action, Details, Package
from depman.core.runner import Runner

_PROBE_TIMEOUT_SECONDS = 10
_MAX_LOCATIONS = 8


class ManagerError(Exception):
    """A package-manager command failed; the message is safe to show to the user."""


def key_value_lines(text: str) -> dict[str, str]:
    """Parse `Key: value` lines (snap info, flatpak info); later duplicates are ignored."""
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() and value.strip():
            pairs.setdefault(key.strip(), value.strip())
    return pairs


def leaf_paths(paths: list[str]) -> tuple[str, ...]:
    """Keep files only: dpkg, pacman and rpm file lists also name every parent directory."""
    listed = {path.rstrip("/") for path in paths if path.startswith("/") and path != "/."}
    parents = {dirname(path) for path in listed}
    return tuple(sorted(listed - parents - {""}))


def busiest_directories(files: tuple[str, ...]) -> tuple[str, ...]:
    """The directories holding most of a package's files, busiest first."""
    counts = Counter(dirname(path) for path in files)
    return tuple(directory for directory, _ in counts.most_common(_MAX_LOCATIONS))


class PackageManager(ABC):
    """One package manager: lists what it installed and offers actions on each package."""

    id: ClassVar[str]
    title: ClassVar[str]
    icon: ClassVar[str] = "package-x-generic-symbolic"
    # Command that proves the manager is installed and working, e.g. ("snap", "version").
    probe: ClassVar[tuple[str, ...]]

    def __init__(self, runner: Runner) -> None:
        self._runner = runner

    def detect(self) -> bool:
        """True when the manager's binary exists and answers its probe command."""
        if self._runner.which(self.probe[0]) is None:
            return False
        return self._runner.run(self.probe, timeout=_PROBE_TIMEOUT_SECONDS).ok

    @abstractmethod
    def list_packages(self) -> list[Package]:
        """Every package this manager has installed, sorted by name."""

    @abstractmethod
    def details(self, package: Package) -> Details:
        """Full information for one package's page."""

    @abstractmethod
    def actions(self, package: Package) -> list[Action]:
        """Commands the user may run on this package; the first is the main one."""

    def _output(self, *argv: str) -> str:
        """Run a read-only command and return its stdout, or raise ManagerError."""
        result = self._runner.run(argv)
        if not result.ok:
            reason = result.stderr.strip() or f"exit code {result.returncode}"
            raise ManagerError(f"`{' '.join(argv)}` failed: {reason}")
        return result.stdout
