# Stack rules: Python + GTK 4 / libadwaita

## Python (S-PY)

| ID | Rule | Checked by |
|---|---|---|
| S-PY-01 | Runtime code uses only the standard library and `gi`. No third-party runtime dependency. | review, `pyproject.toml` |
| S-PY-02 | `from __future__ import annotations` in every module; modern typing (`list[str]`, `X | None`). | ruff `UP`, `FA` |
| S-PY-03 | Value objects are `@dataclass(frozen=True)` with tuples, not lists. | A3 |
| S-PY-04 | External commands go through the `Runner` passed to the manager. No `subprocess`, `shutil.which` or `os.environ` outside `depman/core/runner.py`. | `scripts/layering.py` |
| S-PY-05 | Parsers are module-level pure functions or private methods taking text and returning dataclasses. | tests |
| S-PY-06 | Commands run with `LC_ALL=C` so output parsing does not depend on the user's locale. | `SystemRunner` |

## GTK / libadwaita (S-GTK)

| ID | Rule | Checked by |
|---|---|---|
| S-GTK-01 | Call `gi.require_version` once, in `depman/ui/__init__.py`. | review |
| S-GTK-02 | Widgets are touched only on the main thread. Worker results come back through `tasks.run_async`. | A3 |
| S-GTK-03 | Use libadwaita widgets and style classes (`Adw.NavigationView`, `Adw.ActionRow`, `.boxed-list`, `.title-1`, `.dim-label`) before writing custom CSS. | A3 |
| S-GTK-04 | Custom CSS lives only in `depman/ui/style.css`. Colours come from named colours, never inline hex in Python. | review |
| S-GTK-05 | The look follows Ubuntu's software app: centred clamped content, top tabs, plain rows, Ubuntu orange accent. No gradients, no custom window chrome. | A3 |
| S-GTK-06 | Target libadwaita 1.5 (Ubuntu 24.04). Do not use newer API without a guard. | UI smoke test |
| S-GTK-07 | UI modules hold no parsing or command knowledge; they consume `Package`, `Details`, `Action`. | `scripts/layering.py`, A4 |

## Tool config

- Formatter and linter: `ruff` (config in `pyproject.toml`).
- Tests: `pytest` (config in `pyproject.toml`). The UI smoke test needs a display; `make check` wraps it in `xvfb-run`.
- Dev setup on Ubuntu/WSL:
  `sudo apt install gir1.2-gtk-4.0 gir1.2-adw-1 python3-pytest xvfb make` and `pipx install ruff`.
