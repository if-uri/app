# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

from __future__ import annotations

import errno
import base64
import json
import mimetypes
import socket
import subprocess
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any
from urllib.parse import parse_qs, urlparse

from . import __version__
from .flow_compile import uri2flow_available, validate_flow
from .flow_engine import dry_run_flow, dry_run_uri, expand_flow
from .packs.loader import pack_summary
from .packs.runtime import dispatch_local_uri, get_local_uri_runtime, local_runtime_info
from .urirun_bridge import (
    call_urirun,
    default_urirun_registry,
    dispatch_local as urirun_dispatch,
    parse_json_object,
    registry_summary,
    urirun_info,
)
from .urisys_client import UrisysNodeClient
from .flow_runner import examples_root, run_flow_file
from .chat_channels import (
    fetch_chat_channel_index,
    fetch_chat_history,
    list_chat_channels,
    migrate_local_chat_to_urisys,
    send_chat_message_routed,
    urisys_chat_available,
)
from .network_scan import scan_network
from .storage import add_event, load_workspace, save_workspace, now_iso
from .remote_screen import capture_remote_screen, probe_remote_control
from .paths import web_dir
from .voice_pipeline import (
    install_voice_packs,
    plan_voice_command,
    run_voice_command,
    voice_capabilities,
)
from .voice_planner import load_flow_catalog, voice_planner_mode
from .webrtc_signal import local_peer_url, poll_signals, post_signal
from .webrtc_pipeline import webrtc_capabilities

WEB_DIR = web_dir()


class PortInUseError(OSError):
    """HTTP bind failed because the port is already taken."""


