"""Confirm an action, run it with live output, and report how it ended."""

from __future__ import annotations

from collections.abc import Callable

from gi.repository import Adw, GLib, Gtk

from depman.core.models import Action, Package
from depman.core.runner import Runner
from depman.ui.tasks import run_async

_CONFIRM = "confirm"
_CANCEL = "cancel"
_PREVIEW_HEIGHT = 180
_LOG_WIDTH = 680
_LOG_HEIGHT = 440
_AUTH_DISMISSED_CODES = (126, 127)


def confirm_and_run(
    parent: Gtk.Widget,
    runner: Runner,
    package: Package,
    action: Action,
    on_finished: Callable[[bool], None],
) -> None:
    """Ask the user to confirm the exact command, then run it and call on_finished(success)."""
    dialog = Adw.AlertDialog(
        heading=f"{action.label} {package.title}?",
        body=action.description,
        extra_child=_command_preview(runner, action),
    )
    dialog.add_response(_CANCEL, "Cancel")
    dialog.add_response(_CONFIRM, action.label)
    appearance = (
        Adw.ResponseAppearance.DESTRUCTIVE
        if action.destructive
        else Adw.ResponseAppearance.SUGGESTED
    )
    dialog.set_response_appearance(_CONFIRM, appearance)
    dialog.set_default_response(_CANCEL)
    dialog.set_close_response(_CANCEL)

    def responded(_dialog: Adw.AlertDialog, response: str) -> None:
        if response == _CONFIRM:
            _RunDialog(runner, package, action, on_finished).present(parent)

    dialog.connect("response", responded)
    dialog.present(parent)


def _command_preview(runner: Runner, action: Action) -> Gtk.Widget:
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    who = "Runs as administrator:" if action.needs_root else "Runs:"
    caption = Gtk.Label(label=who, xalign=0)
    caption.add_css_class("dim-label")
    command = Gtk.Label(label=" ".join(action.argv), xalign=0, wrap=True, selectable=True)
    command.add_css_class("monospace")
    command.add_css_class("command")
    box.append(caption)
    box.append(command)
    if action.preview_argv:
        preview = Gtk.Label(label="Checking what will change…", xalign=0, yalign=0, wrap=True)
        preview.add_css_class("monospace")
        preview.add_css_class("caption")
        box.append(Gtk.ScrolledWindow(child=preview, min_content_height=_PREVIEW_HEIGHT))
        run_async(
            lambda: runner.run(action.preview_argv),
            lambda result, error: preview.set_label(
                str(error) if result is None else (result.stdout or result.stderr).strip()
            ),
        )
    return box


class _RunDialog(Adw.Dialog):
    """Streams a running command's output and stays open until the user has seen the result."""

    def __init__(
        self,
        runner: Runner,
        package: Package,
        action: Action,
        on_finished: Callable[[bool], None],
    ) -> None:
        super().__init__(
            title=f"{action.label} {package.title}",
            content_width=_LOG_WIDTH,
            content_height=_LOG_HEIGHT,
            can_close=False,
        )
        self._on_finished = on_finished
        self._succeeded = False
        self._spinner = Gtk.Spinner(spinning=True)
        self._status = Gtk.Label(label="Working…", xalign=0, hexpand=True, wrap=True)
        self._status.add_css_class("heading")
        self._log = Gtk.TextView(editable=False, cursor_visible=False, monospace=True)
        self._log.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._log.add_css_class("log")
        self._close = Gtk.Button(label="Close", sensitive=False, halign=Gtk.Align.END)
        self._close.connect("clicked", lambda _button: self.close())
        self.set_child(self._layout())
        self.connect("closed", lambda _dialog: self._on_finished(self._succeeded))

        argv, as_root = action.argv, action.needs_root
        run_async(lambda: runner.stream(argv, self._line_from_thread, as_root), self._done)

    def _layout(self) -> Gtk.Widget:
        status = Gtk.Box(spacing=10)
        status.append(self._spinner)
        status.append(self._status)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for edge in ("top", "bottom", "start", "end"):
            getattr(body, f"set_margin_{edge}")(16)
        body.append(status)
        body.append(Gtk.ScrolledWindow(child=self._log, vexpand=True, has_frame=True))
        body.append(self._close)
        toolbar = Adw.ToolbarView(content=body)
        toolbar.add_top_bar(Adw.HeaderBar(show_end_title_buttons=False))
        return toolbar

    def _line_from_thread(self, line: str) -> None:
        GLib.idle_add(self._append, line)

    def _append(self, line: str) -> bool:
        buffer = self._log.get_buffer()
        buffer.insert(buffer.get_end_iter(), line + "\n")
        self._log.scroll_to_mark(
            buffer.create_mark(None, buffer.get_end_iter(), False), 0, False, 0, 0
        )
        return GLib.SOURCE_REMOVE

    def _done(self, exit_code: int | None, error: Exception | None) -> None:
        self._succeeded = exit_code == 0
        self._spinner.set_visible(False)
        self._status.set_label(_outcome(exit_code, error))
        self._status.add_css_class("success" if self._succeeded else "error")
        self._close.set_sensitive(True)
        self.set_can_close(True)


def _outcome(exit_code: int | None, error: Exception | None) -> str:
    if error is not None:
        return f"Failed: {error}"
    if exit_code == 0:
        return "Finished successfully"
    if exit_code in _AUTH_DISMISSED_CODES:
        return f"Not run (exit code {exit_code}). Authentication was cancelled or unavailable."
    return f"Failed with exit code {exit_code}"
