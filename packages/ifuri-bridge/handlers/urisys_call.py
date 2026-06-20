# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Proxy app:// commands to urisys-node (local dry-run envelope or real call)."""

from __future__ import annotations

from typing import Any


def _endpoint(payload: dict[str, Any], context: dict[str, Any]) -> str:
    variables = context.get("variables") or {}
    target = variables.get("target") or payload.get("target") or "local"
    ep = payload.get("endpoint") or context.get("endpoint") or variables.get("endpoint")
    if ep:
        return str(ep).rstrip("/")
    if target and target not in {"local", "default"}:
        if "://" in str(target):
            return str(target).rstrip("/")
        return f"http://{target}:8790"
    import os

    return os.environ.get("URISYS_NODE_ENDPOINT", "http://127.0.0.1:8790").rstrip("/")


def urisys_call(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    uri = str(payload.get("uri") or "")
    if not uri:
        return {"ok": False, "error": "missing uri in payload"}

    ep = _endpoint(payload, context)
    dry_run = bool(payload.get("dry_run", context.get("dry_run", False)))
    approved = bool(payload.get("approved", context.get("approved", False)))
    body = payload.get("payload")
    if body is None:
        body = {k: v for k, v in payload.items() if k not in {"uri", "endpoint", "dry_run", "approved", "target"}}

    try:
        from ifuri_app.urisys_client import UrisysNodeClient

        client = UrisysNodeClient(ep)
        result = client.call_uri(
            uri,
            body if isinstance(body, dict) else {},
            approved=approved,
            allow_real=not dry_run,
            dry_run=dry_run,
        )
        return {"ok": bool(result.get("ok", True)), "endpoint": ep, "result": result}
    except Exception as exc:
        return {"ok": False, "endpoint": ep, "error": str(exc)}


def node_health(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    ep = _endpoint(payload, context)
    try:
        from ifuri_app.urisys_client import UrisysNodeClient

        health = UrisysNodeClient(ep).health()
        return {"ok": bool(health.get("ok", True)), "endpoint": ep, "health": health}
    except Exception as exc:
        return {"ok": False, "endpoint": ep, "error": str(exc)}
