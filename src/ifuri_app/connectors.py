"""Connectors & URI routes — fetch and normalise a urirun node's ``/routes``.

A urirun node exposes ``GET /routes`` (see :mod:`ifuri_app.urirun_bridge`). The
payload shape has drifted across urirun versions, so this module normalises
whatever comes back into a flat list of route rows that the GUI can group by
node and URI scheme.

Accepted ``/routes`` shapes:
    {"ok": true, "routes": [{"uri": "sys://local/echo", "kind": "command", ...}]}
    {"ok": true, "routes": {"sys://local/echo": {"kind": "command", ...}}}
    {"ok": true, "routes": ["sys://local/echo", "mcp://fs/list"]}
    {"routes": ...}            # bare, no "ok"
    [ ... ]                    # bare list

Kept dependency-free (stdlib only) and side-effect free apart from the HTTP GET
in :func:`fetch_node_routes`, so the normaliser is unit-testable without a live
node or the optional ``urirun`` package installed.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

# Keys a route entry might use for the URI itself, in priority order.
_URI_KEYS = ("uri", "pattern", "route", "match", "id")
# Keys that carry a short human-facing detail for the route.
_DETAIL_KEYS = ("argv", "command", "target", "endpoint", "url", "description")


def route_scheme(uri: str) -> str:
    """Return the scheme of a URI (the part before ``://``), or ``"other"``."""
    text = (uri or "").strip()
    head, sep, _ = text.partition("://")
    if sep and head:
        return head.lower()
    # tolerate "scheme:path" without the double slash
    head, sep, _ = text.partition(":")
    return head.lower() if sep and head else "other"


def _detail(binding: dict[str, Any]) -> str:
    for key in _DETAIL_KEYS:
        val = binding.get(key)
        if val in (None, "", [], {}):
            continue
        if isinstance(val, (list, tuple)):
            return " ".join(str(p) for p in val)
        return str(val)
    return ""


def _row(uri: str, binding: dict[str, Any] | None = None) -> dict[str, Any]:
    binding = binding or {}
    return {
        "uri": uri,
        "scheme": route_scheme(uri),
        "kind": str(binding.get("kind") or ""),
        "adapter": str(binding.get("adapter") or ""),
        "detail": _detail(binding),
    }


def normalize_routes(payload: Any) -> list[dict[str, Any]]:
    """Flatten a ``/routes`` payload into sorted ``{uri, scheme, kind, ...}`` rows."""
    routes: Any = payload
    if isinstance(payload, dict):
        routes = payload.get("routes", payload)

    rows: list[dict[str, Any]] = []
    if isinstance(routes, dict):
        for uri, binding in routes.items():
            rows.append(_row(str(uri), binding if isinstance(binding, dict) else None))
    elif isinstance(routes, (list, tuple)):
        for item in routes:
            if isinstance(item, str):
                rows.append(_row(item))
            elif isinstance(item, dict):
                uri = next((str(item[k]) for k in _URI_KEYS if item.get(k)), "")
                if uri:
                    rows.append(_row(uri, item))
    # de-duplicate on uri (keep first), then sort by scheme then uri for stable display
    seen: set[str] = set()
    unique = [r for r in rows if not (r["uri"] in seen or seen.add(r["uri"]))]
    unique.sort(key=lambda r: (r["scheme"], r["uri"]))
    return unique


def group_by_scheme(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group normalised route rows by their URI scheme (insertion-sorted)."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["scheme"], []).append(row)
    return grouped


def fetch_node_routes(endpoint: str, *, timeout: float = 3.0) -> dict[str, Any]:
    """GET ``{endpoint}/routes`` and normalise it.

    Returns ``{"ok", "endpoint", "routes", "error"}``; ``ok`` is False with a
    populated ``error`` on any transport/parse failure — never raises.
    """
    base = (endpoint or "").rstrip("/")
    url = f"{base}/routes"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as data
        return {"ok": False, "endpoint": endpoint, "routes": [], "error": str(exc)}
    if isinstance(payload, dict) and payload.get("ok") is False:
        return {
            "ok": False,
            "endpoint": endpoint,
            "routes": [],
            "error": str(payload.get("error") or "node reported not-ok"),
        }
    return {"ok": True, "endpoint": endpoint, "routes": normalize_routes(payload), "error": None}
