# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Local JSONL chat store queries (fallback when urisys-node lacks /app/chat)."""

from __future__ import annotations

from typing import Any


def list_messages(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    channel_id = str(payload.get("channel_id") or "default")
    limit = int(payload.get("limit") or 200)
    try:
        from ifuri_app.chat_store import LocalChatStore

        store = LocalChatStore()
        messages = store.list_messages(channel_id, limit=limit)
        return {"ok": True, "channel_id": channel_id, "messages": messages, "via": "local"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def list_channels(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    try:
        from ifuri_app.chat_store import LocalChatStore

        store = LocalChatStore()
        channels = store.list_channels()
        return {"ok": True, "channels": channels, "via": "local"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
