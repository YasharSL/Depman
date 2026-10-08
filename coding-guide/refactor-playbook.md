# Refactor playbook

Behavior-preserving, one module at a time. Bugs found on the way are reported, not fixed in the same change.

## Layer 0 — safety net

1. `make check` green and committed.
2. For the module you will touch, add characterization tests through its interface using recorded output (`tests/fixtures/`).

## Layer 1 — mechanical

Formatting, names (C-02), named constants (C-03), dead code removal. No structure change. `make check` after each step.

## Layer 2 — locality

Move knowledge to the module that owns it: manager quirks out of the UI into the manager; command execution into `Runner`. Each move is its own commit.

## Layer 3 — deepening

Pick one candidate from `deepening-log.md`. Shrink the interface or absorb callers' sequencing into the implementation. Delete the shallow pieces; leave no shims. Update the module map.

## Layer 4 — lock in

`make ratchet-update`, update `architecture.md` and mark the log entry `done`.

## Stop conditions

- A test must change its expected values: that is a behavior change; stop and split it out.
- The diff exceeds one module: stop and split.
