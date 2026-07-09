# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""HTTP bind helpers extracted from ``runtime.py`` (IFURI-239)."""

from __future__ import annotations

import errno
import socket
import subprocess
from http.server import HTTPServer
from socketserver import ThreadingMixIn


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
