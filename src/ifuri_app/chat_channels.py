"""Chat channels: each urisys-node :8790, MCP, A2A/agent, ifURI peer is a chat thread."""

from __future__ import annotations

import re
from typing import Any

from .network_scan import scan_network
from .urisys_client import UrisysNodeClient
from .voice_pipeline import plan_voice_command, run_voice_command

A2A_SCHEMES = frozenset({"agent", "a2a"})


def _channel_id(kind: str, key: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._:-]+", "-", key)[:120]
    return f"{kind}:{safe}"


def channels_from_scan(scan: dict[str, Any]) -> list[dict[str, Any]]:
    """Build chat channel list from network scan payload."""
    out: list[dict[str, Any]] = []

    for node in scan.get("urisys_nodes") or []:
        endpoint = str(node.get("endpoint") or "")
        if not endpoint:
            continue
        node_id = str(node.get("node_id") or node.get("host") or "node")
        out.append(
            {
                "id": _channel_id("urisys-node", endpoint),
                "type": "urisys-node",
                "kind": "node",
                "title": node_id,
                "subtitle": f"{endpoint} · {node.get('routes_count', '?')} routes",
                "endpoint": endpoint,
                "node_id": node_id,
                "meta": {
                    "him_driver": node.get("him_driver"),
                    "packs_loaded": node.get("packs_loaded") or [],
                },
            }
        )

    for peer in scan.get("ifuri_peers") or []:
        url = peer.get("api_url") or (
            f"http://{peer.get('address')}:{peer.get('api_port', 8765)}" if peer.get("address") else ""
        )
        if not url:
            continue
        name = str(peer.get("name") or peer.get("id") or peer.get("address") or "ifURI")
        out.append(
            {
                "id": _channel_id("ifuri", url),
                "type": "ifuri",
                "kind": "ifuri",
                "title": name,
                "subtitle": url,
                "peer_url": url.rstrip("/"),
                "meta": {"schemes": peer.get("schemes") or []},
            }
        )

    for svc in (scan.get("services") or []) + (scan.get("mcp_agent_services") or []) + (scan.get("llm_services") or []):
        uri = str(svc.get("uri") or "")
        if not uri or "://" not in uri:
            continue
        scheme = str(svc.get("scheme") or uri.split("://", 1)[0]).lower()
        if scheme == "mcp":
            kind = "mcp"
        elif scheme in A2A_SCHEMES or scheme == "agent":
            kind = "a2a"
        elif scheme == "llm":
            kind = "llm"
        else:
            continue
        name = str(svc.get("name") or uri)
        out.append(
            {
                "id": _channel_id(kind, uri),
                "type": kind,
                "kind": kind,
                "title": name,
                "subtitle": f"{uri} · {svc.get('source', 'local')}",
                "uri": uri,
                "meta": {"scope": svc.get("scope"), "source": svc.get("source"), "peer_url": svc.get("peer_url")},
            }
        )

    # Dedupe by id preserving order
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for ch in out:
        if ch["id"] in seen:
            continue
        seen.add(ch["id"])
        deduped.append(ch)
    return deduped


def list_chat_channels(*, timeout: float = 1.5, scan_subnet: bool = True) -> dict[str, Any]:
    scan = scan_network(timeout=timeout, scan_subnet=scan_subnet)
    channels = channels_from_scan(scan)
    groups: dict[str, list[dict[str, Any]]] = {"node": [], "mcp": [], "a2a": [], "llm": [], "ifuri": []}
    for ch in channels:
        groups.setdefault(ch["kind"], []).append(ch)
    return {
        "ok": True,
        "scanned_at": scan.get("scanned_at"),
        "counts": scan.get("counts"),
        "channels": channels,
        "groups": groups,
    }


