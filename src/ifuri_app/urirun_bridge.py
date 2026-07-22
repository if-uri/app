# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

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
from typing import Any, Callable


INSTALL_HINT = (
    'python -m pip install "urirun>=0.4.190"'
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


def _is_route_not_found(result: Any) -> bool:
    """True when urirun reports a missing route, so callers may try fallback I/O."""
    if not isinstance(result, dict) or result.get("ok") is not False:
        return False
    error = result.get("error")
    if not isinstance(error, dict):
        return False
    message = str(error.get("message") or "").lower()
    category = str(error.get("category") or "").upper()
    return category == "NOT_FOUND" and "route not found" in message


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
    if _is_route_not_found(result):
        return None
    result.setdefault("ok", False)
    result["via"] = "urirun"
    result["execute"] = execute
    return result


def _resolve_available_registry(
    registry_path: str | Path | None = None,
    *,
    registry: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Resolve a registry or return the public error envelope to propagate."""
    info = urirun_info()
    if not info["available"]:
        error = {"ok": False, "available": False, "error": "urirun is not installed", "install": INSTALL_HINT}
        return None, error
    reg = registry if registry is not None else load_registry(registry_path or default_urirun_registry())
    if not reg:
        return None, {"ok": False, "error": "no urirun registry configured"}
    return reg, None


def _project_registry(
    registry_path: str | Path | None,
    *,
    registry: dict[str, Any] | None,
    module_name: str,
    result_key: str,
    project: Callable[[Any, dict[str, Any]], Any],
) -> dict[str, Any]:
    """Run a registry projection with the shared public error contract."""
    reg, error = _resolve_available_registry(registry_path, registry=registry)
    if error:
        return error
    try:
        module = importlib.import_module(module_name)
        return {"ok": True, result_key: project(module, reg)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def list_routes(
    registry_path: str | Path | None = None,
    *,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """List routes in a urirun registry (uses urirun.v2.list_routes)."""
    return _project_registry(
        registry_path,
        registry=registry,
        module_name="urirun.v2",
        result_key="routes",
        project=lambda module, reg: module.list_routes(reg),
    )


def serve_http(
    *,
    registry_path: str | Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8780,
    execute: bool = False,
    policy: dict[str, Any] | None = None,
) -> None:
    """Serve a urirun registry over HTTP.

    Endpoints: ``GET /health``, ``GET /routes``, ``POST /run`` ({uri, payload,
    execute?}). Execution is dry-run unless the server was started with
    ``execute=True`` (and the request asks for it), always behind the policy gate.
    """
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse

    info = urirun_info()
    if not info["available"]:
        raise RuntimeError(f"urirun is not installed. {INSTALL_HINT}")
    reg_path = registry_path or default_urirun_registry()
    registry = load_registry(reg_path)
    if not registry:
        raise RuntimeError("no urirun registry configured (use --registry or workspace urirun.registry)")
    # When the operator starts the server with --execute but supplies no policy,
    # default to allowing the registry's routes (mirrors approved flow execution).
    if policy is None and execute:
        policy = {"execute": {"allow": ["**"]}}

    def _summary() -> dict[str, Any]:
        out = {"ok": True, "urirun": info, "execute": execute}
        if reg_path:
            try:
                out["registry"] = registry_summary(reg_path)
            except Exception:  # noqa: BLE001
                out["registry"] = {"ok": False, "path": str(reg_path)}
        return out

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # quiet
            pass

        def _send(self, code: int, obj: dict[str, Any]) -> None:
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            route = urlparse(self.path).path
            if route in ("/", "/health"):
                self._send(200, _summary())
            elif route == "/routes":
                self._send(200, list_routes(registry=registry))
            else:
                self._send(404, {"ok": False, "error": "not found", "path": route})

        def do_POST(self):  # noqa: N802
            route = urlparse(self.path).path
            if route != "/run":
                self._send(404, {"ok": False, "error": "not found", "path": route})
                return
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception as exc:  # noqa: BLE001
                self._send(400, {"ok": False, "error": f"invalid JSON: {exc}"})
                return
            uri = body.get("uri")
            if not uri:
                self._send(400, {"ok": False, "error": "missing 'uri'"})
                return
            want_execute = bool(body.get("execute")) and execute
            result = dispatch_local(
                uri, body.get("payload") or {},
                execute=want_execute, confirm=bool(body.get("confirm")),
                policy=policy, registry=registry,
            )
            if result is None:
                self._send(404, {"ok": False, "via": "urirun", "uri": uri, "error": "route not in registry"})
            else:
                self._send(200 if result.get("ok") else 422, result)

    httpd = HTTPServer((host, port), Handler)
    print(json.dumps({"ok": True, "serving": f"http://{host}:{port}", "execute": execute, "registry": str(reg_path)}))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


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


def mcp_tools(registry_path: str | Path | None = None, *, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Project a urirun registry to an MCP tools/list (via urirun.v2_mcp)."""
    return _project_registry(
        registry_path,
        registry=registry,
        module_name="urirun.v2_mcp",
        result_key="tools",
        project=lambda module, reg: module.to_mcp_tools(reg),
    )


def a2a_card(
    registry_path: str | Path | None = None,
    *,
    registry: dict[str, Any] | None = None,
    name: str = "ifuri-urirun",
    url: str = "https://ifuri.com",
    version: str = "0.8.0",
) -> dict[str, Any]:
    """Project a urirun registry to an A2A agent card (via urirun.v2_mcp)."""
    return _project_registry(
        registry_path,
        registry=registry,
        module_name="urirun.v2_mcp",
        result_key="card",
        project=lambda module, reg: module.to_a2a_card(reg, name=name, url=url, version=version),
    )


def serve_mcp(*, registry_path: str | Path | None = None, execute: bool = False, policy: dict[str, Any] | None = None) -> None:
    """Serve the urirun registry as an MCP server over stdio (via urirun.v2_mcp)."""
    info = urirun_info()
    if not info["available"]:
        raise RuntimeError(f"urirun is not installed. {INSTALL_HINT}")
    reg = load_registry(registry_path or default_urirun_registry())
    if not reg:
        raise RuntimeError("no urirun registry configured (use --registry or workspace urirun.registry)")
    if policy is None and execute:
        policy = {"execute": {"allow": ["**"]}}
    m = importlib.import_module("urirun.v2_mcp")
    m.serve_mcp(reg, policy=policy, mode=("execute" if execute else "dry-run"))
