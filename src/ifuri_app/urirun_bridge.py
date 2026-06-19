"""Optional bridge to the urirun Python runtime.

ifURI must work without urirun installed, but when the package is available this
module gives the app and CLI one small entry point for registry-backed URI calls.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any


INSTALL_HINT = (
    'python -m pip install "git+https://github.com/tellmesh/urirun.git@main'
    '#subdirectory=adapters/python"'
)


def urirun_info() -> dict[str, Any]:
    spec = importlib.util.find_spec("urirun")
    if spec is None:
        return {
            "available": False,
            "package": "urirun",
            "install": INSTALL_HINT,
        }
    try:
        version = importlib.metadata.version("urirun")
    except importlib.metadata.PackageNotFoundError:
        version = None
    return {
        "available": True,
        "package": "urirun",
        "version": version,
        "origin": spec.origin,
        "install": INSTALL_HINT,
    }


def load_registry(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    registry_path = Path(path).expanduser()
    return json.loads(registry_path.read_text(encoding="utf-8"))


@contextmanager
def service_map_env(service_map: dict[str, str] | None):
    previous = os.environ.get("URI_SERVICE_MAP")
    if service_map:
        os.environ["URI_SERVICE_MAP"] = json.dumps(service_map)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("URI_SERVICE_MAP", None)
        else:
            os.environ["URI_SERVICE_MAP"] = previous


def parse_json_object(value: str | dict[str, Any] | None, *, name: str) -> dict[str, Any]:
    if value is None or value == "":
        return {}
    if isinstance(value, dict):
        return value
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object")
    return parsed


def call_urirun(
    uri: str,
    payload: dict[str, Any] | None = None,
    *,
    registry_path: str | Path | None = None,
    registry: dict[str, Any] | None = None,
    execute: bool = False,
    service_map: dict[str, str] | None = None,
    timeout: float = 30.0,
    validate: bool = True,
) -> dict[str, Any]:
    info = urirun_info()
    if not info["available"]:
        return {
            "ok": False,
            "available": False,
            "via": "urirun",
            "error": "urirun is not installed",
            "install": INSTALL_HINT,
            "uri": uri,
            "payload": payload or {},
        }

    try:
        v2_service = importlib.import_module("urirun.v2_service")
    except Exception as exc:  # noqa: BLE001 - report optional dependency shape.
        return {
            "ok": False,
            "available": False,
            "via": "urirun",
            "error": f"cannot import urirun.v2_service: {exc}",
            "install": INSTALL_HINT,
            "uri": uri,
            "payload": payload or {},
        }

    effective_registry = registry if registry is not None else load_registry(registry_path)
    mode = "execute" if execute else "dry-run"
    with service_map_env(service_map):
        result = v2_service.call(
            uri,
            payload or {},
            effective_registry,
            mode=mode,
            timeout=timeout,
            validate=validate,
        )
    result.setdefault("ok", False)
    result["via"] = "urirun"
    result["execute"] = execute
    if registry_path:
        result["registry"] = str(registry_path)
    return result


def registry_summary(path: str | Path) -> dict[str, Any]:
    registry = load_registry(path) or {}
    bindings = registry.get("bindings") if isinstance(registry.get("bindings"), dict) else {}
    index = registry.get("index") if isinstance(registry.get("index"), dict) else {}
    routes = registry.get("routes") if isinstance(registry.get("routes"), dict) else {}
    route_count = registry.get("routeCount")
    if not isinstance(route_count, int):
        route_count = len(routes) or len(index) or len(bindings)
    return {
        "ok": True,
        "path": str(path),
        "version": registry.get("version"),
        "bindings": len(bindings) or route_count,
        "routes": route_count,
    }


def default_urirun_registry() -> str | None:
    """Resolve the project's urirun registry path (env or workspace).

    urirun is the primary local runtime in ifURI; this points the flow runner and
    HTTP dispatch at a compiled registry so URIs run in-process instead of through
    the legacy shell urisys-node.
    """
    env = os.environ.get("IFURI_URIRUN_REGISTRY")
    if env:
        return env
    try:
        from .storage import load_workspace

        ws = (load_workspace().get("urirun") or {}).get("registry")
        if ws:
            return str(ws)
    except Exception:
        pass
    return None


def dispatch_local(
    uri: str,
    payload: dict[str, Any] | None = None,
    *,
    execute: bool = False,
    confirm: bool = False,
    policy: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Run a URI in-process through urirun's v2 runtime (registry + policy gate).

    Returns the urirun result envelope when the route is in the registry, or
    ``None`` when urirun is unavailable, no registry is configured, or the URI is
    not a urirun route — so callers can fall back to another transport.
    """
    info = urirun_info()
    if not info["available"]:
        return None
    effective = registry if registry is not None else load_registry(registry_path or default_urirun_registry())
    if not effective:
        return None
    try:
        v2 = importlib.import_module("urirun.v2")
    except Exception:  # noqa: BLE001 - optional dependency shape
        return None
    mode = "execute" if execute else "dry-run"
    try:
        result = v2.run(uri, effective, payload or {}, mode=mode, policy=policy, confirm=confirm)
    except KeyError:
        # Route not in the urirun registry -> let the caller try another transport.
        return None
    except Exception as exc:  # noqa: BLE001 - report adapter/runtime errors as envelope
        return {"ok": False, "via": "urirun", "uri": uri, "error": str(exc)}
    result.setdefault("ok", False)
    result["via"] = "urirun"
    result["execute"] = execute
    return result


def scan_project(
    path: str | Path,
    *,
    out: str | Path | None = None,
    registry_out: str | Path | None = None,
) -> dict[str, Any]:
    """Scan a project for URI bindings and compile a registry via the urirun CLI."""
    info = urirun_info()
    if not info["available"]:
        return {"ok": False, "available": False, "error": "urirun is not installed", "install": INSTALL_HINT}
    cmd = [sys.executable, "-m", "urirun.v2", "scan", str(path)]
    if out:
        cmd += ["--out", str(out)]
    if registry_out:
        cmd += ["--registry-out", str(registry_out)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except Exception as exc:  # noqa: BLE001 - surface scan failures as an envelope
        return {"ok": False, "via": "urirun", "error": str(exc), "command": cmd}
    result: dict[str, Any] = {
        "ok": proc.returncode == 0,
        "via": "urirun",
        "returncode": proc.returncode,
        "path": str(path),
    }
    if out:
        result["bindings"] = str(out)
    if registry_out:
        result["registry"] = str(registry_out)
    if proc.stdout.strip():
        result["stdout"] = proc.stdout.strip()
    if proc.returncode != 0 and proc.stderr.strip():
        result["error"] = proc.stderr.strip()
    return result
