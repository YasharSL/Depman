"""Application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from gi.repository import Adw, Gdk, Gtk

from depman import APP_ID
from depman.core.runner import Runner, SystemRunner
from depman.ui.window import MainWindow

_STYLESHEET = Path(__file__).with_name("style.css")


class DepManApp(Adw.Application):
    def __init__(self, runner: Runner | None = None) -> None:
        super().__init__(application_id=APP_ID)
        self._runner = runner or SystemRunner()
        self.window: MainWindow | None = None

    def do_activate(self) -> None:
        if self.window is None:
            provider = Gtk.CssProvider()
            provider.load_from_path(str(_STYLESHEET))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            self.window = MainWindow(self, self._runner)
        self.window.present()


def main() -> int:
    return DepManApp().run(sys.argv)