def send_chat_message(
    channel: dict[str, Any],
    text: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty message"}

    ctype = str(channel.get("type") or channel.get("kind") or "")
    out: dict[str, Any] = {"ok": True, "channel": channel, "user_text": text, "reply": None}

    if ctype == "urisys-node":
        endpoint = str(channel.get("endpoint") or "")
        client = UrisysNodeClient(endpoint or None)
        if text.lower() in {"/health", "health", "status"}:
            health = client.health()
            out["reply"] = {"kind": "health", "body": health}
            out["text"] = _format_json_reply(health)
            return out
        result = run_voice_command(text, client=client, dry_run=dry_run, speak=not dry_run)
        out["reply"] = {"kind": "voice", "body": result}
        out["text"] = _format_voice_reply(result)
        return out

    if ctype == "ifuri":
        import json
        import urllib.error
        import urllib.request

        peer = str(channel.get("peer_url") or "").rstrip("/")
        if not peer:
            return {"ok": False, "error": "missing peer_url"}
        body = json.dumps({"text": text, "dry_run": dry_run, "speak": False}).encode("utf-8")
        req = urllib.request.Request(
            f"{peer}/api/voice/run",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            data = {"ok": False, "error": f"HTTP {exc.code}", "detail": exc.read().decode("utf-8", errors="replace")}
        except Exception as exc:
            data = {"ok": False, "error": str(exc)}
        out["reply"] = {"kind": "peer", "body": data}
        out["text"] = _format_json_reply(data)
        return out

    uri = str(channel.get("uri") or "")
    if not uri:
        return {"ok": False, "error": "missing uri for service channel"}

    payload = _payload_for_scheme(ctype, text)
    if ctype in {"mcp", "a2a", "llm", "agent"}:
        # Local dry-run envelope via flow engine path — real calls need urisys-node or adapter
        plan = plan_voice_command(text)
        out["reply"] = {
            "kind": ctype,
            "uri": uri,
            "payload": payload,
            "plan": plan,
            "note": "URI call envelope — wire to /api/urisys/call when node channel selected as router",
        }
        out["text"] = (
            f"→ {uri}\n"
            f"payload: {_short_json(payload)}\n\n"
            f"{plan.get('message') or ''}".strip()
        )
        return out

    return {"ok": False, "error": f"unsupported channel type: {ctype}"}


def send_chat_message_routed(
    channel: dict[str, Any],
    text: str,
    *,
    router_endpoint: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Send message; MCP/A2A/LLM routed through urisys-node when endpoint available."""
    ctype = str(channel.get("type") or channel.get("kind") or "")
    if not router_endpoint:
        try:
            from .storage import load_workspace

            ep = (load_workspace().get("urisys") or {}).get("endpoint")
            router_endpoint = str(ep).rstrip("/") if ep else None
        except Exception:
            router_endpoint = None
    if ctype in {"mcp", "a2a", "llm", "agent"} and router_endpoint:
        uri = str(channel.get("uri") or "")
        payload = _payload_for_scheme(ctype, text)
        client = UrisysNodeClient(router_endpoint)
        result = client.call_uri(uri, payload, approved=True, allow_real=not dry_run, dry_run=dry_run)
        return {
            "ok": bool(result.get("ok", True)),
            "channel": channel,
            "user_text": text,
            "reply": {"kind": "uri_call", "uri": uri, "body": result},
            "text": _format_json_reply(result),
            "router": router_endpoint,
        }
    return send_chat_message(channel, text, dry_run=dry_run)


def _payload_for_scheme(kind: str, text: str) -> dict[str, Any]:
    if kind == "mcp":
        return {"query": text, "text": text}
    if kind in {"a2a", "agent"}:
        return {"message": text, "text": text, "input": text}
    if kind == "llm":
        return {"prompt": text, "text": text}
    return {"text": text}


def _short_json(obj: Any, limit: int = 800) -> str:
    import json

    s = json.dumps(obj, ensure_ascii=False, indent=2)
    return s if len(s) <= limit else s[: limit - 3] + "..."


def _format_json_reply(data: Any) -> str:
    import json

    return json.dumps(data, ensure_ascii=False, indent=2)


def _format_voice_reply(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return result.get("error") or _format_json_reply(result)
    parts: list[str] = []
    plan = result.get("plan") or {}
    if plan.get("flow_ref"):
        parts.append(f"Flow: {plan['flow_ref']}")
    flow = result.get("flow")
    if isinstance(flow, dict):
        steps = flow.get("steps") or []
        if steps:
            parts.append(f"Steps: {len(steps)}")
            for i, step in enumerate(steps[:5], 1):
                resp = step.get("response") if isinstance(step, dict) else step
                ok = resp.get("ok") if isinstance(resp, dict) else None
                parts.append(f"  {i}. {'OK' if ok else '…'} {step.get('uri') or step.get('step') or ''}")
    hint = result.get("connection_hint")
    if hint:
        parts.append(hint)
    if not parts:
        return _format_json_reply(result)
    return "\n".join(parts)
