#!/usr/bin/env python3
"""File-length ratchet: violations may shrink but never grow (see enforcement.md)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

MAX_FILE_LINES = 300
ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "coding-guide" / "baseline" / "file-length.json"
SOURCE_DIRS = ("depman", "tests", "coding-guide/scripts")


def measure() -> dict[str, int]:
    """Return {relative path: line count} for every file over the limit."""
    over: dict[str, int] = {}
    for source_dir in SOURCE_DIRS:
        for path in sorted((ROOT / source_dir).rglob("*.py")):
            lines = len(path.read_text(encoding="utf-8").splitlines())
            if lines > MAX_FILE_LINES:
                over[path.relative_to(ROOT).as_posix()] = lines
    return over


def check() -> int:
    baseline: dict[str, int] = json.loads(BASELINE.read_text(encoding="utf-8"))
    failures = [
        f"{name}: {lines} lines (limit {MAX_FILE_LINES}, baseline {baseline.get(name, 'none')})"
        for name, lines in measure().items()
        if lines > baseline.get(name, MAX_FILE_LINES)
    ]
    for failure in failures:
        print(f"ratchet: {failure}")
    if not failures:
        print(f"ratchet: ok ({len(baseline)} baselined file(s))")
    return 1 if failures else 0


def update() -> int:
    current = measure()
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"ratchet: baseline written ({len(current)} file(s) over the limit)")
    return 0


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    sys.exit(update() if command == "update" else check())
