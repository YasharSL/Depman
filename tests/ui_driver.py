"""Helpers that start the real window on fixture data and pump the GTK main loop."""

from __future__ import annotations

import time
from collections.abc import Callable

from gi.repository import GLib

from depman.ui.app import DepManApp
from depman.ui.window import MainWindow
from tests.fake_runner import FakeRunner, demo_runner

_TIMEOUT_SECONDS = 10


def pump(until: Callable[[], bool] = lambda: False, seconds: float = _TIMEOUT_SECONDS) -> bool:
    """Run main-loop iterations until the condition holds or the time is up."""
    context = GLib.MainContext.default()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        if until():
            return True
        time.sleep(0.01)
    return until()


def settle(seconds: float = 0.4) -> None:
    pump(seconds=seconds)


def start(runner: FakeRunner | None = None) -> tuple[DepManApp, MainWindow]:
    """Activate the app with a fake runner and wait until its tabs have loaded."""
    app = DepManApp(runner or demo_runner())
    app.register(None)
    app.activate()
    window = app.window
    assert window is not None
    pump(lambda: window._body.get_visible_child_name() != "detecting")
    settle()
    return app, window
