#!/usr/bin/env python3
"""Import-layering gate for D-04, S-PY-04 and S-GTK-07 (see architecture.md)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "depman"
RUNNER_FILE = "depman/core/runner.py"
RUNNER_ONLY = {"subprocess", "shutil"}
UI_FORBIDDEN_FOR_LOGIC = {"gi", "depman.ui"}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def starts_with(module: str, prefixes: set[str]) -> bool:
    return any(module == prefix or module.startswith(prefix + ".") for prefix in prefixes)


def violations(relative: str, modules: set[str]) -> list[str]:
    found: list[str] = []
    is_logic = relative.startswith(("depman/core/", "depman/managers/"))
    for module in sorted(modules):
        if is_logic and starts_with(module, UI_FORBIDDEN_FOR_LOGIC):
            found.append(f"{relative}: logic layer imports {module} (D-04)")
        if relative != RUNNER_FILE and starts_with(module, RUNNER_ONLY):
            found.append(f"{relative}: {module} is only allowed in {RUNNER_FILE} (S-PY-04)")
        if relative.startswith("depman/managers/") and module.startswith("depman.managers"):
            found.append(f"{relative}: managers must not import each other ({module})")
        if relative.startswith("depman/ui/") and module.startswith("depman.managers"):
            found.append(f"{relative}: UI imports a concrete manager {module} (S-GTK-07)")
    return found


def main() -> int:
    problems: list[str] = []
    for path in sorted(PACKAGE.rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        problems.extend(violations(relative, imported_modules(path)))
    for problem in problems:
        print(f"layering: {problem}")
    if not problems:
        print("layering: ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
