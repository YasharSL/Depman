"""One tab: the searchable list of packages installed by one manager."""

from __future__ import annotations

from collections.abc import Callable

from gi.repository import Adw, Gio, GObject, Gtk, Pango

from depman.core.manager import PackageManager
from depman.core.models import Package
from depman.ui.tasks import run_async

_LIST_WIDTH = 900
_ICON_SIZE = 32
_VERSION_WIDTH_CHARS = 26
_FALLBACK_ICON = "package-x-generic"


class PackageItem(GObject.Object):
    """List-model wrapper around a Package."""

    def __init__(self, package: Package) -> None:
        super().__init__()
        self.package = package


class PackageRow(Gtk.Box):
    """Icon, name, summary, scope tag and version of one package."""

    def __init__(self) -> None:
        super().__init__(spacing=12)
        self._icon = Gtk.Image(pixel_size=_ICON_SIZE)
        self._name = Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END)
        self._name.add_css_class("heading")
        self._summary = Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END)
        self._summary.add_css_class("dim-label")
        self._summary.add_css_class("caption")
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
        text.set_valign(Gtk.Align.CENTER)
        text.append(self._name)
        text.append(self._summary)
        self._scope = Gtk.Label(valign=Gtk.Align.CENTER)
        self._scope.add_css_class("scope-tag")
        self._version = Gtk.Label(
            ellipsize=Pango.EllipsizeMode.END, max_width_chars=_VERSION_WIDTH_CHARS
        )
        self._version.add_css_class("dim-label")
        self._version.add_css_class("numeric")
        chevron = Gtk.Image.new_from_icon_name("go-next-symbolic")
        chevron.add_css_class("dim-label")
        for child in (self._icon, text, self._scope, self._version, chevron):
            self.append(child)

    def bind(self, package: Package) -> None:
        theme = Gtk.IconTheme.get_for_display(self.get_display())
        has_own_icon = theme.has_icon(package.name)
        self._icon.set_from_icon_name(package.name if has_own_icon else _FALLBACK_ICON)
        self._name.set_label(package.title)
        self._summary.set_label(package.summary)
        self._summary.set_visible(bool(package.summary))
        self._scope.set_label(package.scope)
        self._scope.set_visible(bool(package.scope))
        self._version.set_label(package.version)


class ManagerPage(Gtk.Stack):
    """Loads a manager's packages in the background and shows them as a filterable list."""

    def __init__(self, manager: PackageManager, on_open: Callable[[Package], None]) -> None:
        super().__init__(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.manager = manager
        self._on_open = on_open
        self._query = ""
        self._store = Gio.ListStore(item_type=PackageItem)
        self._filter = Gtk.CustomFilter.new(self._matches)
        self._shown = Gtk.FilterListModel(model=self._store, filter=self._filter)
        self._shown.connect("items-changed", lambda *_args: self._update_count())
        self._count = Gtk.Label(xalign=0)
        self._count.add_css_class("dim-label")
        self._error = Adw.StatusPage(
            icon_name="dialog-warning-symbolic", title="Could not load packages"
        )
        self._build()
        self.reload()

    def reload(self, on_loaded: Callable[[], None] | None = None) -> None:
        """Fetch the package list again; on_loaded runs once the list is on screen."""
        if self._store.get_n_items() == 0:
            self.set_visible_child_name("loading")

        def done(packages: list[Package] | None, error: Exception | None) -> None:
            self._show(packages, error)
            if on_loaded:
                on_loaded()

        run_async(self.manager.list_packages, done)

    def set_query(self, query: str) -> None:
        self._query = query.strip().lower()
        self._filter.changed(Gtk.FilterChange.DIFFERENT)

    def contains(self, package: Package) -> bool:
        items = (self._store.get_item(index) for index in range(self._store.get_n_items()))
        return any(item.package.name == package.name for item in items)

    def _build(self) -> None:
        spinner = Gtk.Spinner(spinning=True, width_request=32, height_request=32)
        spinner.set_halign(Gtk.Align.CENTER)
        spinner.set_valign(Gtk.Align.CENTER)
        self.add_named(spinner, "loading")

        retry = Gtk.Button(label="Try Again", halign=Gtk.Align.CENTER)
        retry.add_css_class("pill")
        retry.connect("clicked", lambda _button: self.reload())
        self._error.set_child(retry)
        self.add_named(self._error, "error")

        empty = Adw.StatusPage(
            icon_name="package-x-generic-symbolic",
            title="Nothing installed",
            description=f"{self.manager.title} has no packages installed.",
        )
        self.add_named(empty, "empty")
        self.add_named(self._build_list(), "list")

    def _build_list(self) -> Gtk.Widget:
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", lambda _factory, item: item.set_child(PackageRow()))
        factory.connect(
            "bind", lambda _factory, item: item.get_child().bind(item.get_item().package)
        )
        view = Gtk.ListView(
            model=Gtk.NoSelection(model=self._shown),
            factory=factory,
            single_click_activate=True,
            show_separators=True,
        )
        view.add_css_class("package-list")
        view.connect("activate", self._activated)

        # The ListView must be the scrolled child itself, or it creates a widget per package.
        scroller = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vexpand=True,
            child=Adw.ClampScrollable(maximum_size=_LIST_WIDTH, child=view),
        )
        self._count.set_margin_top(18)
        self._count.set_margin_start(12)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.append(Adw.Clamp(maximum_size=_LIST_WIDTH, child=self._count))
        box.append(scroller)
        return box

    def _show(self, packages: list[Package] | None, error: Exception | None) -> None:
        if error is not None:
            self._error.set_description(str(error))
            self.set_visible_child_name("error")
            return
        self._store.splice(
            0, self._store.get_n_items(), [PackageItem(package) for package in packages or []]
        )
        self.set_visible_child_name("list" if packages else "empty")
        self._update_count()

    def _update_count(self) -> None:
        total = self._store.get_n_items()
        shown = self._shown.get_n_items()
        if self._query:
            self._count.set_label(f"{shown} of {total} packages match")
        else:
            self._count.set_label(f"{total} packages installed with {self.manager.title}")

    def _matches(self, item: PackageItem, *_user_data: object) -> bool:
        package = item.package
        haystack = f"{package.name} {package.display_name} {package.summary}".lower()
        return self._query in haystack

    def _activated(self, _view: Gtk.ListView, position: int) -> None:
        self._on_open(self._shown.get_item(position).package)
