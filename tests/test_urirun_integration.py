# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

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


def test_urirun_serve_http(tmp_path):
    import json as _json
    import socket
    import threading
    import time
    import urllib.request

    (tmp_path / "urirun.bindings.v2.json").write_text(
        _json.dumps(
            {
                "version": "urirun.bindings.v2",
                "bindings": {
                    "sys://local/echo/hello": {
                        "kind": "command",
                        "adapter": "argv-template",
                        "argv": ["echo", "served-by-urirun"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    reg = tmp_path / "registry.json"
    assert ub.scan_project(tmp_path, registry_out=reg)["ok"]

    sk = socket.socket()
    sk.bind(("127.0.0.1", 0))
    port = sk.getsockname()[1]
    sk.close()

    threading.Thread(
        target=ub.serve_http,
        kwargs=dict(registry_path=str(reg), host="127.0.0.1", port=port, execute=True),
        daemon=True,
    ).start()

    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/health", timeout=1)
            break
        except Exception:
            time.sleep(0.1)

    def _get(path):
        return _json.loads(urllib.request.urlopen(base + path, timeout=2).read())

    def _post(path, obj):
        req = urllib.request.Request(
            base + path, data=_json.dumps(obj).encode(), headers={"Content-Type": "application/json"}
        )
        return _json.loads(urllib.request.urlopen(req, timeout=2).read())

    assert _get("/health")["ok"] is True
    assert len(_get("/routes")["routes"]) >= 1
    run = _post("/run", {"uri": "sys://local/echo/hello", "execute": True})
    assert run["ok"] is True
    assert run["result"]["stdout"].strip() == "served-by-urirun"


def test_cli_urirun_call_in_process_execute(tmp_path):
    """ifuri-app urirun-call runs a local-registry URI in-process (no service)."""
    import json as _json, subprocess, sys
    (tmp_path / "urirun.bindings.v2.json").write_text(
        _json.dumps({"version": "urirun.bindings.v2", "bindings": {
            "sys://local/echo/hello": {"kind": "command", "adapter": "argv-template",
                                       "argv": ["echo", "hello-cli"]}}}),
        encoding="utf-8")
    reg = tmp_path / "registry.json"
    subprocess.run([sys.executable, "-m", "ifuri_app.cli", "urirun-scan", str(tmp_path),
                    "--registry-out", str(reg)], check=True, capture_output=True)
    out = subprocess.run([sys.executable, "-m", "ifuri_app.cli", "urirun-call",
                          "sys://local/echo/hello", "--registry", str(reg), "--execute"],
                         capture_output=True, text=True)
    data = _json.loads(out.stdout)
    assert data["ok"] is True
    assert data["via"] == "urirun"
    assert data["result"]["stdout"].strip() == "hello-cli"


def test_cli_run_execute_uses_runtime_state(tmp_path, monkeypatch):
    """ifuri-app run --execute must not fall back to dry_run_flow."""
    import json as _json, subprocess, sys

    (tmp_path / "urirun.bindings.v2.json").write_text(
        _json.dumps(
            {
                "version": "urirun.bindings.v2",
                "bindings": {
                    "util://local/echo/say": {
                        "kind": "command",
                        "adapter": "argv-template",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"text": {"type": "string"}},
                            "required": ["text"],
                        },
                        "argv": ["echo", "{text}"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    reg = tmp_path / "registry.json"
    subprocess.run(
        [sys.executable, "-m", "ifuri_app.cli", "urirun-scan", str(tmp_path), "--registry-out", str(reg)],
        check=True,
        capture_output=True,
    )

    monkeypatch.setenv("IFURI_URIRUN_REGISTRY", str(reg))
    monkeypatch.setenv("IFURI_HOME", str(tmp_path / "home"))
    out = subprocess.run(
        [
            sys.executable,
            "-m",
            "ifuri_app.cli",
            "run",
            "util://local/echo/say",
            "--payload",
            '{"text":"hello-run"}',
            "--execute",
        ],
        capture_output=True,
        text=True,
    )
    data = _json.loads(out.stdout)
    assert data["ok"] is True
    assert data["via"] == "urirun"
    assert data["mode"] == "execute"
    assert data["result"]["stdout"].strip() == "hello-run"


def test_mcp_tools_and_a2a_card():
    reg = _registry()
    t = ub.mcp_tools(registry=reg)
    assert t["ok"] is True
    assert len(t["tools"]) == 2
    assert all("name" in x and "inputSchema" in x for x in t["tools"])
    c = ub.a2a_card(registry=reg, url="https://ifuri.com")
    assert c["ok"] is True
    assert c["card"]["name"] == "ifuri-urirun"
    assert len(c["card"]["skills"]) >= 1
