# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Connector hub store (IFURI-017) — fetch a connect.ifuri.com catalog, plan
package installs, and derive payload forms.

PROVISIONAL CONTRACT
--------------------
The real connect.ifuri.com catalog API is not finalised, so the wire shapes
below are an explicit, swappable assumption — grounded in the existing
``if-uri/urirun-connector-*`` repos that such a hub would serve. When the real
spec lands, only :func:`normalize_packages` and :func:`install_command` should
need to change; the GUI and tests drive everything through this module.

Assumed ``GET {catalog_url}`` response::

    {
      "ok": true,
      "packages": [
        {
          "name": "browser-control",
          "version": "0.3.1",
          "scheme": "browser",
          "summary": "Drive Chromium via browser:// URIs",
          "install": {"kind": "pip",
                      "spec": "git+https://github.com/if-uri/urirun-connector-browser-control.git"},
          "routes": [
            {"uri": "browser://{node}/page/command/open",
             "params": [{"name": "url", "required": true}]}
          ]
        }
      ]
    }

Kept stdlib-only and side-effect free apart from the HTTP GET in
:func:`fetch_catalog`, so normalisation and form/command derivation are unit
testable without a live hub.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any

DEFAULT_CATALOG_URL = "https://connect.ifuri.com/api/catalog"
_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


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


def normalize_packages(payload: Any) -> list[dict[str, Any]]:
    """Flatten a catalog payload into a stable list of connector-package dicts."""
    packages = payload.get("packages", payload) if isinstance(payload, dict) else payload
    if not isinstance(packages, (list, tuple)):
        return []
    out: list[dict[str, Any]] = []
    for pkg in packages:
        if not isinstance(pkg, dict) or not pkg.get("name"):
            continue
        install = pkg.get("install") if isinstance(pkg.get("install"), dict) else {}
        routes = [r for r in (_normalize_route(r) for r in (pkg.get("routes") or [])) if r]
        out.append({
            "name": str(pkg["name"]),
            "version": str(pkg.get("version") or ""),
            "scheme": str(pkg.get("scheme") or ""),
            "summary": str(pkg.get("summary") or pkg.get("description") or ""),
            "install": {"kind": str(install.get("kind") or ""), "spec": str(install.get("spec") or "")},
            "routes": routes,
        })
    out.sort(key=lambda p: p["name"])
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


def payload_form_fields(route: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive ordered, de-duplicated form fields for a route's run payload.

    Fields come from (1) explicit ``params`` metadata and (2) ``{placeholder}``
    tokens in the URI template, so a form can be shown before POSTing /run.
    """
    fields: list[dict[str, Any]] = []
    seen: set[str] = set()
    for p in route.get("params") or []:
        name = p.get("name")
        if name and name not in seen:
            seen.add(name)
            fields.append({"name": name, "required": bool(p.get("required", False))})
    for token in _PLACEHOLDER_RE.findall(route.get("uri") or ""):
        if token not in seen:
            seen.add(token)
            fields.append({"name": token, "required": True})
    return fields
