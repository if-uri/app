"""End-to-end: discover a remote urirun node and its MCP/A2A/URI routes.

Spins up a lightweight HTTP server that mimics a real urirun node (``GET
/health`` + ``GET /routes``) and exercises the app's discovery path end to end:

    probe_urisys_node  ->  scan_urisys_nodes  ->  connectors.fetch_node_routes

This needs no display and no optional ``urirun`` package — it tests the app's
own client/discovery code against a faithful stand-in for the node's HTTP API.
"""

from __future__ import annotations

import json
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ifuri_app import connectors  # noqa: E402
from ifuri_app.network_scan import probe_urisys_node, scan_urisys_nodes  # noqa: E402

NODE_HEALTH = {
    "ok": True,
    "node_id": "e2e-node",
    "him_driver": "mock",
    "routes_count": 3,
    "packs_loaded": ["sys", "mcp", "a2a"],
}
NODE_ROUTES = {
    "ok": True,
    "routes": [
        {"uri": "sys://local/echo", "kind": "command", "adapter": "argv-template", "argv": ["echo", "hi"]},
        {"uri": "mcp://filesystem/list", "kind": "mcp", "adapter": "mcp-stdio"},
        {"uri": "a2a://agent/plan", "kind": "agent", "adapter": "a2a-http"},
    ],
}


class _NodeHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):  # quiet test output
        pass

    def _send(self, obj: dict) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path in ("/", "/health"):
            self._send(NODE_HEALTH)
        elif self.path == "/routes":
            self._send(NODE_ROUTES)
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture
def remote_node():
    """A running fake urirun node; yields (host, port)."""
    httpd = HTTPServer(("127.0.0.1", 0), _NodeHandler)
    host, port = httpd.server_address[0], httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    # wait until /health answers
    base = f"http://{host}:{port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/health", timeout=1)
            break
        except Exception:
            time.sleep(0.05)
    try:
        yield host, port
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_probe_discovers_remote_node(remote_node):
    host, port = remote_node
    node = probe_urisys_node(host, port, timeout=1.0)
    assert node is not None
    assert node["endpoint"] == f"http://{host}:{port}"
    assert node["node_id"] == "e2e-node"
    assert node["routes_count"] == 3
    assert set(node["packs_loaded"]) == {"sys", "mcp", "a2a"}


def test_scan_finds_node_via_extra_hosts(remote_node):
    host, port = remote_node
    # don't scan the /24 subnet — just target the fake node's host on its port
    nodes = scan_urisys_nodes(timeout=1.5, port=port, scan_subnet=False, extra_hosts=[host])
    endpoints = {n["endpoint"] for n in nodes}
    assert f"http://{host}:{port}" in endpoints


def test_route_discovery_covers_uri_mcp_a2a(remote_node):
    host, port = remote_node
    result = connectors.fetch_node_routes(f"http://{host}:{port}", timeout=2.0)
    assert result["ok"] is True
    schemes = {r["scheme"] for r in result["routes"]}
    assert {"sys", "mcp", "a2a"} <= schemes
    grouped = connectors.group_by_scheme(result["routes"])
    assert grouped["mcp"][0]["uri"] == "mcp://filesystem/list"
    assert grouped["a2a"][0]["adapter"] == "a2a-http"
    echo = grouped["sys"][0]
    assert echo["kind"] == "command"
    assert echo["detail"] == "echo hi"


class _NoVncHandler(BaseHTTPRequestHandler):
    """Mimics the noVNC example node: /health uses node/routes (not node_id/routes_count)."""

    def log_message(self, *_args):
        pass

    def do_GET(self):  # noqa: N802
        if self.path in ("/", "/health"):
            body = json.dumps({"ok": True, "node": "pc1", "selenium": "http://pc1-browser:4444", "routes": 6})
        elif self.path == "/routes":
            body = json.dumps({"ok": True, "node": "pc1", "routes": [
                {"uri": "browser://pc1/page/command/open", "kind": "command"},
                {"uri": "log://pc1/session/query/recent", "kind": "query"},
                {"uri": "app://pc1/notes/command/add", "kind": "command"},
            ]})
        else:
            self.send_response(404)
            self.end_headers()
            return
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def test_probe_tolerates_novnc_health_schema():
    """probe_urisys_node must normalise node->node_id and routes->routes_count."""
    httpd = HTTPServer(("127.0.0.1", 0), _NoVncHandler)
    host, port = httpd.server_address
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://{host}:{port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/health", timeout=1)
            break
        except Exception:
            time.sleep(0.05)
    try:
        node = probe_urisys_node(host, port, timeout=1.0)
        assert node is not None
        assert node["node_id"] == "pc1"       # mapped from "node"
        assert node["routes_count"] == 6        # mapped from "routes"
        routes = connectors.fetch_node_routes(base, timeout=2.0)["routes"]
        assert {r["scheme"] for r in routes} == {"browser", "log", "app"}
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_end_to_end_node_then_routes(remote_node):
    """The full app path: find the node, then enumerate its routes by scheme."""
    host, port = remote_node
    nodes = scan_urisys_nodes(timeout=1.5, port=port, scan_subnet=False, extra_hosts=[host])
    assert nodes, "node should be discovered"
    endpoint = nodes[0]["endpoint"]
    routes = connectors.fetch_node_routes(endpoint, timeout=2.0)["routes"]
    by_scheme = connectors.group_by_scheme(routes)
    # one route per discovered scheme, matching the node's advertised packs
    assert sorted(by_scheme) == ["a2a", "mcp", "sys"]
    assert sum(len(v) for v in by_scheme.values()) == 3
