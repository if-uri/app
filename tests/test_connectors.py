"""Unit tests for ifuri_app.connectors route normalisation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ifuri_app import connectors as c  # noqa: E402


def test_route_scheme_variants():
    assert c.route_scheme("sys://local/echo/hello") == "sys"
    assert c.route_scheme("MCP://fs/list") == "mcp"
    assert c.route_scheme("a2a:agent/plan") == "a2a"
    assert c.route_scheme("") == "other"
    assert c.route_scheme("noscheme") == "other"


def test_normalize_list_of_dicts():
    payload = {
        "ok": True,
        "routes": [
            {"uri": "sys://local/echo", "kind": "command", "adapter": "argv-template", "argv": ["echo", "hi"]},
            {"uri": "mcp://fs/list", "kind": "mcp"},
        ],
    }
    rows = c.normalize_routes(payload)
    assert [r["uri"] for r in rows] == ["mcp://fs/list", "sys://local/echo"]  # sorted by scheme
    echo = next(r for r in rows if r["scheme"] == "sys")
    assert echo["kind"] == "command"
    assert echo["adapter"] == "argv-template"
    assert echo["detail"] == "echo hi"


def test_normalize_dict_of_bindings():
    payload = {
        "routes": {
            "sys://local/echo": {"kind": "command", "adapter": "argv-template", "argv": ["echo", "x"]},
        }
    }
    rows = c.normalize_routes(payload)
    assert len(rows) == 1
    assert rows[0]["scheme"] == "sys"
    assert rows[0]["detail"] == "echo x"


def test_normalize_list_of_strings_and_bare_list():
    rows = c.normalize_routes(["sys://a/b", "mcp://c/d"])
    assert {r["scheme"] for r in rows} == {"sys", "mcp"}
    assert all(r["kind"] == "" for r in rows)


def test_normalize_alternate_uri_keys_and_dedup():
    payload = {"routes": [{"pattern": "sys://a"}, {"uri": "sys://a"}, {"route": "mcp://b"}]}
    rows = c.normalize_routes(payload)
    uris = [r["uri"] for r in rows]
    assert uris == ["mcp://b", "sys://a"]  # deduped + sorted


def test_normalize_ignores_entries_without_uri():
    rows = c.normalize_routes({"routes": [{"kind": "command"}, {}, "sys://ok"]})
    assert [r["uri"] for r in rows] == ["sys://ok"]


def test_group_by_scheme():
    rows = c.normalize_routes(["sys://a", "sys://b", "mcp://c"])
    grouped = c.group_by_scheme(rows)
    assert sorted(grouped) == ["mcp", "sys"]
    assert len(grouped["sys"]) == 2


def test_fetch_node_routes_handles_unreachable():
    # nothing listening on this port → ok False, error populated, never raises
    out = c.fetch_node_routes("http://127.0.0.1:1", timeout=0.2)
    assert out["ok"] is False
    assert out["routes"] == []
    assert out["error"]
    assert out["endpoint"] == "http://127.0.0.1:1"
