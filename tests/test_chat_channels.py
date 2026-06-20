# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Tests for chat channel builder."""

from __future__ import annotations

from ifuri_app.chat_channels import channels_from_scan, send_chat_message


def test_channels_from_scan_groups_endpoints():
    scan = {
        "urisys_nodes": [
            {"endpoint": "http://192.168.1.10:8790", "node_id": "lenovo", "routes_count": 12},
        ],
        "ifuri_peers": [
            {"name": "desk", "api_url": "http://192.168.1.20:8765", "schemes": ["mcp"]},
        ],
        "services": [
            {"scheme": "mcp", "name": "fs", "uri": "mcp://filesystem/list", "source": "local"},
            {"scheme": "a2a", "name": "reviewer", "uri": "a2a://code-reviewer/run", "source": "local"},
        ],
        "mcp_agent_services": [],
        "llm_services": [{"scheme": "llm", "name": "qwen", "uri": "llm://local/qwen/analyze", "source": "local"}],
    }
    channels = channels_from_scan(scan, local_api_url="http://192.168.1.10:8766")
    kinds = {c["kind"] for c in channels}
    assert "node" in kinds
    assert "mcp" in kinds
    assert "a2a" in kinds
    assert "ifuri" in kinds
    assert "webrtc" in kinds
    assert any(c["endpoint"] == "http://192.168.1.10:8790" for c in channels)
    assert any(c.get("type") == "webrtc-peer" for c in channels)


def test_send_empty_message():
    assert send_chat_message({"type": "urisys-node", "endpoint": "http://127.0.0.1:8790"}, "  ")["ok"] is False
