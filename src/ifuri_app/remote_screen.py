# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Remote screen capture via urisys-node screen:// / kvm://."""

from __future__ import annotations

import base64
import binascii
import os
from typing import Any

from .urisys_client import UrisysNodeClient

DEFAULT_NODE_ID = "local"


def resolve_node_id(client: UrisysNodeClient | None = None, node_id: str | None = None) -> str:
    """Resolve the target node without baking in a lab machine name.

    Order: explicit payload/query -> env/config -> node /health -> neutral local target.
    """
    explicit = str(node_id or "").strip()
    if explicit:
        return explicit
    for key in ("IFURI_DEFAULT_NODE_ID", "URISYS_NODE_ID"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    if client is not None:
        try:
            health = client.health()
        except Exception:  # noqa: BLE001 - best-effort metadata probe
            health = {}
        for key in ("node_id", "node", "name"):
            value = str(health.get(key) or "").strip()
            if value:
                return value
    return DEFAULT_NODE_ID


def unwrap_result(response: dict[str, Any]) -> dict[str, Any]:
    """Normalize /uri/call body to the inner handler result."""
    if not isinstance(response, dict):
        return {}
    inner = response.get("result")
    if isinstance(inner, dict):
        if "result" in inner and isinstance(inner["result"], dict):
            return inner["result"]
        return inner
    return response


def screen_uri(*, node_id: str = DEFAULT_NODE_ID, monitor: int = 1, source: str = "screen") -> str:
    if source == "kvm":
        return f"kvm://{node_id}/monitor/primary/query/screenshot"
    return f"screen://{node_id}/monitor/{monitor}/query/frame"


def capture_remote_screen(
    client: UrisysNodeClient | None = None,
    *,
    node_id: str | None = None,
    monitor: int = 1,
    source: str = "screen",
) -> dict[str, Any]:
    """Capture PNG from remote node. Returns ok, png bytes, metadata."""
    node = client or UrisysNodeClient()
    node_id = resolve_node_id(node, node_id)
    uri = screen_uri(node_id=node_id, monitor=monitor, source=source)
    raw = node.call_uri(uri, {}, approved=True, allow_real=True)
    if not raw.get("ok", True) and raw.get("error"):
        return {"ok": False, "endpoint": node.endpoint, "uri": uri, "error": raw.get("error"), "response": raw}
    result = unwrap_result(raw)
    if result.get("error"):
        return {"ok": False, "endpoint": node.endpoint, "uri": uri, "error": result.get("error"), "response": raw}
    b64 = result.get("base64") or result.get("png_b64") or result.get("image_b64")
    if not b64:
        return {
            "ok": False,
            "endpoint": node.endpoint,
            "uri": uri,
            "error": "no base64 image in response",
            "response": raw,
        }
    try:
        png = base64.b64decode(b64, validate=False)
    except (binascii.Error, ValueError) as exc:
        return {"ok": False, "endpoint": node.endpoint, "uri": uri, "error": str(exc), "response": raw}
    return {
        "ok": True,
        "endpoint": node.endpoint,
        "uri": uri,
        "png": png,
        "width": result.get("width"),
        "height": result.get("height"),
        "backend": result.get("backend") or result.get("backend_used") or result.get("driver"),
        "monitor": result.get("monitor", monitor),
        "mime": result.get("mime", "image/png"),
        "captured_at": result.get("path"),
    }


def probe_remote_control(client: UrisysNodeClient | None = None, *, node_id: str | None = None) -> dict[str, Any]:
    """Quick check: health + screen capture (+ kvm if routes exist)."""
    node = client or UrisysNodeClient()
    node_id = resolve_node_id(node, node_id)
    out: dict[str, Any] = {"ok": False, "endpoint": node.endpoint, "node_id": node_id, "checks": {}}

    health = node.health()
    out["checks"]["health"] = {"ok": bool(health.get("ok")), "detail": health}
    if not health.get("ok"):
        out["error"] = health.get("error") or "node unreachable"
        return out

    packs = set(health.get("packs_loaded") or [])
    out["packs_loaded"] = sorted(packs)
    out["him_driver"] = health.get("him_driver")

    screen = capture_remote_screen(node, node_id=node_id, source="screen")
    out["checks"]["screen"] = {
        "ok": bool(screen.get("ok")),
        "width": screen.get("width"),
        "height": screen.get("height"),
        "backend": screen.get("backend"),
        "error": screen.get("error"),
    }

    kvm_check: dict[str, Any] = {"ok": False, "skipped": "kvm pack not loaded"}
    if "kvm" in packs:
        kvm = capture_remote_screen(node, node_id=node_id, source="kvm")
        kvm_check = {
            "ok": bool(kvm.get("ok")),
            "width": kvm.get("width"),
            "height": kvm.get("height"),
            "backend": kvm.get("backend"),
            "error": kvm.get("error"),
        }
    out["checks"]["kvm"] = kvm_check

    kv_ok = "kv" in packs
    out["checks"]["kv"] = {"ok": kv_ok, "loaded": kv_ok}

    out["ok"] = bool(out["checks"]["health"]["ok"]) and bool(out["checks"]["screen"]["ok"])
    return out
