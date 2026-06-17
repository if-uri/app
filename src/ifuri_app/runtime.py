from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from typing import Any
from urllib.parse import urlparse

from . import __version__
from .flow_engine import dry_run_flow, dry_run_uri, expand_flow
from .storage import add_event, load_workspace, save_workspace, now_iso


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class RuntimeState:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port

    def load(self) -> dict[str, Any]:
        data = load_workspace()
        data["node"]["port"] = self.port
        save_workspace(data)
        return data

    def health(self) -> dict[str, Any]:
        data = self.load()
        return {
            "ok": True,
            "name": "ifURI runtime",
            "version": __version__,
            "node": data.get("node", {}),
            "services": len(data.get("services", [])),
            "groups": len(data.get("groups", [])),
            "time": now_iso(),
        }

    def call_uri(self, uri: str, payload: dict[str, Any] | None = None, dry_run: bool = True) -> dict[str, Any]:
        data = self.load()
        result = dry_run_uri(uri, payload)
        result["dry_run"] = dry_run
        if not dry_run:
            result["ok"] = False
            result["message"] = "non-dry execution is intentionally not implemented in the prototype runtime"
        add_event(data, "uri.call", uri=uri, dry_run=dry_run, ok=result.get("ok"))
        save_workspace(data)
        return result

    def run_flow(self, flow_text: str, dry_run: bool = True) -> dict[str, Any]:
        data = self.load()
        result = dry_run_flow(flow_text)
        result["dry_run"] = dry_run
        if not dry_run:
            result["ok"] = False
            result["message"] = "non-dry flow execution is intentionally not implemented in the prototype runtime"
        add_event(data, "flow.run", dry_run=dry_run, steps=len(result.get("steps", [])))
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

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            data = state.load()
            if path in {"/", "/health", "/api/health"}:
                self._send(200, state.health())
            elif path == "/api/services":
                self._send(200, {"ok": True, "services": data.get("services", [])})
            elif path == "/api/flows":
                self._send(200, {"ok": True, "groups": data.get("groups", [])})
            elif path == "/api/peers":
                self._send(200, {"ok": True, "peers": data.get("peers", [])})
            elif path == "/api/routes":
                self._send(200, {"ok": True, "schemes": sorted({s.get("scheme", "unknown") for s in data.get("services", [])})})
            else:
                self._send(404, {"ok": False, "error": "not_found", "path": path})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            body = self._read_json()
            if body.get("_error"):
                self._send(400, {"ok": False, "error": body["_error"]})
                return
            data = state.load()
            if path == "/api/uri/call":
                uri = str(body.get("uri", "")).strip()
                if not uri:
                    self._send(400, {"ok": False, "error": "missing uri"})
                    return
                self._send(200, state.call_uri(uri, body.get("payload") or {}, bool(body.get("dry_run", True))))
            elif path == "/api/flow/run":
                flow_text = str(body.get("flow_text", ""))
                self._send(200, state.run_flow(flow_text, bool(body.get("dry_run", True))))
            elif path == "/api/flow/expand":
                flow_text = str(body.get("flow_text", ""))
                self._send(200, {"ok": True, **expand_flow(flow_text)})
            elif path == "/api/services":
                service = body.get("service") or body
                if not service.get("uri"):
                    self._send(400, {"ok": False, "error": "missing service.uri"})
                    return
                data.setdefault("services", []).append(service)
                add_event(data, "service.added", uri=service.get("uri"))
                save_workspace(data)
                self._send(200, {"ok": True, "service": service})
            elif path == "/api/peers":
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
            else:
                self._send(404, {"ok": False, "error": "not_found", "path": path})

    return Handler


class RuntimeServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = int(port)
        self.state = RuntimeState(host, self.port)
        self.httpd = ThreadingHTTPServer((host, self.port), make_handler(self.state))
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
