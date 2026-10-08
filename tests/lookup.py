"""Lookups shared by the manager tests."""

from __future__ import annotations

from depman.core.models import Package


def find(manager, name: str) -> Package:
    return next(package for package in manager.list_packages() if package.name == name)


def action(manager, package: Package, action_id: str):
    return next(item for item in manager.actions(package) if item.id == action_id)
