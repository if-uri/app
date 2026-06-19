"""urirun as the primary local runtime (replacement for the shell urisys-node).

These tests verify the in-process urirun dispatch path. They skip when the
optional `urirun` package is not installed.
"""

from __future__ import annotations

import json

import pytest

from ifuri_app import urirun_bridge as ub

pytestmark = pytest.mark.skipif(
    not ub.urirun_info().get("available"),
    reason="urirun package not installed",
)


def _registry():
    import urirun.v2 as v2

    doc = {
        "version": "urirun.bindings.v2",
        "bindings": {
            "sys://local/echo/hello": {
                "kind": "command",
                "adapter": "argv-template",
                "argv": ["echo", "hello-from-urirun"],
            },
            "util://local/echo/say": {
                "kind": "command",
                "adapter": "argv-template",
                "inputSchema": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
                "argv": ["echo", "{text}"],
            },
        },
    }
    return v2.compile_registry(doc)


def test_dispatch_local_unknown_route_returns_none():
    reg = _registry()
    assert ub.dispatch_local("nope://x/y/z", {}, registry=reg) is None


def test_dispatch_local_dry_run_uses_urirun():
    reg = _registry()
    res = ub.dispatch_local("util://local/echo/say", {"text": "hi"}, registry=reg)
    assert res is not None
    assert res["via"] == "urirun"
    assert res["mode"] == "dry-run"


def test_dispatch_local_execute_with_policy():
    reg = _registry()
    res = ub.dispatch_local(
        "sys://local/echo/hello",
        {},
        registry=reg,
        execute=True,
        policy={"execute": {"allow": ["sys://local/**"]}},
    )
    assert res is not None and res["ok"] is True
    assert res["result"]["stdout"].strip() == "hello-from-urirun"


def test_dispatch_local_without_registry_returns_none(monkeypatch):
    monkeypatch.delenv("IFURI_URIRUN_REGISTRY", raising=False)
    # No registry configured -> caller should fall back to another transport.
    assert ub.dispatch_local("sys://local/echo/hello", {}) is None


def test_scan_project_builds_registry(tmp_path):
    (tmp_path / "urirun.bindings.v2.json").write_text(
        json.dumps(
            {
                "version": "urirun.bindings.v2",
                "bindings": {
                    "sys://local/echo/hello": {
                        "kind": "command",
                        "adapter": "argv-template",
                        "argv": ["echo", "hi"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    registry_out = tmp_path / "registry.json"
    result = ub.scan_project(tmp_path, registry_out=registry_out)
    assert result["ok"] is True
    assert registry_out.exists()
    summary = ub.registry_summary(registry_out)
    assert summary["routes"] >= 1
    # the scanned registry actually resolves the route through urirun
    assert ub.dispatch_local("sys://local/echo/hello", {}, registry_path=registry_out) is not None


def test_run_flow_routes_via_urirun(tmp_path, monkeypatch):
    registry_out = tmp_path / "registry.json"
    (tmp_path / "urirun.bindings.v2.json").write_text(
        json.dumps(
            {
                "version": "urirun.bindings.v2",
                "bindings": {
                    "sys://local/echo/hello": {
                        "kind": "command",
                        "adapter": "argv-template",
                        "argv": ["echo", "hello-from-urirun"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    assert ub.scan_project(tmp_path, registry_out=registry_out)["ok"]

    monkeypatch.setenv("IFURI_URIRUN_REGISTRY", str(registry_out))
    monkeypatch.setenv("IFURI_HOME", str(tmp_path / "home"))

    from ifuri_app.runtime import RuntimeState

    res = RuntimeState().run_flow("do:\n  - sys://local/echo/hello\n", dry_run=False, approved=True)
    steps = res.get("steps", [])
    assert steps and steps[0]["via"] == "urirun"
    assert res["ok"] is True
