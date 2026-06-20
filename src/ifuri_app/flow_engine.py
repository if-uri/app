# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

from __future__ import annotations

from typing import Any

from .flow_compile import expand_flow_compiled, flow_steps_from_document, uri2flow_available


def expand_flow(flow_text: str, flow_id: str | None = None) -> dict[str, Any]:
    """Expand compact flow YAML — uri2flow when installed."""
    if uri2flow_available():
        return expand_flow_compiled(flow_text, flow_id=flow_id)
    return _legacy_expand_flow(flow_text, flow_id=flow_id)


def _legacy_expand_flow(flow_text: str, flow_id: str | None = None) -> dict[str, Any]:
    import warnings

    warnings.warn(
        "uri2flow not installed — using legacy regex expand. pip install -e '.[tellmesh]' or uv sync --group tellmesh",
        stacklevel=3,
    )
    fid = flow_id or flow_id_from_text(flow_text)
    steps = extract_steps(flow_text)
    nodes = [
        {
            "id": step["id"],
            "uri": step["uri"],
            "scheme": step["scheme"],
            "line": step["line"],
        }
        for step in steps
    ]
    edges = []
    for left, right in zip(nodes, nodes[1:]):
        edges.append({"from": left["id"], "to": right["id"], "type": "sequence"})
    return {
        "compiler": "legacy",
        "workflow_graph": {"id": fid, "nodes": nodes, "edges": edges},
        "graph": {"id": fid, "nodes": nodes, "edges": edges},
    }


# --- kept for dry-run routing and regex fallback when uri2flow absent ---

import json
import re
import time
from urllib.parse import urlparse

URI_RE = re.compile(r"([a-zA-Z][a-zA-Z0-9+.-]*://[^\s,\]\)}'\"]+)")
TRAILING = ":;,."


def clean_uri(value: str) -> str:
    return value.strip().rstrip(TRAILING)


def uri_scheme(uri: str) -> str:
    if "://" not in uri:
        return "unknown"
    return uri.split("://", 1)[0].lower()


def extract_steps(flow_text: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for line_no, line in enumerate(flow_text.splitlines(), start=1):
        for match in URI_RE.finditer(line):
            uri = clean_uri(match.group(1))
            steps.append({
                "id": f"n{len(steps)+1}",
                "line": line_no,
                "uri": uri,
                "scheme": uri_scheme(uri),
                "raw": line.rstrip(),
            })
    return steps


def flow_id_from_text(flow_text: str, default: str = "flow") -> str:
    for line in flow_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("id:"):
            return stripped.split(":", 1)[1].strip() or default
    return default


def classify_route(uri: str) -> dict[str, Any]:
    scheme = uri_scheme(uri)
    parsed = urlparse(uri)
    route = {"scheme": scheme, "target": parsed.netloc or "local", "mode": "dry-run", "kind": "unknown"}
    if scheme == "ifuri":
        route.update({"kind": "peer", "mode": "remote-envelope"})
    elif scheme in {"mcp", "agent", "llm"}:
        route.update({"kind": "service", "mode": "local-or-remote-adapter"})
    elif scheme in {"flow", "workflow"}:
        route.update({"kind": "workflow", "mode": "expand-and-run"})
    elif scheme in {"browser", "shell", "python", "http", "https", "file"}:
        route.update({"kind": "adapter", "mode": "guarded"})
    return route


def dry_run_uri(uri: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    route = classify_route(uri)
    return {
        "ok": True,
        "dry_run": True,
        "uri": uri,
        "route": route,
        "payload": payload or {},
        "message": f"planned {route['kind']} call via {route['scheme']}://",
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def dry_run_flow(flow_text: str) -> dict[str, Any]:
    graph = expand_flow(flow_text)
    nodes = graph.get("workflow_graph", {}).get("nodes") or graph.get("graph", {}).get("nodes") or []
    results = []
    for node in nodes:
        uri = node.get("uri")
        if uri:
            results.append(dry_run_uri(uri))
    return {"ok": True, "dry_run": True, "graph": graph, "steps": results}


def as_pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
