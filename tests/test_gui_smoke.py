# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""GUI smoke helpers (no display required for import checks)."""

from __future__ import annotations

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


def test_lan_scan_auto_refreshes_connectors(app, monkeypatch):
    """Skanuj LAN should also populate the Konektory tab, not just devices."""
    from ifuri_app import gui

    monkeypatch.setattr(gui, "scan_network", lambda **_kw: {
        "urisys_nodes": [{"endpoint": "http://node-a:8790", "node_id": "node-a"}],
        "ifuri_peers": [], "mcp_agent_services": [], "llm_services": [], "counts": {},
    })
    called = []
    monkeypatch.setattr(app, "refresh_connectors", lambda: called.append(True))
    app.discover_peers()
    assert called, "discover_peers must trigger refresh_connectors when a node is found"


def test_novnc_section_present(app):
    assert hasattr(app, "novnc_status")


def test_novnc_open_dashboard(app, monkeypatch):
    from ifuri_app import gui

    opened = []
    monkeypatch.setattr(gui.webbrowser, "open", lambda url: opened.append(url))
    app.open_novnc_dashboard()
    assert opened and opened[0].startswith("http://127.0.0.1:")
    assert "Dashboard" in app.novnc_status.get()


def test_novnc_precheck_missing_dir(app, monkeypatch):
    from ifuri_app import gui

    monkeypatch.setattr(gui, "demo_dir", lambda: None)
    assert app._novnc_precheck() is None
    assert "Nie znaleziono" in app.novnc_status.get()


def test_novnc_precheck_missing_docker(app, monkeypatch, tmp_path):
    from ifuri_app import gui

    monkeypatch.setattr(gui, "demo_dir", lambda: tmp_path)
    monkeypatch.setattr(gui, "docker_available", lambda: False)
    assert app._novnc_precheck() is None
    assert "docker" in app.novnc_status.get().lower()


_CONNECT_PKGS = {
    "ok": True,
    "packages": [
        {"name": "browser-control", "version": "0.3.1", "scheme": "browser", "summary": "Drive Chromium",
         "install": {"kind": "pip", "spec": "git+https://example/bc.git"},
         "routes": [{"uri": "browser://{node}/page/command/open", "params": [{"name": "url", "required": True}]}]},
        {"name": "time-tools", "version": "0.1.0", "scheme": "time", "summary": "",
         "install": {"kind": "manual", "spec": ""}, "routes": ["time://local/now"]},
    ],
}


def test_app_icon_asset_present():
    from ifuri_app.paths import assets_dir

    icon = assets_dir() / "icon.png"
    assert icon.is_file(), "brand-kit window icon should be bundled in assets/"


def test_app_icon_set_on_window(app):
    # _set_app_icon keeps a PhotoImage ref so Tk doesn't garbage-collect it
    assert getattr(app, "_app_icon", None) is not None


def test_connect_tab_present(app):
    tabs = [app.notebook.tab(i, "text") for i in range(len(app.notebook.tabs()))]
    assert "Connect" in tabs
    assert hasattr(app, "packages_tree")


def test_connect_catalog_and_payload_form(app):
    app._catalog_done(_CONNECT_PKGS)
    rows = app.packages_tree.get_children()
    assert len(rows) == 2
    app.packages_tree.selection_set(rows[0])  # browser-control
    app._on_package_select()
    assert "pip install" in app.connect_install_plan.get()
    assert set(app._payload_vars) == {"url", "node"}  # params + placeholder


def test_connect_payload_form_enriched_from_example(app):
    """Selecting a connector with example payloads builds a pre-filled run form."""
    from ifuri_app import connect_store as cs

    hub = {"connectors": [{
        "id": "planfile", "name": "Planfile Tasks", "uriSchemes": ["task"],
        "install": {"mode": "urirun-extra", "pipSpec": "urirun-connector-planfile @ git+https://x@v0.1.1"},
        "routes": ["task://host/tickets/query/list", "task://host/ticket/command/create"],
        "examples": [{"title": "Create", "uri": "task://host/ticket/command/create",
                      "payload": {"project": ".", "name": "Check DNS", "queue": "ops"}}],
    }]}
    app._catalog_done({"ok": True, "packages": cs.normalize_packages(hub)})
    app.packages_tree.selection_set(app.packages_tree.get_children()[0])
    app._on_package_select()
    # the command route (with an example) wins over the query route, fields pre-filled
    assert set(app._payload_vars) == {"project", "name", "queue"}
    assert app._payload_vars["name"].get() == "Check DNS"


def test_connect_install_manual_no_subprocess(app, monkeypatch):
    from ifuri_app import gui

    # if a subprocess were spawned for a manual package, this would explode the test
    monkeypatch.setattr(gui.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no subprocess for manual")))
    app._catalog_done(_CONNECT_PKGS)
    app.packages_tree.selection_set(app.packages_tree.get_children()[1])  # time-tools (manual)
    app.install_selected_connector()
    assert "ręczna" in app.connect_log.get("1.0", "end")


def test_connect_catalog_error(app):
    app._catalog_done({"ok": False, "error": "refused", "packages": []})
    assert "Błąd katalogu" in app.connect_status.get()
    assert app.packages_tree.get_children() == ()


def test_connect_registry_status_renders(app, monkeypatch):
    from ifuri_app import gui

    monkeypatch.setattr(gui, "local_registry_status", lambda: {
        "available": True, "configured": True, "registry": "/tmp/reg.json",
        "routes": 7, "bindings": 5, "version": "0.3.14",
    })
    app.refresh_registry_status()
    text = app.connect_registry_status.get()
    assert "7 tras" in text and "5 bindingów" in text


def test_connect_registry_status_no_urirun(app, monkeypatch):
    from ifuri_app import gui

    monkeypatch.setattr(gui, "local_registry_status", lambda: {
        "available": False, "configured": False, "registry": None, "routes": 0, "bindings": 0,
    })
    app.refresh_registry_status()
    assert "urirun nie zainstalowany" in app.connect_registry_status.get()


def test_connect_registry_status_registry_without_urirun(app, monkeypatch):
    from ifuri_app import gui

    # registry file present but urirun package missing → show count AND the warning
    monkeypatch.setattr(gui, "local_registry_status", lambda: {
        "available": False, "configured": True, "registry": "/tmp/reg.json", "routes": 12, "bindings": 12,
    })
    app.refresh_registry_status()
    text = app.connect_registry_status.get()
    assert "12 tras" in text and "⚠ urirun" in text
