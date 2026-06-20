# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Tests for packages/ URI pack discovery."""

from __future__ import annotations


from ifuri_app.packs.loader import discover_manifests, pack_summary, packages_root


def test_packages_root_exists():
    root = packages_root()
    assert root.is_dir()
    assert (root / "README.md").is_file()


def test_discover_manifests_finds_bridge_voice_chat():
    manifests = discover_manifests()
    names = {p.parent.name for p in manifests}
    assert "ifuri-bridge" in names
    assert "ifuri-voice" in names
    assert "ifuri-chat" in names
    assert len(manifests) >= 3


def test_pack_summary_lists_js_page_pack():
    summary = pack_summary()
    ids = {item["id"] for item in summary}
    assert "ifuri-page" in ids
    page = next(x for x in summary if x["id"] == "ifuri-page")
    assert page["kind"] in {"javascript", "python+js"}


def test_load_local_registry_when_uricore_available():
    try:
        from ifuri_app.packs.loader import load_local_registry
    except ImportError:
        return
    try:
        registry = load_local_registry()
    except ImportError:
        return
    assert len(registry.manifests) >= 3
    schemes = {m.scheme for m in registry.manifests}
    assert "app" in schemes
    assert "voice" in schemes
