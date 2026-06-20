# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Local uricore runtime backed by packages/*/manifest.yaml."""

from __future__ import annotations

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def get_local_uri_runtime():
    """Return UriControlRuntime for ifURI packs, or None if uricore unavailable."""
    try:
        from uri_control import InMemoryEventStore, PolicyEngine, UriControlRuntime
        from uri_control.registry import RouteNotFoundError  # noqa: F401

        from .loader import load_local_registry

        registry = load_local_registry()
        return UriControlRuntime(
            registry=registry,
            event_store=InMemoryEventStore(),
            policy_engine=PolicyEngine(),
        )
    except ImportError:
        return None


def dispatch_local_uri(
    uri: str,
    payload: dict[str, Any] | None = None,
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Dispatch via local pack handlers. None when no matching route."""
    runtime = get_local_uri_runtime()
    if runtime is None:
        return None
    try:
        from uri_control.registry import RouteNotFoundError

        runtime.registry.match(uri)
    except Exception:
        return None
    ctx = dict(context or {})
    dispatch = runtime.call(uri, payload or {}, context=ctx)
    out = dispatch.to_dict()
    out["via"] = "uricore-local"
    return out


def local_runtime_info() -> dict[str, Any]:
    runtime = get_local_uri_runtime()
    if runtime is None:
        return {"available": False, "packs": []}
    loaded = list(getattr(runtime.registry, "_ifuri_loaded_packs", []) or [])
    return {
        "available": True,
        "packs": loaded,
        "routes": len(runtime.registry.routes),
    }
