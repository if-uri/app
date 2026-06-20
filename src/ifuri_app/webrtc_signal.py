# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""In-memory WebRTC signaling inbox (SDP / ICE relay between ifURI peers)."""

from __future__ import annotations

import threading
import time
from typing import Any

_MAX_SIGNALS_PER_ROOM = 500
_ROOM_TTL_S = 3600.0

_lock = threading.Lock()
_rooms: dict[str, dict[str, Any]] = {}


def local_peer_url(*, host: str = "127.0.0.1", port: int = 8765) -> str:
    """Best-effort LAN-reachable ifURI base URL for peer discovery."""
    if host not in {"", "0.0.0.0", "::"}:
        return f"http://{host}:{port}".rstrip("/")
    try:
        from .network_scan import _local_ipv4

        ip = _local_ipv4()
        if ip:
            return f"http://{ip}:{port}"
    except Exception:
        pass
    return f"http://127.0.0.1:{port}"


def webrtc_room_id(local_url: str, remote_url: str) -> str:
    a, b = sorted([local_url.rstrip("/"), remote_url.rstrip("/")])
    return f"webrtc-peer:{a}|{b}"


def is_webrtc_initiator(local_url: str, remote_url: str) -> bool:
    return local_url.rstrip("/") <= remote_url.rstrip("/")


def _purge_room(room: str, entry: dict[str, Any]) -> None:
    now = time.time()
    if now - float(entry.get("updated_at") or 0) > _ROOM_TTL_S:
        _rooms.pop(room, None)


def post_signal(
    room: str,
    *,
    from_peer: str,
    signal_type: str,
    data: Any,
) -> dict[str, Any]:
    room = (room or "").strip()
    from_peer = (from_peer or "").strip()
    signal_type = (signal_type or "").strip().lower()
    if not room or not from_peer or signal_type not in {"offer", "answer", "ice"}:
        return {"ok": False, "error": "room, from, and type (offer|answer|ice) required"}
    with _lock:
        entry = _rooms.setdefault(
            room,
            {"signals": [], "next_id": 1, "updated_at": time.time()},
        )
        _purge_room(room, entry)
        if room not in _rooms:
            return {"ok": False, "error": "room expired"}
        sig_id = int(entry["next_id"])
        entry["next_id"] = sig_id + 1
        row = {
            "id": sig_id,
            "room": room,
            "from": from_peer,
            "type": signal_type,
            "data": data,
            "at": time.time(),
        }
        entry["signals"].append(row)
        entry["updated_at"] = time.time()
        if len(entry["signals"]) > _MAX_SIGNALS_PER_ROOM:
            entry["signals"] = entry["signals"][-_MAX_SIGNALS_PER_ROOM :]
        return {"ok": True, "id": sig_id, "room": room}


def poll_signals(room: str, *, since: int = 0) -> dict[str, Any]:
    room = (room or "").strip()
    if not room:
        return {"ok": False, "error": "room required"}
    since = max(0, int(since or 0))
    with _lock:
        entry = _rooms.get(room)
        if not entry:
            return {"ok": True, "room": room, "signals": [], "since": since, "next": since}
        _purge_room(room, entry)
        entry = _rooms.get(room)
        if not entry:
            return {"ok": True, "room": room, "signals": [], "since": since, "next": since}
        pending = [s for s in entry["signals"] if int(s.get("id") or 0) > since]
        next_id = int(entry["signals"][-1]["id"]) if entry["signals"] else since
        return {"ok": True, "room": room, "signals": pending, "since": since, "next": next_id}


def room_stats() -> dict[str, Any]:
    with _lock:
        return {"ok": True, "rooms": len(_rooms), "room_ids": sorted(_rooms.keys())[:20]}
