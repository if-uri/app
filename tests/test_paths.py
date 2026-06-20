# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Unit tests for ifuri_app.paths — dev-install and PyInstaller path resolution."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ifuri_app import paths  # noqa: E402


def test_app_package_dir_dev():
    pkg = paths.app_package_dir()
    assert pkg.name == "ifuri_app"
    assert (pkg / "__init__.py").is_file()


def test_web_and_assets_under_package():
    pkg = paths.app_package_dir()
    assert paths.web_dir() == pkg / "web"
    assert paths.assets_dir() == pkg / "assets"


def test_repo_root_and_packages_dir():
    # app_package_dir() == <repo>/src/ifuri_app -> repo_root == <repo>
    pkg = paths.app_package_dir()
    assert paths.repo_root() == pkg.parent.parent
    assert paths.packages_dir() == paths.repo_root() / "packages"


def test_frozen_bundle_branch(monkeypatch, tmp_path):
    """When sys.frozen is set, resolve relative to _MEIPASS, preferring the dir with web/."""
    bundle = tmp_path / "bundle"
    (bundle / "ifuri_app" / "web").mkdir(parents=True)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    assert paths.app_package_dir() == bundle / "ifuri_app"


def test_frozen_bundle_fallback_without_web(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    # no web/ anywhere → falls back to <base>/ifuri_app
    assert paths.app_package_dir() == tmp_path / "ifuri_app"
