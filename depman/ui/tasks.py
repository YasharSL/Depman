"""Run blocking work off the GTK main loop and deliver the result back on it."""

from __future__ import annotations

import threading
from collections.abc import Callable

from gi.repository import GLib


def run_async[Result](
    work: Callable[[], Result],
    on_done: Callable[[Result | None, Exception | None], None],
) -> None:
    """Call work() in a thread, then on_done(result, error) on the main loop."""

    def deliver(result: Result | None, error: Exception | None) -> bool:
        on_done(result, error)
        return GLib.SOURCE_REMOVE

    def target() -> None:
        try:
            result = work()
        except Exception as error:  # noqa: BLE001 - any failure must reach the UI, not kill the thread
            GLib.idle_add(deliver, None, error)
        else:
            GLib.idle_add(deliver, result, None)

    threading.Thread(target=target, daemon=True).start()
