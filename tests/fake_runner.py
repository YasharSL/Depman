"""Test adapter for the Runner seam: answers commands from recorded output."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from depman.core.runner import CommandResult

FIXTURES = Path(__file__).parent / "fixtures"
FAKE_HOME = "/home/test"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


Output = str | Callable[[tuple[str, ...]], str]


class FakeRunner:
    """Maps a command-line prefix to stdout; unknown commands fail like a missing binary."""

    def __init__(
        self,
        outputs: dict[str, Output] | None = None,
        binaries: Sequence[str] = (),
        writable_prefixes: Sequence[str] = (FAKE_HOME,),
    ) -> None:
        self.outputs = dict(outputs or {})
        self.binaries = set(binaries) | {line.split()[0] for line in self.outputs}
        self.writable_prefixes = tuple(writable_prefixes)
        self.streamed: list[tuple[tuple[str, ...], bool]] = []

    def which(self, binary: str) -> str | None:
        return f"/usr/bin/{binary}" if binary in self.binaries else None

    def run(self, argv: Sequence[str], timeout: float = 0) -> CommandResult:
        command = tuple(argv)
        line = " ".join(command)
        prefixes = [key for key in self.outputs if line.startswith(key)]
        if not prefixes:
            return CommandResult(command, 127, "", f"{command[0]}: command not found")
        output = self.outputs[max(prefixes, key=len)]
        return CommandResult(command, 0, output if isinstance(output, str) else output(command), "")

    def stream(
        self, argv: Sequence[str], on_line: Callable[[str], None], as_root: bool = False
    ) -> int:
        self.streamed.append((tuple(argv), as_root))
        on_line(f"ran {' '.join(argv)}")
        return 0

    def writable(self, path: str) -> bool:
        return path.startswith(self.writable_prefixes)

    def expand(self, path: str) -> str:
        return path.replace("~", FAKE_HOME)


def _pip_inspect(argv: tuple[str, ...]) -> str:
    """The inspect script gets a package name as a fourth argument when asked for details."""
    return fixture("pip_details_requests.json" if len(argv) > 3 else "pip_list.json")


def demo_runner() -> FakeRunner:
    """A system with every supported manager installed, built from the fixtures."""
    return FakeRunner(
        {
            "dpkg-query --version": "dpkg-query 1.22.6",
            "dpkg-query -W": fixture("dpkg_list.txt"),
            "dpkg-query -W -f=${Architecture}": fixture("dpkg_details_bash.txt"),
            "dpkg-query -L": fixture("dpkg_files_bash.txt"),
            "apt-mark showmanual": "bash\n",
            "apt-get -s": "Reading package lists...\nRemv bash [5.2.21-2ubuntu4]\n",
            "snap version": "snap 2.77.1",
            "snap list": fixture("snap_list.txt"),
            "snap info": fixture("snap_info_nmap.txt"),
            "flatpak --version": "Flatpak 1.14.6",
            "flatpak list": fixture("flatpak_list.txt"),
            "flatpak info": fixture("flatpak_info_firefox.txt"),
            "flatpak info --show-location": "/var/lib/flatpak/app/org.mozilla.firefox\n",
            "python3 --version": "Python 3.12.3",
            "python3 -c": _pip_inspect,
            "pipx --version": "1.4.3",
            "pipx list": fixture("pipx_list.json"),
            "pipx environment": f"{FAKE_HOME}/.local/share/pipx/venvs\n",
            "npm --version": "10.8.2",
            "npm ls": fixture("npm_ls.json"),
            "npm prefix": f"{FAKE_HOME}/.npm-global\n",
            "cargo --version": "cargo 1.81.0",
            "cargo install": fixture("cargo_list.txt"),
        }
    )


def arch_runner() -> FakeRunner:
    """An Arch system, from output captured in an archlinux container."""
    return FakeRunner(
        {
            "pacman --version": "Pacman v7.0.0",
            "pacman -Qi": fixture("pacman_list.txt"),
            "pacman -Qi bash": fixture("pacman_info_bash.txt"),
            "pacman -Qlq": fixture("pacman_files_bash.txt"),
            "pacman -Qmq": "pacman\n",
        }
    )


def fedora_runner(front_end: str = "dnf") -> FakeRunner:
    """An RPM system, from output captured in a fedora container."""
    return FakeRunner(
        {
            f"{front_end} --version": "5.4.3.0",
            "rpm -qa": fixture("rpm_list.txt"),
            "rpm -q --qf": fixture("rpm_details_bash.txt"),
            "rpm -ql": fixture("rpm_files_bash.txt"),
        }
    )