def _port_listeners(port: int) -> list[str]:
    try:
        out = subprocess.check_output(
            ["ss", "-tlnp"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.0,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []
    hits: list[str] = []
    needle = f":{port}"
    for line in out.splitlines():
        if needle not in line:
            continue
        hits.append(line.strip())
    return hits


def format_port_in_use_error(host: str, port: int) -> str:
    listeners = _port_listeners(port)
    lines = [
        f"Port {port} on {host} is already in use.",
        "Another ifURI instance may already be running — open the existing UI or stop it first.",
        f"Try: ifuri-app voice --port {port + 1}",
    ]
    if listeners:
        lines.append("Listeners:")
        lines.extend(f"  {row}" for row in listeners[:4])
    return "\n".join(lines)


def _port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def find_free_port(host: str, start: int, *, attempts: int = 10) -> int:
    for port in range(start, start + attempts):
        if _port_available(host, port):
            return port
    raise PortInUseError(format_port_in_use_error(host, start))


def bind_runtime_server(host: str, port: int, handler) -> ThreadingHTTPServer:
    try:
        return ThreadingHTTPServer((host, port), handler)
    except OSError as exc:
        if exc.errno in {errno.EADDRINUSE, getattr(errno, "WSAEADDRINUSE", errno.EADDRINUSE)}:
            raise PortInUseError(format_port_in_use_error(host, port)) from exc
        raise


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def _load_urirun_policy(data: dict[str, Any], approved: bool) -> dict[str, Any] | None:
    """Policy for in-process urirun execution.

    Uses ``urirun.policy`` (a JSON path) from the workspace when present. When the
    operator approved a real run we default to allowing the registry's own routes
    (mirroring the old approved urisys-node behaviour); otherwise execution stays
    default-deny.
    """
    pol_path = (data.get("urirun") or {}).get("policy")
    if pol_path:
        try:
            return json.loads(Path(pol_path).expanduser().read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - bad policy path should not crash dispatch
            pass
    return {"execute": {"allow": ["**"]}} if approved else None


class RuntimeState:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port

    def load(self) -> dict[str, Any]:
        data = load_workspace()
        node = data.setdefault("node", {})
        if node.get("port") != self.port:
            node["port"] = self.port
            save_workspace(data)
        return data

    def health(self) -> dict[str, Any]:
        data = self.load()
        node_ep = data.get("urisys", {}).get("endpoint") or UrisysNodeClient().endpoint
        urisys = UrisysNodeClient(node_ep).health()
        return {
            "ok": True,
            "name": "ifURI runtime",
            "version": __version__,
            "node": data.get("node", {}),
            "urisys": {"endpoint": node_ep, "health": urisys},
            "examples_root": str(examples_root()),
            "services": len(data.get("services", [])),
            "groups": len(data.get("groups", [])),
            "packs": local_runtime_info(),
            "urirun": urirun_info(),
            "uri2flow": uri2flow_available(),
            "time": now_iso(),
        }

    def call_uri(
        self,
        uri: str,
        payload: dict[str, Any] | None = None,
        dry_run: bool = True,
        *,
        approved: bool = True,
    ) -> dict[str, Any]:
        data = self.load()
        node_ep = data.get("urisys", {}).get("endpoint") or UrisysNodeClient().endpoint
        ctx = {
            "endpoint": node_ep,
            "approved": approved,
            "dry_run": dry_run,
        }
        if not dry_run:
            local = dispatch_local_uri(uri, payload, context=ctx)
            if local is not None:
                add_event(data, "uri.call", uri=uri, dry_run=False, ok=local.get("ok"), via="uricore-local")
                save_workspace(data)
                return local
        else:
            runtime = get_local_uri_runtime()
            if runtime is not None:
                try:
                    matched = runtime.registry.match(uri)
                    preview = dry_run_uri(uri, payload)
                    preview["via"] = "local-pack-preview"
                    preview["operation"] = matched.route.operation
                    preview["manifest_id"] = matched.route.manifest_id
                    add_event(data, "uri.call", uri=uri, dry_run=True, ok=True, via="local-pack-preview")
                    save_workspace(data)
                    return preview
                except Exception:
                    pass
        # urirun in-process runtime (registry-backed) before any remote fallback
        urirun_reg = (data.get("urirun") or {}).get("registry") or default_urirun_registry()
        urirun_resp = urirun_dispatch(
            uri,
            payload,
            execute=not dry_run,
            confirm=approved,
            policy=_load_urirun_policy(data, approved) if not dry_run else None,
            registry_path=urirun_reg,
        )
        if urirun_resp is not None:
            add_event(data, "uri.call", uri=uri, dry_run=dry_run, ok=urirun_resp.get("ok"), via="urirun")
            save_workspace(data)
            return urirun_resp
        result = dry_run_uri(uri, payload)
        result["dry_run"] = dry_run
        if not dry_run:
            result["ok"] = False
            result["message"] = "no local pack route — use urirun registry, /api/urisys/call, or install a matching handler"
        add_event(data, "uri.call", uri=uri, dry_run=dry_run, ok=result.get("ok"))
        save_workspace(data)
        return result

    def run_flow(self, flow_text: str, dry_run: bool = True, *, approved: bool = True) -> dict[str, Any]:
        data = self.load()
        if dry_run:
            result = dry_run_flow(flow_text)
            result["dry_run"] = True
            add_event(data, "flow.run", dry_run=True, steps=len(result.get("steps", [])))
            save_workspace(data)
            return result

        expanded = expand_flow(flow_text)
        nodes = (expanded.get("workflow_graph") or {}).get("nodes") or []
        node_ep = data.get("urisys", {}).get("endpoint") or UrisysNodeClient().endpoint
        client = UrisysNodeClient(node_ep)
        urirun_reg = (data.get("urirun") or {}).get("registry") or default_urirun_registry()
        urirun_pol = _load_urirun_policy(data, approved)
        steps_out: list[dict[str, Any]] = []
        ok = True
        for node in nodes:
            uri = str(node.get("uri") or "")
            if not uri:
                continue
            payload = node.get("payload") if isinstance(node.get("payload"), dict) else {}
            local = dispatch_local_uri(uri, payload, context={"endpoint": node_ep, "approved": approved, "dry_run": False})
            urirun_resp = None
            if local is None:
                urirun_resp = urirun_dispatch(
                    uri, payload, execute=True, confirm=approved,
                    policy=urirun_pol, registry_path=urirun_reg,
                )
            if local is not None:
                step_ok = bool(local.get("ok"))
                steps_out.append({"id": node.get("id"), "uri": uri, "ok": step_ok, "via": "uricore-local", "response": local})
            elif urirun_resp is not None:
                step_ok = bool(urirun_resp.get("ok"))
                steps_out.append({"id": node.get("id"), "uri": uri, "ok": step_ok, "via": "urirun", "response": urirun_resp})
            else:
                resp = client.call_uri(uri, payload, approved=approved, allow_real=True)
                step_ok = bool(resp.get("ok", True)) and not resp.get("error")
                steps_out.append({"id": node.get("id"), "uri": uri, "ok": step_ok, "via": "urisys-node", "response": resp})
            ok = ok and step_ok
            if not step_ok:
                break
        result = {"ok": ok, "dry_run": False, "graph": expanded, "steps": steps_out, "endpoint": node_ep}
        add_event(data, "flow.run", dry_run=False, steps=len(steps_out))
        save_workspace(data)
        return result


def json_bytes(data: Any) -> bytes:
    return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")


def make_handler(state: RuntimeState):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ifURI/0.1"

        def log_message(self, fmt: str, *args: Any) -> None:
            # Keep CLI output clean. Runtime events are stored in workspace.json.
            return

        def _send(self, status: int, data: Any) -> None:
            body = json_bytes(data)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.end_headers()
            self.wfile.write(body)

        def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0:
                return {}
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as exc:
                return {"_error": str(exc), "_raw": raw.decode("utf-8", errors="replace")}

        def do_OPTIONS(self) -> None:
            self._send(200, {"ok": True})

        def _serve_file(self, rel_path: str) -> None:
            path = (WEB_DIR / rel_path).resolve()
            if not str(path).startswith(str(WEB_DIR.resolve())) or not path.is_file():
                self._send(404, {"ok": False, "error": "not_found"})
                return
            ctype, _ = mimetypes.guess_type(str(path))
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            try:
                self._do_GET_impl(head_only=False)
            except Exception as exc:
                traceback.print_exc()
                self._send(500, {"ok": False, "error": str(exc), "type": type(exc).__name__})

        def do_HEAD(self) -> None:
            try:
                self._do_GET_impl(head_only=True)
            except Exception as exc:
                traceback.print_exc()
                self._send(500, {"ok": False, "error": str(exc), "type": type(exc).__name__})

        def _do_GET_impl(self, *, head_only: bool = False) -> None:
            path = urlparse(self.path).path
            if path in {"/voice", "/"}:
                if head_only:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    return
                self._serve_file("index.html")
            elif path.startswith("/web/"):
                if head_only:
                    self.send_response(200)
                    self.end_headers()
                    return
                self._serve_file(path[len("/web/"):])
            else:
                handler = Handler._GET_ROUTES.get(path)
                if handler:
                    data = state.load()
                    qs = parse_qs(urlparse(self.path).query)
                    handler(self, data, qs)
                else:
                    self._send(404, {"ok": False, "error": "not_found", "path": path})

        def do_POST(self) -> None:
            try:
                self._do_POST_impl()
            except Exception as exc:
                traceback.print_exc()
                self._send(500, {"ok": False, "error": str(exc), "type": type(exc).__name__})

        def _do_POST_impl(self) -> None:
            path = urlparse(self.path).path
            body = self._read_json()
            if body.get("_error"):
                self._send(400, {"ok": False, "error": body["_error"]})
                return
            handler = Handler._POST_ROUTES.get(path)
            if handler:
                data = state.load()
                handler(self, body, data)
            else:
                self._send(404, {"ok": False, "error": "not_found", "path": path})

        # ── GET handlers ──────────────────────────────────────────────────────

        def _get_health(self, data: dict, qs: dict) -> None:
            self._send(200, state.health())

        def _get_services(self, data: dict, qs: dict) -> None:
            self._send(200, {"ok": True, "services": data.get("services", [])})

        def _get_flows(self, data: dict, qs: dict) -> None:
            self._send(200, {"ok": True, "groups": data.get("groups", [])})

        def _get_peers(self, data: dict, qs: dict) -> None:
            self._send(200, {"ok": True, "peers": data.get("peers", [])})

        def _get_routes(self, data: dict, qs: dict) -> None:
            self._send(200, {"ok": True, "schemes": sorted({s.get("scheme", "unknown") for s in data.get("services", [])})})

        def _get_examples(self, data: dict, qs: dict) -> None:
            self._send(200, {"ok": True, "root": str(examples_root())})

        def _get_packs(self, data: dict, qs: dict) -> None:
            info = local_runtime_info()
            self._send(
                200,
                {
                    "ok": True,
                    "packs": pack_summary(),
                    "loaded": info.get("packs") or [],
                    "runtime": info,
                    "uri2flow": uri2flow_available(),
                },
            )

        def _get_urirun(self, data: dict, qs: dict) -> None:
            registry = (qs.get("registry") or [""])[0]
            out = urirun_info()
            if registry:
                try:
                    out["registry"] = registry_summary(registry)
                except Exception as exc:  # noqa: BLE001 - invalid registry path is API data.
                    out["registry"] = {"ok": False, "path": registry, "error": str(exc)}
            self._send(200, out)

        def _get_voice_catalog(self, data: dict, qs: dict) -> None:
            refresh = (qs.get("refresh") or ["0"])[0] == "1"
            self._send(
                200,
                {
                    "ok": True,
                    "planner": voice_planner_mode(),
                    "flows": load_flow_catalog(refresh=refresh),
                },
            )

        def _get_voice_capabilities(self, data: dict, qs: dict) -> None:
            ep = (qs.get("endpoint") or [""])[0] or data.get("urisys", {}).get("endpoint") or ""
            client = UrisysNodeClient(ep or None) if ep else UrisysNodeClient()
            self._send(200, voice_capabilities(client))

        def _get_webrtc_capabilities(self, data: dict, qs: dict) -> None:
            ep = (qs.get("endpoint") or [""])[0] or data.get("urisys", {}).get("endpoint") or ""
            client = UrisysNodeClient(ep or None) if ep else None
            out = webrtc_capabilities(client)
            out["local_api_url"] = local_peer_url(host=state.host, port=state.port)
            self._send(200, out)

        def _get_webrtc_signal(self, data: dict, qs: dict) -> None:
            room = (qs.get("room") or [""])[0]
            try:
                since = int((qs.get("since") or ["0"])[0])
            except ValueError:
                since = 0
            self._send(200, poll_signals(room, since=since))

        def _get_chat_channels(self, data: dict, qs: dict) -> None:
            try:
                timeout = float((qs.get("timeout") or ["1.5"])[0])
            except ValueError:
                timeout = 1.5
            payload = list_chat_channels(
                timeout=min(max(timeout, 0.5), 5.0),
                local_host=state.host,
                local_port=state.port,
            )
            router = (qs.get("endpoint") or [""])[0] or data.get("urisys", {}).get("endpoint") or ""
            if router or payload.get("channels"):
                hist = fetch_chat_channel_index(router_endpoint=router or None)
                if hist.get("ok"):
                    by_id = {c["channel_id"]: c for c in hist.get("channels") or []}
                    payload["history_index"] = by_id
                    for ch in payload.get("channels") or []:
                        preview = by_id.get(ch.get("id") or "")
                        if preview:
                            ch["last_message_at"] = preview.get("last_at")
                            ch["preview"] = preview.get("preview")
            self._send(200, payload)

        def _get_chat_history(self, data: dict, qs: dict) -> None:
            channel_id = (qs.get("channel_id") or qs.get("channel") or [""])[0]
            if not channel_id:
                self._send(400, {"ok": False, "error": "missing channel_id"})
                return
            try:
                limit = int((qs.get("limit") or ["200"])[0])
            except ValueError:
                limit = 200
            router = (qs.get("endpoint") or [""])[0] or data.get("urisys", {}).get("endpoint") or ""
            self._send(
                200,
                fetch_chat_history(
                    channel_id,
                    router_endpoint=router or None,
                    limit=min(max(limit, 1), 500),
                ),
            )

        def _get_chat_status(self, data: dict, qs: dict) -> None:
            router = (qs.get("endpoint") or [""])[0] or data.get("urisys", {}).get("endpoint") or ""
            self._send(200, urisys_chat_available(router_endpoint=router or None))

        def _get_network_scan(self, data: dict, qs: dict) -> None:
            try:
                timeout = float((qs.get("timeout") or ["1.5"])[0])
            except ValueError:
                timeout = 1.5
            self._send(200, scan_network(timeout=min(max(timeout, 0.5), 5.0)))

        def _get_urisys_screen(self, data: dict, qs: dict) -> None:
            ep = (qs.get("endpoint") or [""])[0] or data.get("urisys", {}).get("endpoint") or ""
            node_id = (qs.get("node_id") or [""])[0]
            monitor = int((qs.get("monitor") or ["1"])[0])
            source = (qs.get("source") or ["screen"])[0]
            shot = capture_remote_screen(
                UrisysNodeClient(ep or None),
                node_id=node_id,
                monitor=monitor,
                source=source,
            )
            if not shot.get("ok"):
                self._send(502, shot)
                return
            self._send_bytes(200, shot["png"], shot.get("mime") or "image/png")

        def _get_urisys_control(self, data: dict, qs: dict) -> None:
            ep = (qs.get("endpoint") or [""])[0] or data.get("urisys", {}).get("endpoint") or ""
            node_id = (qs.get("node_id") or [""])[0]
            self._send(200, probe_remote_control(UrisysNodeClient(ep or None), node_id=node_id))

        # ── POST handlers ─────────────────────────────────────────────────────

        def _post_uri_call(self, body: dict, data: dict) -> None:
            uri = str(body.get("uri", "")).strip()
            if not uri:
                self._send(400, {"ok": False, "error": "missing uri"})
                return
            self._send(
                200,
                state.call_uri(
                    uri,
                    body.get("payload") or {},
                    bool(body.get("dry_run", True)),
                    approved=bool(body.get("approved", True)),
                ),
            )

        def _post_flow_run(self, body: dict, data: dict) -> None:
            flow_text = str(body.get("flow_text", ""))
            self._send(
                200,
                state.run_flow(
                    flow_text,
                    bool(body.get("dry_run", True)),
                    approved=bool(body.get("approved", True)),
                ),
            )

        def _post_flow_expand(self, body: dict, data: dict) -> None:
            flow_text = str(body.get("flow_text", ""))
            if not flow_text.strip():
                self._send(400, {"ok": False, "error": "missing flow_text"})
                return
            try:
                result = expand_flow(flow_text)
                self._send(200, {"ok": True, **result})
            except ImportError as exc:
                self._send(501, {"ok": False, "error": str(exc), "hint": "pip install -e '.[packs]'"})
            except Exception as exc:
                self._send(400, {"ok": False, "error": str(exc), "type": type(exc).__name__})

        def _post_flow_validate(self, body: dict, data: dict) -> None:
            flow_text = str(body.get("flow_text", ""))
            if not flow_text.strip():
                self._send(400, {"ok": False, "error": "missing flow_text"})
                return
            result = validate_flow(flow_text)
            self._send(200 if result.get("ok") else 400, result)

        def _post_services(self, body: dict, data: dict) -> None:
            service = body.get("service") or body
            if not service.get("uri"):
                self._send(400, {"ok": False, "error": "missing service.uri"})
                return
            data.setdefault("services", []).append(service)
            add_event(data, "service.added", uri=service.get("uri"))
            save_workspace(data)
            self._send(200, {"ok": True, "service": service})

        def _post_peers(self, body: dict, data: dict) -> None:
            peer = body.get("peer") or body
            if not peer.get("id"):
                self._send(400, {"ok": False, "error": "missing peer.id"})
                return
            peers = [p for p in data.get("peers", []) if p.get("id") != peer.get("id")]
            peers.append(peer)
            data["peers"] = peers[-100:]
            add_event(data, "peer.added", peer=peer.get("id"))
            save_workspace(data)
            self._send(200, {"ok": True, "peer": peer})

        def _post_urisys_health(self, body: dict, data: dict) -> None:
            ep = str(body.get("endpoint") or data.get("urisys", {}).get("endpoint") or "")
            client = UrisysNodeClient(ep or None)
            self._send(200, {"ok": True, "endpoint": client.endpoint, "health": client.health()})

        def _post_urisys_call(self, body: dict, data: dict) -> None:
            ep = str(body.get("endpoint") or data.get("urisys", {}).get("endpoint") or "")
            uri = str(body.get("uri", "")).strip()
            if not uri:
                self._send(400, {"ok": False, "error": "missing uri"})
                return
            client = UrisysNodeClient(ep or None)
            self._send(
                200,
                client.call_uri(
                    uri,
                    body.get("payload") or {},
                    approved=bool(body.get("approved", True)),
                    allow_real=bool(body.get("allow_real", True)),
                    dry_run=bool(body.get("dry_run", False)),
                ),
            )

        def _post_urirun_call(self, body: dict, data: dict) -> None:
            uri = str(body.get("uri", "")).strip()
            if not uri:
                self._send(400, {"ok": False, "error": "missing uri"})
                return
            try:
                service_map = parse_json_object(body.get("service_map") or body.get("serviceMap"), name="service_map")
            except Exception as exc:  # noqa: BLE001 - API should return a JSON error.
                self._send(400, {"ok": False, "error": str(exc)})
                return
            registry_path = body.get("registry") or body.get("registry_path")
            registry_json = body.get("registry_json") if isinstance(body.get("registry_json"), dict) else None
            payload = body.get("payload") or {}
            execute = bool(body.get("execute", False))
            if service_map:
                result = call_urirun(
                    uri,
                    payload,
                    registry_path=registry_path,
                    registry=registry_json,
                    execute=execute,
                    service_map=service_map,
                    timeout=float(body.get("timeout", 30.0)),
                    validate=not bool(body.get("no_validate", False)),
                )
            else:
                policy = {"execute": {"allow": ["**"]}} if execute else None
                result = urirun_dispatch(
                    uri,
                    payload,
                    registry_path=registry_path,
                    registry=registry_json,
                    execute=execute,
                    policy=policy,
                )
                if result is None:
                    # Compatibility path: without a local registry, keep the
                    # old dry-run service envelope for clients that use this
                    # endpoint as a transport planner.
                    result = call_urirun(
                        uri,
                        payload,
                        registry_path=registry_path,
                        registry=registry_json,
                        execute=execute,
                        timeout=float(body.get("timeout", 30.0)),
                        validate=not bool(body.get("no_validate", False)),
                    )
            self._send(200, result)

        def _post_urisys_screen(self, body: dict, data: dict) -> None:
            ep = str(body.get("endpoint") or data.get("urisys", {}).get("endpoint") or "")
            node_id = str(body.get("node_id") or "")
            monitor = int(body.get("monitor") or 1)
            source = str(body.get("source") or "screen")
            shot = capture_remote_screen(
                UrisysNodeClient(ep or None),
                node_id=node_id,
                monitor=monitor,
                source=source,
            )
            if shot.get("ok") and shot.get("png"):
                shot = dict(shot)
                shot["png_b64"] = base64.b64encode(shot.pop("png")).decode("ascii")
            self._send(200, shot)

        def _post_urisys_control(self, body: dict, data: dict) -> None:
            ep = str(body.get("endpoint") or data.get("urisys", {}).get("endpoint") or "")
            node_id = str(body.get("node_id") or "")
            self._send(200, probe_remote_control(UrisysNodeClient(ep or None), node_id=node_id))

        def _post_chat_send(self, body: dict, data: dict) -> None:
            channel = body.get("channel") or {}
            text = str(body.get("text") or body.get("prompt") or "").strip()
            router = str(body.get("router_endpoint") or body.get("endpoint") or data.get("urisys", {}).get("endpoint") or "")
            self._send(
                200,
                send_chat_message_routed(
                    channel,
                    text,
                    router_endpoint=router or None,
                    dry_run=bool(body.get("dry_run", False)),
                ),
            )

        def _post_chat_migrate(self, body: dict, data: dict) -> None:
            router = str(body.get("router_endpoint") or body.get("endpoint") or data.get("urisys", {}).get("endpoint") or "")
            self._send(
                200,
                migrate_local_chat_to_urisys(
                    router_endpoint=router or None,
                    dry_run=bool(body.get("dry_run", False)),
                    force=bool(body.get("force", False)),
                ),
            )

        def _post_webrtc_signal(self, body: dict, data: dict) -> None:
            room = str(body.get("room") or "").strip()
            from_peer = str(body.get("from") or "").strip()
            signal_type = str(body.get("type") or "").strip()
            self._send(
                200,
                post_signal(
                    room,
                    from_peer=from_peer,
                    signal_type=signal_type,
                    data=body.get("data"),
                ),
            )

        def _post_chat_channels(self, body: dict, data: dict) -> None:
            self._send(
                200,
                list_chat_channels(
                    timeout=min(max(float(body.get("timeout", 1.5)), 0.5), 5.0),
                    scan_subnet=bool(body.get("scan_subnet", True)),
                    local_host=state.host,
                    local_port=state.port,
                ),
            )

        def _post_network_scan(self, body: dict, data: dict) -> None:
            self._send(
                200,
                scan_network(
                    timeout=min(max(float(body.get("timeout", 1.5)), 0.5), 5.0),
                    scan_subnet=bool(body.get("scan_subnet", True)),
                ),
            )

        def _post_voice_plan(self, body: dict, data: dict) -> None:
            text = str(body.get("text", "")).strip()
            ep = str(body.get("endpoint") or data.get("urisys", {}).get("endpoint") or "")
            client = UrisysNodeClient(ep or None) if ep else UrisysNodeClient()
            planner = body.get("planner")
            self._send(
                200,
                plan_voice_command(text, client=client, planner=str(planner) if planner else None),
            )

        def _post_voice_run(self, body: dict, data: dict) -> None:
            ep = str(body.get("endpoint") or data.get("urisys", {}).get("endpoint") or "")
            text = str(body.get("text", "")).strip()
            client = UrisysNodeClient(ep or None) if ep else None
            self._send(
                200,
                run_voice_command(
                    text,
                    client=client,
                    dry_run=bool(body.get("dry_run", False)),
                    speak=bool(body.get("speak", True)),
                ),
            )

        def _post_voice_install_packs(self, body: dict, data: dict) -> None:
            ep = str(body.get("endpoint") or data.get("urisys", {}).get("endpoint") or "")
            client = UrisysNodeClient(ep or None) if ep else None
            self._send(
                200,
                install_voice_packs(
                    client=client,
                    dry_run=bool(body.get("dry_run", False)),
                ),
            )

        def _post_flow_run_file(self, body: dict, data: dict) -> None:
            ep = str(body.get("endpoint") or data.get("urisys", {}).get("endpoint") or "")
            flow_ref = str(body.get("flow") or body.get("flow_ref") or "").strip()
            if not flow_ref:
                self._send(400, {"ok": False, "error": "missing flow"})
                return
            client = UrisysNodeClient(ep or None) if ep else None
            self._send(
                200,
                run_flow_file(
                    flow_ref,
                    client=client,
                    dry_run=bool(body.get("dry_run", False)),
                ),
            )

    Handler._GET_ROUTES = {
        "/health": Handler._get_health,
        "/api/health": Handler._get_health,
        "/api/services": Handler._get_services,
        "/api/flows": Handler._get_flows,
        "/api/peers": Handler._get_peers,
        "/api/routes": Handler._get_routes,
        "/api/examples": Handler._get_examples,
        "/api/packs": Handler._get_packs,
        "/api/urirun": Handler._get_urirun,
        "/api/voice/catalog": Handler._get_voice_catalog,
        "/api/voice/capabilities": Handler._get_voice_capabilities,
        "/api/webrtc/capabilities": Handler._get_webrtc_capabilities,
        "/api/webrtc/signal": Handler._get_webrtc_signal,
        "/api/chat/channels": Handler._get_chat_channels,
        "/api/chat/history": Handler._get_chat_history,
        "/api/chat/status": Handler._get_chat_status,
        "/api/network/scan": Handler._get_network_scan,
        "/api/urisys/screen.png": Handler._get_urisys_screen,
        "/api/urisys/control-test": Handler._get_urisys_control,
    }
    Handler._POST_ROUTES = {
        "/api/uri/call": Handler._post_uri_call,
        "/api/flow/run": Handler._post_flow_run,
        "/api/flow/expand": Handler._post_flow_expand,
        "/api/flow/validate": Handler._post_flow_validate,
        "/api/services": Handler._post_services,
        "/api/peers": Handler._post_peers,
        "/api/urisys/health": Handler._post_urisys_health,
        "/api/urisys/call": Handler._post_urisys_call,
        "/api/urirun/call": Handler._post_urirun_call,
        "/api/urisys/screen": Handler._post_urisys_screen,
        "/api/urisys/control-test": Handler._post_urisys_control,
        "/api/chat/send": Handler._post_chat_send,
        "/api/chat/migrate": Handler._post_chat_migrate,
        "/api/webrtc/signal": Handler._post_webrtc_signal,
        "/api/chat/channels": Handler._post_chat_channels,
        "/api/network/scan": Handler._post_network_scan,
        "/api/voice/plan": Handler._post_voice_plan,
        "/api/voice/run": Handler._post_voice_run,
        "/api/voice/install-packs": Handler._post_voice_install_packs,
        "/api/flow/run-file": Handler._post_flow_run_file,
    }
    return Handler


class RuntimeServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = int(port)
        self.state = RuntimeState(host, self.port)
        self.httpd = bind_runtime_server(host, self.port, make_handler(self.state))
        self.thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        host = "127.0.0.1" if self.host in {"0.0.0.0", ""} else self.host
        return f"http://{host}:{self.port}"

    def start(self) -> "RuntimeServer":
        if self.thread and self.thread.is_alive():
            return self
        self.thread = threading.Thread(target=self.httpd.serve_forever, name="ifuri-runtime", daemon=True)
        self.thread.start()
        return self

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        if self.thread:
            self.thread.join(timeout=2)
