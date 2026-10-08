# Core rules

Each rule has a stable ID. "Checked by" names the tool or checklist item that verifies it.

## Design and depth (D-)

| ID | Rule | Checked by |
|---|---|---|
| D-01 | A module hides real behavior behind a small interface. Prefer adding to a deep module's implementation over adding a new entry point. | A4 |
| D-02 | No pass-through functions, no helper used once, no interface with one implementation unless a second adapter exists (deletion test). | A4 |
| D-03 | A seam needs two adapters (for example the real one and a test one). Record it in `architecture.md`. | A6 |
| D-04 | Imports follow the layering in `architecture.md`. `depman.core` and `depman.managers` never import `gi` or `depman.ui`. | `scripts/layering.py` |
| D-05 | Callers never need to know a module's internal sequencing. If two calls must always happen together, they are one call. | A4 |
| D-06 | Tests go through a module's interface, never its private functions. | review, T-01 |

## Code clarity (C-)

| ID | Rule | Checked by |
|---|---|---|
| C-01 | Stay inside the limits table below. | ruff, ratchet |
| C-02 | Names say what a thing is in domain words: package, manager, action, details, runner. | ruff `N`, A3 |
| C-03 | No magic values. A literal with meaning gets a named module-level constant. | ruff `PLR2004`, A3 |
| C-04 | Comments explain why, not what. No commented-out code. | ruff `ERA`, A3 |
| C-05 | Public functions, methods and dataclass fields are type-annotated. | ruff `ANN` |
| C-06 | Data that crosses modules is a frozen dataclass, not a dict or tuple of loose values. | A3 |

## Errors (E-)

| ID | Rule | Checked by |
|---|---|---|
| E-01 | No bare `except` and no silently swallowed exception. | ruff `E722`, `BLE`, `S110` |
| E-02 | A failed external command becomes a `ManagerError` with the command and its stderr. The UI shows it; it never crashes the app. | tests |
| E-03 | Never build a shell string. Commands are argv tuples and run without a shell. | ruff `S602`, `S604`, `S605` |
| E-04 | A destructive or privileged command runs only from an `Action` the user confirmed, and the confirmation shows the exact command. | A3 |

## Tests (T-)

| ID | Rule | Checked by |
|---|---|---|
| T-01 | Every manager has tests for listing, details and actions, driven by recorded command output through `FakeRunner`. | pytest |
| T-02 | Tests never run a real package-manager command and never need root. | review |
| T-03 | A bugfix starts with a failing test. | B-bugfix |
| T-04 | Parsers are tested with real captured output kept in `tests/fixtures/`. | review |

## Performance (P-)

| ID | Rule | Checked by |
|---|---|---|
| P-01 | The GTK main loop never waits on a subprocess. Commands run through `depman.ui.tasks`. | A3, UI smoke test |
| P-02 | Long lists use `Gtk.ListView` with a model, not one widget per item. | A3 |
| P-03 | Details are loaded when a package is opened, not for the whole list. | A3 |

## Maintenance (M-)

| ID | Rule | Checked by |
|---|---|---|
| M-01 | One concern per change, roughly 400 changed lines at most; split otherwise. | B1 |
| M-02 | Bugs noticed outside the task go in the report, not in the diff. | A3 |
| M-03 | Search for an existing helper or pattern before writing a new one. | B3 |
| M-09 | Update `architecture.md` and `README.md` when the module map or behavior changes. | A6 |
| M-10 | A suppression (`# noqa`, `# type: ignore`) carries an inline reason and is listed in the report. | ruff `PGH`, A1 |

## Limits table

| Limit | Value | Tool |
|---|---|---|
| Line length | 100 | ruff format / `E501` |
| File length | 300 lines | `scripts/ratchet.py` |
| Function length | 40 statements | ruff `PLR0915` |
| Cyclomatic complexity | 8 | ruff `C901` |
| Function arguments | 5 | ruff `PLR0913` |
| Branches per function | 10 | ruff `PLR0912` |
| Nesting depth | 3 | ruff `PLR1702` (preview) / A3 |
