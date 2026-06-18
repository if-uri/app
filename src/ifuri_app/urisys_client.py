"""HTTP client for urisys-node (local slave or remote host)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def default_node_endpoint() -> str:
    for key in ("URISYS_NODE_ENDPOINT", "IFURI_URISYS_ENDPOINT"):
        value = os.environ.get(key)
        if value:
            return value.rstrip("/")
    try:
        from .storage import load_workspace

        ws_ep = (load_workspace().get("urisys") or {}).get("endpoint")
        if ws_ep:
            return str(ws_ep).rstrip("/")
    except Exception:
        pass
    return "http://127.0.0.1:8790"


VOICE_PACK_NAMES = frozenset({"stt", "tts", "voice", "uristt", "uri2voice", "uriwebrtc"})
WEBRTC_PACK_NAMES = frozenset({"webrtc", "uriwebrtc"})


LLM_PACK_NAMES = frozenset({"llm", "urillm"})


def node_llm_available(client: UrisysNodeClient | None = None) -> bool:
    node = client or UrisysNodeClient()
    health = node.health()
    if not health.get("ok"):
        return False
    packs = {str(p).lower() for p in (health.get("packs_loaded") or [])}
    return bool(packs & LLM_PACK_NAMES)


def node_webrtc_available(client: UrisysNodeClient | None = None) -> bool:
    node = client or UrisysNodeClient()
    health = node.health()
    if not health.get("ok"):
        return False
    packs = {str(p).lower() for p in (health.get("packs_loaded") or [])}
    return bool(packs & WEBRTC_PACK_NAMES)


def node_voice_capabilities(client: UrisysNodeClient | None = None) -> dict[str, Any]:
    node = client or UrisysNodeClient()
    health = node.health()
    if not health.get("ok"):
        return {"stt": False, "tts": False, "llm": False, "webrtc": False, "reachable": False, "endpoint": node.endpoint}
    packs = {str(p).lower() for p in (health.get("packs_loaded") or [])}
    has_voice = bool(packs & VOICE_PACK_NAMES) or "stt" in packs
    routes = int(health.get("routes_count") or 0)
    # Heuristic: dedicated voice packs or enough routes that stt/tts were registered.
    has_stt = has_voice or routes > 60
    return {
        "reachable": True,
        "endpoint": node.endpoint,
        "stt": has_stt,
        "tts": has_stt,
        "llm": node_llm_available(node),
        "webrtc": node_webrtc_available(node),
        "packs_loaded": sorted(packs),
    }


class UrisysNodeClient:
    def __init__(self, endpoint: str | None = None, *, timeout: float = 60.0):
        self.endpoint = (endpoint or default_node_endpoint()).rstrip("/")
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def call_uri(
        self,
        uri: str,
        payload: dict[str, Any] | None = None,
        *,
        approved: bool = True,
        allow_real: bool = True,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        body = {
            "uri": uri,
            "payload": payload or {},
            "context": {
                "approved": approved,
                "allow_real": allow_real,
                "dry_run": dry_run,
            },
        }
        return self._post("/uri/call", body)

    def app_chat_messages(self, channel_id: str, *, limit: int = 200) -> dict[str, Any]:
        qs = urllib.parse.urlencode({"channel_id": channel_id, "limit": limit})
        return self._get(f"/app/chat/messages?{qs}")

    def app_chat_channels(self, *, limit: int = 100) -> dict[str, Any]:
        qs = urllib.parse.urlencode({"limit": limit})
        return self._get(f"/app/chat/channels?{qs}")

    def app_chat_append(
        self,
        channel_id: str,
        role: str,
        text: str,
        *,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/app/chat/messages",
            {"channel_id": channel_id, "role": role, "text": text, "meta": meta or {}},
        )

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.endpoint}{path}"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return {"ok": False, "error": f"HTTP {exc.code}", "url": url}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "url": url}

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.endpoint}{path}"
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"ok": False, "error": raw or f"HTTP {exc.code}"}
            parsed.setdefault("ok", False)
            return parsed
        except Exception as exc:
            return {"ok": False, "error": str(exc), "url": url}
