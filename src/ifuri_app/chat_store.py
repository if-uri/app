# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Local chat history when urisys-node has no /app/chat/* endpoints."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import app_home, ensure_home


def chat_store_path() -> Path:
    override = __import__("os").environ.get("IFURI_CHAT_STORE")
    if override:
        return Path(override).expanduser().resolve()
    return app_home() / "app-chat.jsonl"


class LocalChatStore:
    def __init__(self, path: Path | None = None):
        self.path = path or chat_store_path()
        ensure_home()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        channel_id: str,
        role: str,
        text: str,
        *,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = {
            "message_id": str(uuid.uuid4()),
            "channel_id": channel_id,
            "role": role,
            "text": text,
            "meta": meta or {},
            "at": datetime.now(timezone.utc).isoformat(),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def list_messages(self, channel_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        if not channel_id or not self.path.exists():
            return []
        limit = max(1, min(int(limit), 500))
        matched: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("channel_id") == channel_id:
                matched.append(row)
        return matched[-limit:]

    def list_channels(self, *, limit: int = 100) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        limit = max(1, min(int(limit), 500))
        by_id: dict[str, dict[str, Any]] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            cid = row.get("channel_id")
            if not cid:
                continue
            cid = str(cid)
            by_id[cid] = {
                "channel_id": cid,
                "last_at": row.get("at"),
                "last_role": row.get("role"),
                "preview": str(row.get("text") or "")[:120],
                "message_count": int(by_id.get(cid, {}).get("message_count") or 0) + 1,
            }
        items = sorted(by_id.values(), key=lambda x: x.get("last_at") or "", reverse=True)
        return items[:limit]
