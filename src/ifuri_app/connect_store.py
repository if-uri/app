# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Connector hub store (IFURI-017) — fetch the connect.ifuri.com catalog, plan
package installs, and derive payload forms.

REAL CONTRACT (connect.ifuri.com ``GET /connectors.json``)
----------------------------------------------------------
Matches the live hub (``if-uri/connect.ifuri.com``, ``data/connectors.json`` /
``hub_catalog()``). Catalog shape::

    {
      "version": "ifuri.connectors.v1",
      "connectors": [
        {
          "id": "planfile",
          "name": "Planfile Tasks",
          "status": "available",
          "category": "Planning",
          "summary": "...",
          "uriSchemes": ["task", "planfile"],
          "routes": ["task://host/tickets/query/list", ...],   # plain URI strings
          "install": {"mode": "urirun-extra",
                      "pipSpec": "urirun-connector-planfile @ git+https://github.com/if-uri/urirun-connector-planfile.git@v0.1.1"}
        }
      ]
    }

:func:`normalize_packages` flattens this (and the older ``packages``/``scheme``/
``install.spec`` shape, kept for back-compat) into one stable row shape the GUI
and tests consume. Stdlib-only and side-effect free apart from the HTTP GET in
:func:`fetch_catalog`.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any

DEFAULT_CATALOG_URL = "https://connect.ifuri.com/connectors.json"
_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
_VERSION_RE = re.compile(r"@(v[0-9][\w.\-]*)")


def catalog_url() -> str:
    """Catalog endpoint — ``IFURI_CONNECT_CATALOG`` env override, else the default."""
    return os.environ.get("IFURI_CONNECT_CATALOG") or DEFAULT_CATALOG_URL


def _normalize_route(route: Any) -> dict[str, Any]:
    if isinstance(route, str):
        return {"uri": route, "params": []}
    if isinstance(route, dict) and route.get("uri"):
        params = route.get("params") or []
        norm_params = [
            {"name": p["name"], "required": bool(p.get("required", False))}
            for p in params
            if isinstance(p, dict) and p.get("name")
        ]
        return {"uri": str(route["uri"]), "params": norm_params}
    return {}


def _normalize_install(install: dict[str, Any]) -> dict[str, Any]:
    """Map either the hub shape ({mode, pipSpec}) or the legacy {kind, spec}."""
    spec = (install.get("pipSpec") or install.get("spec") or "").strip()
    # hub install is always pip-based (mode urirun-extra/...); legacy carried kind explicitly
    kind = "pip" if spec else str(install.get("kind") or "")
    return {"kind": kind, "spec": spec, "mode": str(install.get("mode") or "")}


def _version_of(install: dict[str, Any], pkg: dict[str, Any]) -> str:
    if pkg.get("version"):
        return str(pkg["version"])
    match = _VERSION_RE.search(install.get("spec") or "")
    return match.group(1) if match else ""


def _normalize_package_item(pkg: Any) -> "dict[str, Any] | None":
    """Normalize one catalog entry; returns None if the entry is unusable."""
    if not isinstance(pkg, dict):
        return None
    name = pkg.get("name") or pkg.get("id")
    if not name:
        return None
    install = _normalize_install(pkg.get("install") if isinstance(pkg.get("install"), dict) else {})
    schemes = pkg.get("uriSchemes") or ([pkg["scheme"]] if pkg.get("scheme") else [])
    routes = [r for r in (_normalize_route(r) for r in (pkg.get("routes") or [])) if r]
    examples = [
        {"title": str(e.get("title") or ""), "uri": str(e.get("uri") or ""),
         "payload": e["payload"] if isinstance(e.get("payload"), dict) else {}}
        for e in (pkg.get("examples") or [])
        if isinstance(e, dict) and e.get("uri")
    ]
    return {
        "id": str(pkg.get("id") or name),
        "name": str(name),
        "version": _version_of(install, pkg),
        "scheme": str(schemes[0]) if schemes else "",
        "schemes": [str(s) for s in schemes],
        "summary": str(pkg.get("summary") or pkg.get("description") or ""),
        "category": str(pkg.get("category") or ""),
        "status": str(pkg.get("status") or ""),
        "install": install,
        "routes": routes,
        "examples": examples,
    }


