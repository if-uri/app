# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Launch helper for the ``if-uri/examples/11-novnc_lan_flow`` Docker/noVNC demo.

The example runs Chromium desktops inside noVNC containers driven by a URI flow,
plus a dashboard that embeds the noVNC views. This module locates the example
directory, builds the dashboard URL, and assembles the ``docker compose``
commands the desktop app shells out to. Pure/testable apart from
:func:`docker_available`, which only probes ``PATH``.

Ports mirror the example's Makefile defaults and can be overridden through the
environment (``DASHBOARD_PORT``, ``PC1_NOVNC_PORT`` …), matching how the example
itself is parameterised.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

DEMO_REL = "examples/11-novnc_lan_flow"

# (env var, query-string key, default) for the dashboard URL.
_PORT_SPEC = (
    ("DASHBOARD_PORT", None, "8192"),
    ("PC1_NOVNC_PORT", "pc1NovncPort", "7901"),
    ("PC2_NOVNC_PORT", "pc2NovncPort", "7902"),
    ("PC1_API_PORT", "pc1ApiPort", "9001"),
    ("PC2_API_PORT", "pc2ApiPort", "9002"),
)


def demo_dir() -> Path | None:
    """Resolve the noVNC example directory, or ``None`` if it can't be found.

    Honours ``IFURI_NOVNC_DEMO_DIR``; otherwise looks for ``examples/11-…``
    next to the ``if-uri/app`` package root (app and examples are siblings).
    """
    env = os.environ.get("IFURI_NOVNC_DEMO_DIR")
    if env:
        path = Path(env).expanduser()
        return path if path.is_dir() else None
    # src/ifuri_app/novnc_demo.py -> parents[2] == if-uri/app, parents[3] == if-uri
    repo_root = Path(__file__).resolve().parents[3]
    candidate = repo_root / DEMO_REL
    return candidate if candidate.is_dir() else None


def read_env_file(directory: Path | None) -> dict[str, str]:
    """Parse ``KEY=VALUE`` lines from the demo's ``.env`` (docker compose reads it too)."""
    if directory is None:
        return {}
    env_path = directory / ".env"
    if not env_path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def dashboard_ports(directory: Path | None = None) -> dict[str, str]:
    """Effective ports with docker compose precedence: shell env > .env file > default.

    ``directory`` defaults to :func:`demo_dir` so the URL the app opens matches the
    ports ``docker compose`` actually publishes from the example's ``.env``.
    """
    if directory is None:
        directory = demo_dir()
    file_env = read_env_file(directory)
    return {
        env: os.environ.get(env) or file_env.get(env) or default
        for env, _key, default in _PORT_SPEC
    }


def dashboard_url(ports: dict[str, str] | None = None, *, directory: Path | None = None) -> str:
    """Build the dashboard URL (with noVNC/API port query params)."""
    ports = ports or dashboard_ports(directory)
    dash = ports.get("DASHBOARD_PORT", "8192")
    query = "&".join(
        f"{key}={ports.get(env, default)}"
        for env, key, default in _PORT_SPEC
        if key is not None
    )
    return f"http://127.0.0.1:{dash}/?{query}"


def docker_available() -> bool:
    """True when a ``docker`` CLI is on PATH (compose v2 ships with it)."""
    return shutil.which("docker") is not None


def compose_args(action: str) -> list[str]:
    """``docker compose`` argv for ``up`` / ``down`` / ``logs``."""
    base = ["docker", "compose"]
    if action == "up":
        return base + ["up", "-d", "--build"]
    if action == "down":
        return base + ["down", "-v", "--remove-orphans"]
    if action == "logs":
        return base + ["logs", "--tail=200"]
    raise ValueError(f"unknown compose action: {action!r}")


def launch_info() -> dict[str, Any]:
    """Snapshot used by the GUI: directory, dashboard URL, docker availability."""
    directory = demo_dir()
    return {
        "dir": str(directory) if directory else None,
        "available": directory is not None and docker_available(),
        "docker": docker_available(),
        "dashboard_url": dashboard_url(),
    }
