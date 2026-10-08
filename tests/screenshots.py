"""Render the app on fixture data to PNG files (run with `make screenshot`)."""

from __future__ import annotations

from pathlib import Path

from gi.repository import Gdk, Graphene, Gtk

from tests import ui_driver

OUTPUT = Path("build/screenshots")


def capture(widget: Gtk.Widget, name: str) -> None:
    """Snapshot a widget through its renderer, so no screenshot tool is needed."""
    ui_driver.settle(0.8)
    paintable = Gtk.WidgetPaintable.new(widget)
    width, height = widget.get_width(), widget.get_height()
    snapshot = Gtk.Snapshot()
    paintable.snapshot(snapshot, width, height)
    node = snapshot.to_node()
    bounds = Graphene.Rect().init(0, 0, width, height)
    texture = widget.get_native().get_renderer().render_texture(node, bounds)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    texture.save_to_png(str(OUTPUT / f"{name}.png"))
    print(f"wrote {OUTPUT / name}.png ({width}x{height})")


def main() -> None:
    assert Gdk.Display.get_default() is not None, "no display: run under xvfb-run"
    app, window = ui_driver.start()
    capture(window, "1-apt-list")

    window._tabs.set_visible_child_name("pip")
    capture(window, "2-python-list")

    apt = window._pages["apt"]
    bash = next(
        item.package for item in map(apt._store.get_item, range(6)) if item.package.name == "bash"
    )
    window._tabs.set_visible_child_name("apt")
    window._open_package(bash)
    capture(window, "3-package-page")

    purge = apt.manager.actions(bash)[1]
    window._run_action(bash, purge)
    capture(window, "4-confirm-purge")
    window.close()
    app.quit()


if __name__ == "__main__":
    main()
