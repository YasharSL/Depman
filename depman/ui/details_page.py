"""A package's own page: header, action buttons, details, locations and files."""

from __future__ import annotations

from collections.abc import Callable

from gi.repository import Adw, Gio, Gtk, Pango

from depman.core.manager import PackageManager
from depman.core.models import Action, Details, Package
from depman.ui.tasks import run_async

_PAGE_WIDTH = 860
_ICON_SIZE = 96
_FILES_SHOWN = 500
_FILES_HEIGHT = 320
_FALLBACK_ICON = "package-x-generic"
_URL_PREFIXES = ("http://", "https://")


class DetailsPage(Adw.NavigationPage):
    """Shows everything about one package and offers the manager's actions for it."""

    def __init__(
        self,
        manager: PackageManager,
        package: Package,
        on_action: Callable[[Package, Action], None],
    ) -> None:
        super().__init__(title=package.title)
        self.manager = manager
        self.package = package
        self._on_action = on_action
        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        for edge in ("top", "bottom", "start", "end"):
            getattr(self._content, f"set_margin_{edge}")(24)
        clamp = Adw.Clamp(maximum_size=_PAGE_WIDTH, child=self._content)
        scroller = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, child=clamp)
        toolbar = Adw.ToolbarView(content=scroller)
        toolbar.add_top_bar(Adw.HeaderBar())
        self.set_child(toolbar)
        self.refresh()

    def refresh(self) -> None:
        """Load the details again, for example after an update or reinstall."""
        run_async(lambda: self.manager.details(self.package), self._show)

    def _show(self, details: Details | None, error: Exception | None) -> None:
        self._clear()
        if details is None:
            self._content.append(
                Adw.StatusPage(
                    icon_name="dialog-warning-symbolic",
                    title="Could not load details",
                    description=str(error),
                )
            )
            return
        self.package = details.package
        self._content.append(self._header(details.package))
        if details.note:
            self._content.append(_note(details.note))
        if details.description:
            self._content.append(_description(details.description))
        if details.fields:
            self._content.append(self._fields_group(details))
        if details.locations:
            self._content.append(self._locations_group(details.locations))
        if details.files:
            self._content.append(_files_group(details.files))

    def _clear(self) -> None:
        while child := self._content.get_first_child():
            self._content.remove(child)

    def _header(self, package: Package) -> Gtk.Widget:
        theme = Gtk.IconTheme.get_for_display(self.get_display())
        icon_name = package.name if theme.has_icon(package.name) else _FALLBACK_ICON
        icon = Gtk.Image(icon_name=icon_name, pixel_size=_ICON_SIZE)

        name = Gtk.Label(label=package.title, xalign=0, wrap=True, selectable=True)
        name.add_css_class("title-1")
        summary = Gtk.Label(label=package.summary, xalign=0, wrap=True)
        summary.set_visible(bool(package.summary))
        version = Gtk.Label(label=f"Version {package.version} · {self.manager.title}", xalign=0)
        version.add_css_class("dim-label")
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, hexpand=True)
        text.set_valign(Gtk.Align.CENTER)
        for child in (name, summary, version, self._buttons()):
            text.append(child)

        header = Gtk.Box(spacing=24)
        header.append(icon)
        header.append(text)
        return header

    def _buttons(self) -> Gtk.Widget:
        box = Gtk.Box(spacing=8, margin_top=10)
        for index, action in enumerate(self.manager.actions(self.package)):
            button = Gtk.Button(label=action.label, tooltip_text=action.description)
            if index == 0 and action.destructive:
                button.add_css_class("destructive-action")
            button.connect("clicked", self._clicked, action)
            box.append(button)
        return box

    def _clicked(self, _button: Gtk.Button, action: Action) -> None:
        self._on_action(self.package, action)

    def _fields_group(self, details: Details) -> Gtk.Widget:
        group = Adw.PreferencesGroup(title="Details")
        group.add(_property_row("Package name", details.package.name))
        for label, value in details.fields:
            row = _property_row(label, value)
            if value.startswith(_URL_PREFIXES):
                row.add_suffix(self._open_button("adw-external-link-symbolic", value))
            group.add(row)
        return group

    def _locations_group(self, locations: tuple[str, ...]) -> Gtk.Widget:
        group = Adw.PreferencesGroup(
            title="Locations", description="Where this package keeps its files"
        )
        for path in locations:
            row = _property_row("", path)
            row.add_suffix(self._open_button("folder-open-symbolic", Gio.File.new_for_path(path)))
            group.add(row)
        return group

    def _open_button(self, icon_name: str, target: str | Gio.File) -> Gtk.Button:
        button = Gtk.Button(icon_name=icon_name, valign=Gtk.Align.CENTER, tooltip_text="Open")
        button.add_css_class("flat")
        if isinstance(target, str):
            launcher = Gtk.UriLauncher.new(target)
        else:
            launcher = Gtk.FileLauncher.new(target)
        button.connect("clicked", lambda _button: launcher.launch(self.get_root(), None, None))
        return button


def _property_row(label: str, value: str) -> Adw.ActionRow:
    # Markup must be off before the text is set: values such as "Name <mail@host>" are not markup.
    row = Adw.ActionRow(use_markup=False, subtitle_selectable=True)
    row.set_title(label)
    row.set_subtitle(value)
    row.add_css_class("property")
    return row


def _note(text: str) -> Gtk.Widget:
    label = Gtk.Label(label=text, xalign=0, wrap=True)
    label.add_css_class("note")
    return label


def _description(text: str) -> Gtk.Widget:
    return Gtk.Label(label=text, xalign=0, wrap=True, selectable=True)


def _files_group(files: tuple[str, ...]) -> Gtk.Widget:
    listing = "\n".join(files[:_FILES_SHOWN])
    if len(files) > _FILES_SHOWN:
        listing += f"\n… and {len(files) - _FILES_SHOWN} more"
    label = Gtk.Label(label=listing, xalign=0, yalign=0, selectable=True)
    label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
    label.add_css_class("monospace")
    label.add_css_class("file-list")
    scroller = Gtk.ScrolledWindow(
        child=label, min_content_height=min(_FILES_HEIGHT, 24 * len(files) + 24)
    )
    expander = Adw.ExpanderRow(title="Installed files", subtitle=f"{len(files)} files")
    expander.add_row(Gtk.ListBoxRow(child=scroller, activatable=False))
    group = Adw.PreferencesGroup()
    group.add(expander)
    return group
