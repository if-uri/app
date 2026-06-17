"""Resolve package paths for dev installs and PyInstaller bundles."""

from __future__ import annotations

import sys
from pathlib import Path


def app_package_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path.cwd()))
        for candidate in (base / "ifuri_app", base):
            if (candidate / "web").is_dir():
                return candidate
        return base / "ifuri_app"
    return Path(__file__).resolve().parent


def web_dir() -> Path:
    return app_package_dir() / "web"


def assets_dir() -> Path:
    return app_package_dir() / "assets"


def repo_root() -> Path:
    """Repository root (parent of src/)."""
    return app_package_dir().parent.parent


def packages_dir() -> Path:
    return repo_root() / "packages"
