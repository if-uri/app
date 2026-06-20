"""GUI smoke helpers (no display required for import checks)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def app():
    """Build IfuriDesktop headlessly, skipping when no usable display is present."""
    import tkinter as tk

    from ifuri_app.gui import IfuriDesktop

    try:
        instance = IfuriDesktop()
    except tk.TclError as exc:  # no display (CI without xvfb) → skip, not fail
        pytest.skip(f"no Tk display: {exc}")
    try:
        yield instance
    finally:
        instance.destroy()


def test_gui_module_imports():
    import tkinter  # noqa: F401

    from ifuri_app.gui import IfuriDesktop, TREE_ROW_HEIGHT, launch_gui  # noqa: F401

    assert callable(launch_gui)
    assert TREE_ROW_HEIGHT >= 28


def test_gui_smoke_script_parse():
    scripts = Path(__file__).resolve().parents[1] / "scripts" / "gui_smoke.py"
    text = scripts.read_text(encoding="utf-8")
    assert "run_gui_smoke" in text
    assert "Sieć lokalna" in text or "notebook_tabs" in text


def test_connectors_tab_present(app):
    tabs = [app.notebook.tab(i, "text") for i in range(len(app.notebook.tabs()))]
    assert "Konektory" in tabs
    assert hasattr(app, "connectors_tree")


def test_connectors_render_groups_by_node_and_scheme(app):
    app._connectors_done(
        [
            {
                "ok": True,
                "endpoint": "http://node-a:8790",
                "routes": [
                    {"uri": "sys://local/echo", "scheme": "sys", "kind": "command", "adapter": "argv-template", "detail": "echo hi"},
                    {"uri": "mcp://fs/list", "scheme": "mcp", "kind": "mcp", "adapter": "", "detail": ""},
                ],
            },
            {"ok": False, "endpoint": "http://dead:8790", "routes": [], "error": "refused"},
        ]
    )
    tree = app.connectors_tree
    nodes = tree.get_children()
    assert len(nodes) == 2  # one ok node + one error node
    ok_node = nodes[0]
    schemes = {tree.item(s, "text").split("://")[0] for s in tree.get_children(ok_node)}
    assert schemes == {"sys", "mcp"}
    assert "2 tras" in app.connectors_status.get()


def test_connectors_empty_state(app):
    app._last_scan = {}
    app.workspace.pop("urisys", None)
    app._urirun_serve = None
    app.refresh_connectors()
    assert "Brak znanych węzłów" in app.connectors_status.get()
