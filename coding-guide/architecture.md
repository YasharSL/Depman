# Architecture

## Glossary

- **Module**: a unit with an interface and an implementation (a file or package here).
- **Interface**: everything a caller must know to use a module.
- **Implementation**: what the module hides.
- **Depth**: how much behavior sits behind how small an interface. Deep is good; shallow means the interface is nearly as complex as what it hides.
- **Seam**: a place where one implementation can be swapped for another without editing callers.
- **Adapter**: a concrete implementation plugged into a seam.
- **Leverage**: what callers gain from a module per unit of interface they learn.
- **Locality**: a change, bug or piece of knowledge lives in one place.

Domain words: **manager** (a package manager such as apt or npm), **package** (one installed item), **details** (everything shown on a package's page), **action** (one command the user can run on a package: uninstall, purge, update), **scope** (where a package is installed: system, user, or apt-owned).

## Deep-module principles

1. One manager = one module. Everything about a manager (its commands, output formats, quirks, root needs) lives in its file. The rest of the app knows only the `PackageManager` interface.
2. The interface is three calls: `list_packages()`, `details(package)`, `actions(package)`. Adding a capability means deepening these, not adding a fourth call per manager.
3. The UI is generic. It renders `Package`, `Details` and `Action` and never branches on a manager id.
4. Apply the deletion test before adding a module: if deleting it only moves a line or two into the caller, it should not exist.

## Module map

| Module | Interface | Hides | Depth |
|---|---|---|---|
| `depman.core.models` | `Package`, `Details`, `Action`, `format_size` | nothing (value objects) | n/a |
| `depman.core.runner` | `Runner` protocol, `SystemRunner`, `CommandResult` | subprocess, locale, PATH lookup, root elevation (pkexec/sudo), output streaming | deep |
| `depman.core.manager` | `PackageManager` base, `ManagerError`, parsing helpers shared by three or more managers (`key_value_lines`, `leaf_paths`, `busiest_directories`) | detection probe, command failure handling | medium |
| `depman.core.registry` | `detect_managers(runner)` | the list of known managers and their order | small on purpose |
| `depman.managers.<name>` | a `PackageManager` subclass | that manager's commands, parsing, scopes, actions | deep |
| `depman.ui.tasks` | `run_async(work, on_done)` | threads and the hop back to the GTK main loop | deep |
| `depman.ui.window` | `MainWindow` | tabs, search, navigation, refresh after an action | medium |
| `depman.ui.manager_page` | `ManagerPage` | list model, filtering, loading and error states | deep |
| `depman.ui.details_page` | `DetailsPage` | layout of a package's page | medium |
| `depman.ui.action_dialog` | `confirm_and_run(...)` | confirmation, preview, live output, result | deep |
| `depman.ui.app` | `DepManApp`, `main()` | application setup and CSS loading | small |

## Layering

```
depman.ui  ->  depman.core.registry  ->  depman.managers  ->  depman.core.{manager,runner,models}
```

- `core` and `managers` never import `gi` or `depman.ui` (D-04).
- Only `depman/core/runner.py` imports `subprocess` or `shutil` (S-PY-04).
- `managers` modules never import each other.
- Enforced by `coding-guide/scripts/layering.py`.

## Seam register

| Seam | Adapters | Why it exists |
|---|---|---|
| `Runner` | `SystemRunner` (real), `tests.fake_runner.FakeRunner` (recorded output) | lets every manager be tested without the package manager installed or root |
| `PackageManager` | apt, pacman, dnf, zypper, snap, flatpak, pip, pipx, npm, cargo | the product's main variation point |

## Adding a manager

1. Add `depman/managers/<name>.py` with a `PackageManager` subclass.
2. Register it in `depman/core/registry.py`.
3. Add fixtures and tests in `tests/`. No UI change is needed.

Front ends that share one package database (DNF and Zypper over RPM) live in one module as
subclasses of a private base, because managers never import each other.
