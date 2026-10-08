"""The only module that touches the operating system: commands, PATH, root."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

DEFAULT_TIMEOUT_SECONDS = 60
_PKEXEC = "pkexec"
_SUDO = "sudo"
# pkexec and sudo drop the environment, so the settings travel on the command line.
_ROOT_ENV = ("env", "DEBIAN_FRONTEND=noninteractive", "LC_ALL=C")
NO_ELEVATION_MESSAGE = (
    "Administrator rights are needed, but neither pkexec nor sudo was found. "
    "Install polkit (package 'pkexec' or 'policykit-1') and try again."
)


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class Runner(Protocol):
    """Seam between managers and the operating system."""

    def which(self, binary: str) -> str | None: ...

    def run(
        self, argv: Sequence[str], timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> CommandResult: ...

    def stream(
        self, argv: Sequence[str], on_line: Callable[[str], None], as_root: bool = False
    ) -> int: ...

    def writable(self, path: str) -> bool: ...

    def expand(self, path: str) -> str: ...


class SystemRunner:
    """Runs real commands, without a shell and with a locale-independent environment."""

    def __init__(self) -> None:
        self._env = {**os.environ, "LC_ALL": "C", "DEBIAN_FRONTEND": "noninteractive"}

    def which(self, binary: str) -> str | None:
        return shutil.which(binary)

    def run(self, argv: Sequence[str], timeout: float = DEFAULT_TIMEOUT_SECONDS) -> CommandResult:
        command = tuple(argv)
        try:
            done = subprocess.run(
                command,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout,
                env=self._env,
                stdin=subprocess.DEVNULL,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return CommandResult(command, 127, "", str(error))
        return CommandResult(command, done.returncode, done.stdout, done.stderr)

    def stream(
        self, argv: Sequence[str], on_line: Callable[[str], None], as_root: bool = False
    ) -> int:
        """Run a command, feeding each output line to on_line; return the exit code."""
        command = self.elevated(argv) if as_root else tuple(argv)
        if not command:
            on_line(NO_ELEVATION_MESSAGE)
            return 127
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                errors="replace",
                env=self._env,
            )
        except OSError as error:
            on_line(str(error))
            return 127
        assert process.stdout is not None
        for line in process.stdout:
            on_line(line.rstrip("\n"))
        return process.wait()

    def elevated(self, argv: Sequence[str]) -> tuple[str, ...]:
        """Prefix argv so it runs as root; empty tuple when no way to elevate exists."""
        if os.geteuid() == 0:
            return tuple(argv)
        if self.which(_PKEXEC):
            return (_PKEXEC, *_ROOT_ENV, *argv)
        if self.which(_SUDO):
            return (_SUDO, "-n", *_ROOT_ENV, *argv)
        return ()

    def writable(self, path: str) -> bool:
        return os.access(path, os.W_OK)

    def expand(self, path: str) -> str:
        return os.path.expandvars(os.path.expanduser(path))