def normalize_packages(payload: Any) -> list[dict[str, Any]]:
    """Flatten a catalog payload into a stable list of connector-package dicts.

    Accepts the live hub shape (``{connectors: [...]}`` with ``id``/``uriSchemes``/
    ``install.pipSpec``) and the older ``{packages: [...]}``/``scheme`` shape.
    """
    if isinstance(payload, dict):
        packages = payload.get("connectors") or payload.get("packages") or []
    else:
        packages = payload
    if not isinstance(packages, (list, tuple)):
        return []
    out = [item for pkg in packages for item in [_normalize_package_item(pkg)] if item]
    out.sort(key=lambda p: p["name"].lower())
    return out


def fetch_catalog(url: str | None = None, *, timeout: float = 4.0) -> dict[str, Any]:
    """GET the hub catalog and normalise it. Never raises — errors come back as data."""
    target = url or catalog_url()
    try:
        with urllib.request.urlopen(target, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as data
        return {"ok": False, "url": target, "packages": [], "error": str(exc)}
    if isinstance(payload, dict) and payload.get("ok") is False:
        return {"ok": False, "url": target, "packages": [],
                "error": str(payload.get("error") or "hub reported not-ok")}
    return {"ok": True, "url": target, "packages": normalize_packages(payload), "error": None}


def install_command(pkg: dict[str, Any]) -> list[str] | None:
    """Build the install argv for a package, or ``None`` if it can't be installed.

    Only ``pip`` installs are understood today; other kinds return None so the
    GUI can show "manual install" rather than running something unexpected.
    """
    install = pkg.get("install") or {}
    spec = (install.get("spec") or "").strip()
    if install.get("kind") == "pip" and spec:
        return ["python", "-m", "pip", "install", spec]
    return None


def local_registry_status() -> dict[str, Any]:
    """Summarise the local urirun registry for the post-install 'refresh' step.

    Never raises; reports whether urirun is installed and how many routes the
    configured registry exposes, so the Connect tab can confirm an installed
    connector actually landed in the local registry.
    """
    from .urirun_bridge import default_urirun_registry, registry_summary, urirun_info

    info = urirun_info()
    path = default_urirun_registry()
    status: dict[str, Any] = {
        "available": bool(info.get("available")),
        "version": info.get("version"),
        "registry": path,
        "configured": bool(path),
        "routes": 0,
        "bindings": 0,
    }
    if path:
        try:
            summary = registry_summary(path)
            status["routes"] = int(summary.get("routes") or 0)
            status["bindings"] = int(summary.get("bindings") or 0)
        except Exception as exc:  # noqa: BLE001 - surface registry read failure as data
            status["error"] = str(exc)
    return status


def example_payload_for(uri: str, examples: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    """Return the example payload whose ``uri`` matches ``uri``, if any."""
    for ex in examples or []:
        if ex.get("uri") == uri and isinstance(ex.get("payload"), dict):
            return ex["payload"]
    return None


def payload_form_fields(route: dict[str, Any], examples: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Derive ordered, de-duplicated form fields for a route's run payload.

    Fields come from, in priority order: (1) explicit ``params`` metadata, (2) a
    matching connector ``example`` payload — keys become fields pre-filled with the
    example value (the richest source the hub offers), and (3) ``{placeholder}``
    tokens in the URI template. Each field is ``{name, required, example}``.
    """
    fields: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(name: str, *, required: bool, example: Any = "") -> None:
        if name and name not in seen:
            seen.add(name)
            fields.append({"name": name, "required": required, "example": "" if example is None else str(example)})

    for p in route.get("params") or []:
        add(p.get("name"), required=bool(p.get("required", False)))
    for key, value in (example_payload_for(route.get("uri") or "", examples) or {}).items():
        add(str(key), required=False, example=value)
    for token in _PLACEHOLDER_RE.findall(route.get("uri") or ""):
        add(token, required=True)
    return fields
