# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

from __future__ import annotations

import json
import socket
import threading
import time
from typing import Any

from . import DISCOVERY_PORT
from .storage import load_workspace, save_workspace, now_iso

MAGIC_DISCOVER = "ifuri.discover"
MAGIC_PEER = "ifuri.peer"


def local_descriptor(api_port: int = 8765) -> dict[str, Any]:
    data = load_workspace()
    node = dict(data.get("node", {}))
    node["port"] = api_port
    services = [s for s in data.get("services", []) if s.get("enabled", True) and s.get("scope") in {"shared", "public"}]
    return {
        "type": MAGIC_PEER,
        "id": node.get("id"),
        "name": node.get("name"),
        "role": node.get("role", "host"),
        "api_port": api_port,
        "api_path": "/api/uri/call",
        "schemes": sorted({s.get("scheme", "unknown") for s in services}),
        "services": services,
        "time": now_iso(),
    }


class DiscoveryResponder:
    def __init__(self, api_port: int = 8765, discovery_port: int = DISCOVERY_PORT):
        self.api_port = int(api_port)
        self.discovery_port = int(discovery_port)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._sock: socket.socket | None = None

    def start(self) -> "DiscoveryResponder":
        if self._thread and self._thread.is_alive():
            return self
        self._thread = threading.Thread(target=self._loop, name="ifuri-discovery", daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock = sock
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", self.discovery_port))
        except OSError:
            return
        sock.settimeout(0.4)
        while not self._stop.is_set():
            try:
                raw, addr = sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                msg = json.loads(raw.decode("utf-8"))
            except Exception:
                continue
            if msg.get("type") != MAGIC_DISCOVER:
                continue
            reply = local_descriptor(self.api_port)
            reply["address"] = socket.gethostbyname(socket.gethostname()) if socket.gethostname() else addr[0]
            try:
                sock.sendto(json.dumps(reply).encode("utf-8"), addr)
            except OSError:
                pass


def discover(timeout: float = 1.2, api_port: int = 8765, discovery_port: int = DISCOVERY_PORT) -> list[dict[str, Any]]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(0.2)
    message = json.dumps({"type": MAGIC_DISCOVER, "api_port": api_port, "time": now_iso()}).encode("utf-8")
    peers: dict[str, dict[str, Any]] = {}
    try:
        sock.sendto(message, ("255.255.255.255", discovery_port))
        end = time.time() + timeout
        while time.time() < end:
            try:
                raw, addr = sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                msg = json.loads(raw.decode("utf-8"))
            except Exception:
                continue
            if msg.get("type") != MAGIC_PEER:
                continue
            msg.setdefault("address", addr[0])
            msg.setdefault("api_url", f"http://{msg['address']}:{msg.get('api_port', api_port)}")
            peer_id = str(msg.get("id") or f"{addr[0]}:{msg.get('api_port', api_port)}")
            peers[peer_id] = msg
    finally:
        sock.close()
    data = load_workspace()
    known = {p.get("id"): p for p in data.get("peers", [])}
    for peer_id, peer in peers.items():
        known[peer_id] = peer
    data["peers"] = list(known.values())[-100:]
    save_workspace(data)
    return list(peers.values())
