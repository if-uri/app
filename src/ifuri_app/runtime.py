# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

from __future__ import annotations

import threading

from .runtime_bind import (
    PortInUseError,
    ThreadingHTTPServer,
    bind_runtime_server,
    find_free_port,
    format_port_in_use_error,
    _port_available,
)
from .runtime_handlers import make_handler
from .runtime_state import RuntimeState, load_urirun_policy as _load_urirun_policy


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
