# Enforcement

Tooling says "no"; prose says "please". Every gate below runs from `make check`.

## Gates

| Gate | Command | Rules |
|---|---|---|
| Format | `ruff format --check .` | C-01 |
| Lint | `ruff check .` | C-, E-, M-10, limits table |
| Layering | `python3 coding-guide/scripts/layering.py` | D-04, S-PY-04, S-GTK-07 |
| Ratchet | `python3 coding-guide/scripts/ratchet.py check` | file length (C-01) |
| Tests | `pytest` (UI smoke test under `xvfb-run`) | T-, E-02 |

## Commands

- `make check` — all gates. Must be green before a change is called done.
- `make check-fast` — lint, layering and tests without the UI smoke test.
- `make format` — apply formatting and safe lint fixes.
- `make ratchet-update` — rewrite the baseline after files got shorter.
- `make screenshot` — render the app with fixture data to `build/screenshots/`.

## Ratchet

`coding-guide/scripts/ratchet.py` records, in `coding-guide/baseline/file-length.json`, every Python file that is over the file-length limit and by how much. `check` fails if a file not in the baseline goes over the limit, or a baselined file grows. The baseline may only shrink.

The skill's bundled `assets/ratchet.py` was not present in this installation, so this script was written for the repo.

## Hooks and CI

- `.githooks/pre-commit` runs `make check-fast`. Enable with `git config core.hooksPath .githooks`.
- No CI is configured yet (no remote). When one is added, it runs `make check` on Ubuntu 24.04 with the packages listed in `stack/python-gtk.md`.

## Exception policy

A rule is waived only with an inline reason (`# noqa: RULE - reason`) and a line in the change report. Repeated waivers of one rule mean the rule should change: propose the edit to `rules.md`.
