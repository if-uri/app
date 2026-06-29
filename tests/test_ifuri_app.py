# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Tests for ifURI urisys integration."""

from __future__ import annotations

from unittest.mock import patch

from ifuri_app.flow_engine import expand_flow
from ifuri_app.network_scan import scan_network
from ifuri_app.remote_screen import unwrap_result, screen_uri, capture_remote_screen, resolve_node_id
from ifuri_app.urisys_client import node_voice_capabilities
from ifuri_app.voice_pipeline import plan_voice_command, _connection_hint


def test_plan_linkedin_flow():
    plan = plan_voice_command("otwórz linkedin i napisz post")
    assert plan["ok"]
    assert plan["plan"] == "flow"
    assert "08-kvm-linkedin" in plan["flow_ref"]


def test_plan_health_flow():
    plan = plan_voice_command("sprawdź health node")
    assert plan["ok"]
    assert plan["plan"] == "flow"
    assert "01-health-probe" in plan["flow_ref"]


def test_plan_voice_fallback():
    plan = plan_voice_command("zrób coś zupełnie innego xyz")
    assert plan["ok"]
    assert plan["plan"] == "uri"
    assert plan["uri"].startswith("voice://")


def test_expand_flow_extracts_uris():
    text = "do:\n  - kv://session/key/x/query/get\n  - screen://local/monitor/1/query/frame"
    graph = expand_flow(text)
    nodes = graph["workflow_graph"]["nodes"]
    uris = [n["uri"] for n in nodes]
    assert any(u.startswith("kv://") for u in uris)
    assert any(u.startswith("screen://") for u in uris)
    if graph.get("compiler") == "uri2flow":
        assert graph.get("graph")


def test_scan_network_structure():
    fake_peers = [{"id": "p1", "name": "desk", "address": "192.168.1.10", "api_port": 8765, "schemes": ["mcp"]}]
    fake_nodes = [{"endpoint": "http://192.168.1.20:8790", "host": "192.168.1.20", "node_id": "lenovo", "routes_count": 12}]
    with (
        patch("ifuri_app.network_scan.discover", return_value=fake_peers),
        patch("ifuri_app.network_scan.scan_urisys_nodes", return_value=fake_nodes),
        patch("ifuri_app.network_scan.probe_urisys_node", return_value=None),
        patch("ifuri_app.network_scan.probe_ifuri_peer", return_value=None),
        patch("ifuri_app.network_scan.try_mdns_urisys", return_value=[]),
        patch("ifuri_app.network_scan._collect_local_services", return_value=[{"scheme": "mcp", "name": "fs", "uri": "mcp://filesystem/list", "source": "local"}]),
    ):
        result = scan_network(timeout=0.5, scan_subnet=False)

    assert result["ok"]
    assert len(result["ifuri_peers"]) == 1
    assert len(result["urisys_nodes"]) == 1
    assert result["counts"]["ifuri_peers"] == 1
    assert result["counts"]["urisys_nodes"] == 1
    assert any(s["scheme"] == "mcp" for s in result["mcp_agent_services"])


def test_node_voice_capabilities_without_voice_packs():
    class FakeClient:
        endpoint = "http://127.0.0.1:8790"

        def health(self):
            return {"ok": True, "packs_loaded": ["browser", "kvm", "him"], "routes_count": 52}

    caps = node_voice_capabilities(FakeClient())
    assert caps["reachable"]
    assert caps["stt"] is False
    assert caps["tts"] is False


def test_node_voice_capabilities_with_stt_pack():
    class FakeClient:
        endpoint = "http://192.168.188.201:8790"

        def health(self):
            return {"ok": True, "packs_loaded": ["browser", "stt"], "routes_count": 55}

    caps = node_voice_capabilities(FakeClient())
    assert caps["stt"] is True
    assert caps["tts"] is True


def test_screen_uri():
    assert "screen://lenovo/monitor/1" in screen_uri(node_id="lenovo", monitor=1)
    assert screen_uri(source="kvm").startswith("kvm://")


def test_resolve_node_id_order(monkeypatch):
    class FakeClient:
        def health(self):
            return {"ok": True, "node_id": "from-health"}

    assert resolve_node_id(FakeClient(), "explicit") == "explicit"
    monkeypatch.setenv("IFURI_DEFAULT_NODE_ID", "from-env")
    assert resolve_node_id(FakeClient(), "") == "from-env"
    monkeypatch.delenv("IFURI_DEFAULT_NODE_ID")
    assert resolve_node_id(FakeClient(), "") == "from-health"
    assert resolve_node_id(None, "") == "local"


def test_unwrap_result_nested():
    data = {"ok": True, "result": {"result": {"width": 100, "base64": "abc"}}}
    assert unwrap_result(data)["width"] == 100


def test_capture_remote_screen_mock():
    class FakeClient:
        endpoint = "http://test:8790"

        def call_uri(self, uri, payload, **kwargs):
            return {"ok": True, "result": {"width": 800, "height": 600, "base64": "aGVsbG8="}}

    out = capture_remote_screen(FakeClient())
    assert out["ok"]
    assert out["png"] == b"hello"


def test_connection_hint_on_refused():
    hint = _connection_hint(
        {
            "flow": {
                "steps": [
                    {"response": {"ok": False, "error": "<urlopen error [Errno 111] Connection refused>"}}
                ]
            }
        },
        "http://127.0.0.1:8790",
    )
    assert hint
    assert "127.0.0.1:8790" in hint
