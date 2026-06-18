"""Chat channels: each urisys-node :8790, MCP, A2A/agent, ifURI peer is a chat thread."""

from __future__ import annotations

import re
from typing import Any

from .chat_store import LocalChatStore
from .network_scan import scan_network
from .urisys_client import UrisysNodeClient, default_node_endpoint
from .voice_pipeline import plan_voice_command, run_voice_command
from .webrtc_signal import local_peer_url, webrtc_room_id

A2A_SCHEMES = frozenset({"agent", "a2a"})


def _channel_id(kind: str, key: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._:-]+", "-", key)[:120]
    return f"{kind}:{safe}"


def channels_from_scan(scan: dict[str, Any], *, local_api_url: str | None = None) -> list[dict[str, Any]]:
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
        peer_url = url.rstrip("/")
        out.append(
            {
                "id": _channel_id("ifuri", peer_url),
                "type": "ifuri",
                "kind": "ifuri",
                "title": name,
                "subtitle": peer_url,
                "peer_url": peer_url,
                "meta": {"schemes": peer.get("schemes") or []},
            }
        )
        if local_api_url and peer_url.rstrip("/") != local_api_url.rstrip("/"):
            room = webrtc_room_id(local_api_url, peer_url)
            out.append(
                {
                    "id": _channel_id("webrtc-peer", peer_url),
                    "type": "webrtc-peer",
                    "kind": "webrtc",
                    "title": f"{name} (WebRTC)",
                    "subtitle": peer_url,
                    "peer_url": peer_url,
                    "signaling_room": room,
                    "meta": {"local_url": local_api_url, "remote_url": peer_url},
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


def list_chat_channels(*, timeout: float = 1.5, scan_subnet: bool = True, local_host: str = "127.0.0.1", local_port: int = 8765) -> dict[str, Any]:
    scan = scan_network(timeout=timeout, scan_subnet=scan_subnet)
    local_api = local_peer_url(host=local_host, port=local_port)
    channels = channels_from_scan(scan, local_api_url=local_api)
    groups: dict[str, list[dict[str, Any]]] = {"node": [], "mcp": [], "a2a": [], "llm": [], "ifuri": [], "webrtc": []}
    for ch in channels:
        groups.setdefault(ch["kind"], []).append(ch)
    return {
        "ok": True,
        "scanned_at": scan.get("scanned_at"),
        "counts": scan.get("counts"),
        "local_api_url": local_api,
        "channels": channels,
        "groups": groups,
    }


def resolve_data_endpoint(
    *,
    router_endpoint: str | None = None,
    channel: dict[str, Any] | None = None,
) -> str | None:
    """urisys-node that stores app chat history for ifURI."""
    if router_endpoint:
        return router_endpoint.rstrip("/")
    if channel and str(channel.get("type") or "") == "urisys-node":
        ep = str(channel.get("endpoint") or "").strip()
        if ep:
            return ep.rstrip("/")
    try:
        from .storage import load_workspace

        ep = (load_workspace().get("urisys") or {}).get("endpoint")
        if ep:
            return str(ep).rstrip("/")
    except Exception:
        pass
    return default_node_endpoint().rstrip("/")


def _urisys_chat_unavailable(data: dict[str, Any]) -> bool:
    if data.get("ok"):
        return False
    err = str(data.get("error") or "").lower()
    typ = str(data.get("type") or "").lower()
    return "404" in err or "not found" in err or typ == "route_not_found"


def _local_chat_store() -> LocalChatStore:
    return LocalChatStore()


def fetch_chat_history(
    channel_id: str,
    *,
    router_endpoint: str | None = None,
    channel: dict[str, Any] | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    ep = resolve_data_endpoint(router_endpoint=router_endpoint, channel=channel)
    store = _local_chat_store()
    if ep:
        client = UrisysNodeClient(ep)
        data = client.app_chat_messages(channel_id, limit=limit)
        if data.get("ok"):
            data.setdefault("endpoint", ep)
            data["via"] = "urisys"
            return data
        if not _urisys_chat_unavailable(data):
            uri_data = client.call_uri(
                "app://local/chat/query/messages",
                {"channel_id": channel_id, "limit": limit},
                approved=True,
                dry_run=False,
            )
            result = uri_data.get("result") if isinstance(uri_data.get("result"), dict) else uri_data
            if isinstance(result, dict) and result.get("messages") is not None:
                return {
                    "ok": True,
                    "endpoint": ep,
                    "channel_id": channel_id,
                    "messages": result.get("messages") or [],
                    "count": len(result.get("messages") or []),
                    "via": "urisys-uri",
                }
    messages = store.list_messages(channel_id, limit=limit)
    return {
        "ok": True,
        "channel_id": channel_id,
        "messages": messages,
        "count": len(messages),
        "via": "local",
        "endpoint": ep,
        "note": "urisys-node bez /app/chat — historia lokalna (~/.ifuri/app-chat.jsonl)",
    }


def fetch_chat_channel_index(
    *,
    router_endpoint: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    ep = resolve_data_endpoint(router_endpoint=router_endpoint)
    store = _local_chat_store()
    local_channels = store.list_channels(limit=limit)
    if ep:
        client = UrisysNodeClient(ep)
        data = client.app_chat_channels(limit=limit)
        if data.get("ok"):
            data.setdefault("endpoint", ep)
            data["via"] = "urisys"
            return data
    return {
        "ok": True,
        "channels": local_channels,
        "count": len(local_channels),
        "via": "local",
        "endpoint": ep,
    }


def persist_chat_turn(
    channel_id: str,
    user_text: str,
    assistant_text: str,
    *,
    router_endpoint: str | None = None,
    channel: dict[str, Any] | None = None,
    reply_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ep = resolve_data_endpoint(router_endpoint=router_endpoint, channel=channel)
    store = _local_chat_store()
    if ep:
        client = UrisysNodeClient(ep)
        user_row = client.app_chat_append(channel_id, "user", user_text)
        asst_row = client.app_chat_append(
            channel_id,
            "assistant",
            assistant_text,
            meta=reply_meta or {},
        )
        if user_row.get("ok") and asst_row.get("ok"):
            return {"ok": True, "endpoint": ep, "saved": 2, "via": "urisys"}
        if not (_urisys_chat_unavailable(user_row) or _urisys_chat_unavailable(asst_row)):
            uri_user = client.call_uri(
                "app://local/chat/command/append",
                {"channel_id": channel_id, "role": "user", "text": user_text},
                approved=True,
                dry_run=False,
            )
            uri_asst = client.call_uri(
                "app://local/chat/command/append",
                {
                    "channel_id": channel_id,
                    "role": "assistant",
                    "text": assistant_text,
                    "meta": reply_meta or {},
                },
                approved=True,
                dry_run=False,
            )
            if uri_user.get("ok") and uri_asst.get("ok"):
                return {"ok": True, "endpoint": ep, "saved": 2, "via": "urisys-uri"}
    store.append(channel_id, "user", user_text)
    store.append(channel_id, "assistant", assistant_text, meta=reply_meta or {})
    return {"ok": True, "saved": 2, "via": "local", "endpoint": ep}


def urisys_chat_available(*, router_endpoint: str | None = None) -> dict[str, Any]:
    ep = resolve_data_endpoint(router_endpoint=router_endpoint)
    if not ep:
        return {"ok": False, "available": False, "error": "no urisys endpoint"}
    client = UrisysNodeClient(ep)
    probe = client.app_chat_messages("__ifuri_probe__", limit=1)
    available = bool(probe.get("ok")) and not _urisys_chat_unavailable(probe)
    return {"ok": True, "available": available, "endpoint": ep}


def migrate_local_chat_to_urisys(
    *,
    router_endpoint: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Upload ~/.ifuri/app-chat.jsonl to urisys-node when /app/chat is available."""
    check = urisys_chat_available(router_endpoint=router_endpoint)
    if not check.get("available"):
        return {
            **check,
            "ok": False,
            "error": "urisys-node lacks /app/chat/* — upgrade to urisys-node >= 0.1.15",
        }
    ep = check["endpoint"]
    client = UrisysNodeClient(ep)
    store = _local_chat_store()
    channels = store.list_channels()
    uploaded = 0
    skipped = 0
    details: list[dict[str, Any]] = []

    for ch in channels:
        cid = str(ch.get("channel_id") or "")
        if not cid:
            continue
        local_msgs = store.list_messages(cid, limit=500)
        if not local_msgs:
            continue
        if not force:
            remote = client.app_chat_messages(cid, limit=500)
            if remote.get("ok") and (remote.get("messages") or []):
                skipped += len(local_msgs)
                details.append({"channel_id": cid, "action": "skip", "remote_count": len(remote.get("messages") or [])})
                continue
        count = 0
        if not dry_run:
            for msg in local_msgs:
                client.app_chat_append(
                    cid,
                    str(msg.get("role") or "user"),
                    str(msg.get("text") or ""),
                    meta=msg.get("meta") if isinstance(msg.get("meta"), dict) else {},
                )
                count += 1
        else:
            count = len(local_msgs)
        uploaded += count
        details.append({"channel_id": cid, "action": "upload", "messages": count})

    return {
        "ok": True,
        "endpoint": ep,
        "dry_run": dry_run,
        "force": force,
        "channels": len(channels),
        "messages_uploaded": uploaded,
        "messages_skipped": skipped,
        "details": details,
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
    persist: bool = True,
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
        out = {
            "ok": bool(result.get("ok", True)),
            "channel": channel,
            "user_text": text,
            "reply": {"kind": "uri_call", "uri": uri, "body": result},
            "text": _format_json_reply(result),
            "router": router_endpoint,
        }
    else:
        out = send_chat_message(channel, text, dry_run=dry_run)

    if persist and out.get("ok"):
        channel_id = str(channel.get("id") or "")
        assistant_text = str(out.get("text") or out.get("error") or "")
        if channel_id and assistant_text:
            out["history"] = persist_chat_turn(
                channel_id,
                text,
                assistant_text,
                router_endpoint=router_endpoint,
                channel=channel,
                reply_meta={"reply": out.get("reply")},
            )
    return out


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
