# DepMan coding guide

Single source of truth for how code is written in this repo. The `ystack-code` skill reads it before and after every change.

## Detected stack

- Language: Python 3.12+ (system interpreter, because PyGObject comes from the distro)
- UI: GTK 4 + libadwaita 1.5+ through PyGObject
- Package manager: none at runtime (stdlib + distro `gi`); dev tools are `ruff` and `pytest`
- Test runner: pytest
- Target OS: any current Linux distribution (developed on Windows through WSL Ubuntu 24.04; Arch and Fedora checked in containers)
- Monorepo: no

## Read order

1. `rules.md` — core rules and the limits table
2. `stack/python-gtk.md` — Python and GTK rules, tool config
3. `architecture.md` — glossary, module map, layering, seam register
4. `checklists.md` — Before/After checklists per task type
5. `enforcement.md` — gates and how to run them
6. `refactor-playbook.md`, `deepening-log.md` — when refactoring

## Commands

| Command | What it runs |
|---|---|
| `make check` | format check, lint, layering, ratchet, all tests |
| `make check-fast` | lint, layering, tests without the UI smoke test |
| `make format` | `ruff format` + `ruff check --fix` |
| `make run` | start the app |
| `make deb` | build the Debian package into `dist/` |
| `make install` / `make uninstall` | distro-independent install under `PREFIX` (default `/usr/local`) |

## Precedence

User instruction > `CONTEXT.md` / `docs/adr/` (none yet) > this guide > tool defaults.
When a rule here is wrong for a situation, waive it in the change report and propose the guide edit; do not skip it silently.
