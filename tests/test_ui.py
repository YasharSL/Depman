"""Smoke test of the real window on fixture data. Needs a display (xvfb-run)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.ui

ui_driver = pytest.importorskip("tests.ui_driver")


@pytest.fixture(scope="module")
def window():
    app, window = ui_driver.start()
    yield window
    window.close()
    app.quit()


def test_one_tab_per_detected_manager(window):
    assert list(window._pages) == ["apt", "snap", "flatpak", "pip", "pipx", "npm", "cargo"]
    assert window._body.get_visible_child_name() == "tabs"
    assert all(page.get_visible_child_name() == "list" for page in window._pages.values())


def test_search_filters_every_tab(window):
    window._search.set_text("bash")
    ui_driver.settle()
    assert window._pages["apt"]._shown.get_n_items() == 1
    assert window._pages["snap"]._shown.get_n_items() == 0
    window._search.set_text("")
    ui_driver.settle()
    assert window._pages["apt"]._shown.get_n_items() == 6


def test_opening_a_package_shows_its_page_with_actions(window):
    apt = window._pages["apt"]
    bash = next(
        item.package for item in map(apt._store.get_item, range(6)) if item.package.name == "bash"
    )
    window._open_package(bash)
    ui_driver.settle()
    page = window._navigation.get_visible_page()
    assert type(page).__name__ == "DetailsPage"
    assert page.get_title() == "bash"
    window._navigation.pop()
    ui_driver.settle()


def test_action_runs_only_after_confirmation(window):
    runner = window._runner
    snap = window._pages["snap"]
    nmap = snap._store.get_item(1).package
    purge = snap.manager.actions(nmap)[1]
    window._run_action(nmap, purge)
    ui_driver.settle()
    assert runner.streamed == []  # the confirmation dialog is open, nothing ran yet
