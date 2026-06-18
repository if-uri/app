"""WebRTC pack install and smoke on urisys-node (phase 1: uriwebrtc mock)."""

from __future__ import annotations

import os
from typing import Any

from .flow_runner import run_flow_file
from .urisys_client import UrisysNodeClient, node_webrtc_available
from .voice_pipeline import VOICE_STT_WHEEL

WEBRTC_PACKS_FLOW = "lenovo-remote/02c-install-webrtc-pack.uri.flow.yaml"
WEBRTC_WHEEL = os.environ.get(
    "URISYS_WEBRTC_WHEEL",
    f"{os.environ.get('URISYS_WHEEL_HOST', 'http://192.168.188.212:8765')}/uriwebrtc-0.1.0-py3-none-any.whl",
)

__all__ = [
    "WEBRTC_PACKS_FLOW",
    "install_webrtc_pack",
    "webrtc_capabilities",
    "webrtc_pack_install_hint",
    "webrtc_smoke",
]


def webrtc_capabilities(client: UrisysNodeClient | None = None) -> dict[str, Any]:
    node = client or UrisysNodeClient()
    available = node_webrtc_available(node)
    hint = webrtc_pack_install_hint(node)
    return {
        "ok": True,
        "endpoint": node.endpoint,
        "webrtc": available,
        "webrtc_pack_hint": hint,
    }


def install_webrtc_pack(
    *,
    client: UrisysNodeClient | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    node = client or UrisysNodeClient()
    hint = webrtc_pack_install_hint(node)
    if not hint.get("needed"):
        return {
            "ok": True,
            "skipped": True,
            "message": "webrtc pack already available",
            "webrtc": True,
        }
    result = run_flow_file(WEBRTC_PACKS_FLOW, client=node, dry_run=dry_run, approved=True, allow_real=not dry_run)
    if not dry_run and not result.get("ok"):
        health = node.health()
        target = str(health.get("node_id") or "local")
        direct = node.call_uri(
            f"node://{target}/command/install-pack",
            {"pack": "webrtc", "install": True, "force": True, "specs": [WEBRTC_WHEEL]},
            dry_run=False,
        )
        result = {
            "ok": bool((direct.get("result") or direct).get("ok", direct.get("ok"))),
            "fallback": "direct-install-pack",
            "direct": direct,
            "flow": result,
        }
    available = node_webrtc_available(node)
    return {
        "ok": bool(result.get("ok")) and available,
        "dry_run": dry_run,
        "flow": WEBRTC_PACKS_FLOW,
        "endpoint": node.endpoint,
        "result": result,
        "webrtc": available,
        "webrtc_pack_hint": webrtc_pack_install_hint(node),
    }


def webrtc_smoke(*, client: UrisysNodeClient | None = None) -> dict[str, Any]:
    node = client or UrisysNodeClient()
    if not node_webrtc_available(node):
        return {"ok": False, "error": "webrtc pack not loaded", "endpoint": node.endpoint}
    start = node.call_uri(
        "webrtc://local/session/rdp-chat/command/start",
        {"room": "rdp-lab"},
        dry_run=False,
    )
    send = node.call_uri(
        "webrtc://local/session/rdp-chat/data/command/send",
        {"envelope": {"uri": "kvm://local/monitor/primary/query/screenshot", "payload": {}}},
        dry_run=False,
    )
    signal = node.call_uri(
        "webrtc://local/session/rdp-chat/signal/command/post",
        {"room": "rdp-chat", "from": "http://ifuri/smoke", "type": "offer", "data": {"type": "offer", "sdp": "v=0"}},
        dry_run=False,
    )
    inbox = node.call_uri(
        "webrtc://local/session/rdp-chat/signal/query/inbox",
        {"room": "rdp-chat", "since": 0},
        dry_run=False,
    )
    ok = (
        bool(start.get("ok"))
        and bool(send.get("ok"))
        and bool(signal.get("ok"))
        and bool(inbox.get("ok"))
    )
    return {
        "ok": ok,
        "endpoint": node.endpoint,
        "start": start,
        "send": send,
        "signal": signal,
        "inbox": inbox,
    }


def webrtc_pack_install_hint(client: UrisysNodeClient) -> dict[str, Any]:
    if node_webrtc_available(client):
        return {"needed": False}
    return {
        "needed": True,
        "endpoint": client.endpoint,
        "flow_ref": WEBRTC_PACKS_FLOW,
        "cli": f"ifuri-app webrtc-install-pack --endpoint {client.endpoint}",
        "message": "Install webrtc pack on urisys-node (flow 02c-install-webrtc-pack)",
    }
