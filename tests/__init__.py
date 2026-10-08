"""Tests. Importing depman.ui here pins the GTK versions before any gi.repository import."""

import contextlib

with contextlib.suppress(ImportError, ValueError):
    import depman.ui  # noqa: F401 - imported for its gi.require_version side effect
