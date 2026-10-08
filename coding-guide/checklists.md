# Checklists

Used by `ystack-code`. Post a compact summary, not the whole list.

## Before (all tasks)

- **B1** Scope stated, out-of-scope stated; one concern, about 400 lines at most (M-01).
- **B2** Modules touched, from the module map, each marked deep or shallow.
- **B3** Searched for an existing helper or pattern (M-03).
- **B4** Shape chosen: which deep module absorbs the change, or why a new module passes the deletion test (D-01, D-02).
- **B5** Layering respected by the plan (D-04).
- **B6** Tests planned, and through which interface (D-06).
- **B7** Any new external command written as argv, with its root need and whether it is destructive (E-03, E-04).
- **B8** Baseline: `make check-fast` result before edits; pre-existing failures noted.

### Extras

- **Feature**: new manager follows "Adding a manager" in `architecture.md`; UI change has no manager-specific branch (S-GTK-07).
- **Bugfix**: failing test first (T-03); fixture captured from the real output that broke parsing (T-04).
- **Refactor**: follow `refactor-playbook.md`; characterization tests first; no behavior change.

## After (all tasks)

- **A1** Gates: `make format`, then `make check` green; suppressions have reasons (M-10).
- **A2** Ratchet baseline did not grow; if it shrank, run `make ratchet-update`.
- **A3** Diff self-review against `rules.md`: limits, names, comments, magic values, errors, no leftover debug code, main thread never blocked (P-01), confirmation shows the exact command (E-04).
- **A4** Depth check: nothing got shallower; no pass-through, no single-adapter seam, no manager knowledge in the UI.
- **A5** Deepening scan of touched code and neighbours; log candidates in `deepening-log.md`.
- **A6** Docs and map: `architecture.md`, `README.md` updated (M-09).
- **A7** Tests cover the new behavior through an interface; no real commands run (T-02).
- **A8** UI changes looked at: `make screenshot` and view the image.
