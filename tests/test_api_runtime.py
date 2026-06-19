"""HTTP API smoke tests for ifURI runtime."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pytest

from ifuri_app.runtime import RuntimeServer, find_free_port


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    home = tmp_path_factory.mktemp("ifuri-home")
    os.environ["IFURI_HOME"] = str(home)
    os.environ["IFURI_CHAT_STORE"] = str(home / "app-chat.jsonl")
    port = find_free_port("127.0.0.1", 18765, attempts=20)
    srv = RuntimeServer("127.0.0.1", port).start()
    yield srv
    srv.stop()


def _get(url: str) -> tuple[int, dict]:
    with urllib.request.urlopen(url, timeout=15) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body) if body else {}


def _post(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body) if body else {}


def test_health(server):
    status, data = _get(f"{server.url}/api/health")
    assert status == 200
    assert data.get("ok") is True
    assert data.get("name") == "ifURI runtime"


def test_voice_page(server):
    req = urllib.request.Request(f"{server.url}/voice")
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8")
    assert resp.status == 200
    assert "ifURI" in html
    assert "/web/voice.js" in html


def test_static_assets(server):
    for asset in ("url_state.js", "i18n.js", "voice.js", "voice.css", "page_runtime.js"):
        with urllib.request.urlopen(f"{server.url}/web/{asset}", timeout=10) as resp:
            assert resp.status == 200
            assert resp.read()


def test_api_packs(server):
    status, data = _get(f"{server.url}/api/packs")
    assert status == 200
    assert data.get("ok") is True
    assert isinstance(data.get("packs"), list)
    assert len(data.get("packs") or []) >= 3
    assert "runtime" in data


def test_api_urirun_status(server):
    status, data = _get(f"{server.url}/api/urirun")
    assert status == 200
    assert data.get("package") == "urirun"
    assert "available" in data


def test_api_urirun_call_contract(server):
    status, data = _post(
        f"{server.url}/api/urirun/call",
        {
            "uri": "tool://local/report/render",
            "payload": {"format": "html"},
            "execute": False,
        },
    )
    assert status == 200
    assert data.get("via") == "urirun"
    assert data.get("uri") == "tool://local/report/render"


def test_api_urirun_call_local_registry_execute(server, tmp_path):
    pytest.importorskip("urirun")
    import urirun.v2 as v2

    registry = v2.compile_registry(
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
    )
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    status, data = _post(
        f"{server.url}/api/urirun/call",
        {
            "uri": "util://local/echo/say",
            "payload": {"text": "hello-from-api"},
            "registry": str(registry_path),
            "execute": True,
        },
    )
    assert status == 200
    assert data.get("ok") is True
    assert data.get("via") == "urirun"
    assert data.get("mode") == "execute"
    assert (data.get("result") or {}).get("stdout", "").strip() == "hello-from-api"


def test_uri_call_voice_plan(server):
    status, data = _post(
        f"{server.url}/api/uri/call",
        {
            "uri": "voice://local/query/plan",
            "payload": {"text": "health"},
            "dry_run": False,
            "approved": True,
        },
    )
    if status != 200:
        return
    if data.get("via") == "uricore-local":
        assert data.get("ok") is True


def test_flow_validate(server):
    flow_text = "do:\n  - screen://local/monitor/1/query/frame"
    status, data = _post(f"{server.url}/api/flow/validate", {"flow_text": flow_text})
    assert status == 200
    assert data.get("ok") is True


def test_flow_expand(server):
    flow_text = "do:\n  - kv://session/key/x/query/get\n  - screen://local/monitor/1/query/frame"
    status, data = _post(f"{server.url}/api/flow/expand", {"flow_text": flow_text})
    assert status == 200
    assert data.get("ok") is True
    nodes = (data.get("workflow_graph") or {}).get("nodes") or []
    assert len(nodes) >= 2


def test_flow_expand_missing_text(server):
    try:
        _post(f"{server.url}/api/flow/expand", {"flow_text": "  "})
        assert False, "expected 400"
    except urllib.error.HTTPError as exc:
        assert exc.code == 400
        body = json.loads(exc.read().decode("utf-8"))
        assert body.get("ok") is False


def test_chat_channels(server):
    status, data = _get(f"{server.url}/api/chat/channels?timeout=0.5")
    assert status == 200
    assert data.get("ok") is True
    assert "channels" in data


def test_chat_history(server):
    status, data = _get(f"{server.url}/api/chat/history?channel_id=test-api")
    assert status == 200
    assert data.get("ok") is True
    assert isinstance(data.get("messages"), list)


def test_network_scan(server):
    status, data = _get(f"{server.url}/api/network/scan?timeout=0.5")
    assert status == 200
    assert "counts" in data


def test_voice_plan(server):
    status, data = _post(f"{server.url}/api/voice/plan", {"text": "health"})
    assert status == 200
    assert "flow_ref" in data or "message" in data or data.get("ok") is not None


def test_chat_send_empty(server):
    status, data = _post(
        f"{server.url}/api/chat/send",
        {"channel": {"type": "urisys-node", "id": "x", "endpoint": "http://127.0.0.1:8790"}, "text": "  "},
    )
    assert status == 200
    assert data.get("ok") is False


def test_concurrent_health(server):
    """Regression: parallel requests must not crash on workspace save."""
    url = f"{server.url}/api/health"

    def hit() -> bool:
        status, data = _get(url)
        return status == 200 and data.get("ok") is True

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: hit(), range(24)))
    assert all(results)


def test_not_found(server):
    try:
        _get(f"{server.url}/api/no-such-endpoint")
        assert False, "expected 404"
    except urllib.error.HTTPError as exc:
        assert exc.code == 404
        body = json.loads(exc.read().decode("utf-8"))
        assert body.get("error") == "not_found"


def test_webrtc_signal_api(server):
    room = "webrtc-peer:smoke"
    status, posted = _post(
        f"{server.url}/api/webrtc/signal",
        {"room": room, "from": "http://127.0.0.1:8766", "type": "offer", "data": {"sdp": "v=0"}},
    )
    assert status == 200
    assert posted.get("ok") is True
    status, inbox = _get(f"{server.url}/api/webrtc/signal?room={room}&since=0")
    assert status == 200
    assert inbox.get("ok") is True
    assert len(inbox.get("signals") or []) == 1
