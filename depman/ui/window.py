"""Main window: one tab per detected manager, search, and navigation to package pages."""

from __future__ import annotations

from gi.repository import Adw, GObject, Gtk

from depman import APP_NAME
from depman.core.manager import PackageManager
from depman.core.models import Action, Package
from depman.core.registry import KNOWN_MANAGERS, detect_managers
from depman.core.runner import Runner
from depman.ui.action_dialog import confirm_and_run
from depman.ui.details_page import DetailsPage
from depman.ui.manager_page import ManagerPage
from depman.ui.tasks import run_async

_DEFAULT_SIZE = (1100, 760)
_SEARCH_WIDTH = 500


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application, runner: Runner) -> None:
        super().__init__(application=application, title=APP_NAME)
        self.set_default_size(*_DEFAULT_SIZE)
        self._runner = runner
        self._pages: dict[str, ManagerPage] = {}
        self._tabs = Adw.ViewStack()
        self._navigation = Adw.NavigationView()
        self._toasts = Adw.ToastOverlay(child=self._navigation)
        self._search = Gtk.SearchEntry(placeholder_text="Search installed packages", hexpand=True)
        self._search.connect("search-changed", self._search_changed)
        self._body = Gtk.Stack()
        self._navigation.add(Adw.NavigationPage(title=APP_NAME, child=self._root()))
        self.set_content(self._toasts)
        run_async(lambda: detect_managers(self._runner), self._managers_detected)

    def _root(self) -> Gtk.Widget:
        search_bar = Gtk.SearchBar(child=Adw.Clamp(maximum_size=_SEARCH_WIDTH, child=self._search))
        search_bar.connect_entry(self._search)
        search_bar.set_key_capture_widget(self)
        search_toggle = Gtk.ToggleButton(icon_name="system-search-symbolic", tooltip_text="Search")
        flags = GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE
        search_toggle.bind_property("active", search_bar, "search-mode-enabled", flags)
        refresh = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Reload all lists")
        refresh.connect("clicked", lambda _button: self._reload_all())

        header = Adw.HeaderBar()
        switcher = Adw.ViewSwitcher(stack=self._tabs, policy=Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(switcher)
        header.pack_start(search_toggle)
        header.pack_end(refresh)

        detecting = Adw.StatusPage(title="Looking for package managers…")
        detecting.set_child(Gtk.Spinner(spinning=True, width_request=32, height_request=32))
        self._body.add_named(detecting, "detecting")
        self._body.add_named(self._tabs, "tabs")
        nothing = Adw.StatusPage(
            icon_name="package-x-generic-symbolic",
            title="No package managers found",
            description="DepMan looks for " + ", ".join(m.title for m in KNOWN_MANAGERS) + ".",
        )
        self._body.add_named(nothing, "nothing")

        toolbar = Adw.ToolbarView(content=self._body)
        toolbar.add_top_bar(header)
        toolbar.add_top_bar(search_bar)
        return toolbar

    def _managers_detected(
        self, managers: list[PackageManager] | None, _error: Exception | None
    ) -> None:
        for manager in managers or []:
            page = ManagerPage(manager, self._open_package)
            self._pages[manager.id] = page
            self._tabs.add_titled_with_icon(page, manager.id, manager.title, manager.icon)
        self._body.set_visible_child_name("tabs" if self._pages else "nothing")

    def _search_changed(self, entry: Gtk.SearchEntry) -> None:
        for page in self._pages.values():
            page.set_query(entry.get_text())

    def _reload_all(self) -> None:
        for page in self._pages.values():
            page.reload()

    def _open_package(self, package: Package) -> None:
        manager = self._pages[package.manager_id].manager
        self._navigation.push(DetailsPage(manager, package, self._run_action))

    def _run_action(self, package: Package, action: Action) -> None:
        def finished(succeeded: bool) -> None:
            if succeeded:
                self._toasts.add_toast(Adw.Toast(title=f"{action.label}: {package.title} done"))
            page = self._pages[package.manager_id]
            page.reload(lambda: self._after_reload(page, package))

        confirm_and_run(self, self._runner, package, action, finished)

    def _after_reload(self, page: ManagerPage, package: Package) -> None:
        """Leave the package's page if it is gone, otherwise show its fresh details."""
        details = self._navigation.get_visible_page()
        if not isinstance(details, DetailsPage) or details.package.name != package.name:
            return
        if page.contains(package):
            details.refresh()
        else:
            self._navigation.pop()
