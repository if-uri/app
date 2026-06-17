"""Compile compact URI flows via uri2flow (with legacy shape compat)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class FlowCompileError(RuntimeError):
    """Flow text could not be compiled."""


def uri2flow_available() -> bool:
    try:
        import uri2flow  # noqa: F401

        return True
    except ImportError:
        return False


def _parse_flow_input(flow: str | dict[str, Any] | Path) -> dict[str, Any]:
    if isinstance(flow, dict):
        return flow
    if isinstance(flow, Path) or (isinstance(flow, str) and "\n" not in flow and Path(str(flow)).is_file()):
        from uri2flow import load_flow

        doc = load_flow(flow)
        return {
            "flow": {"id": doc.id, "description": doc.description},
            "do": [
                {
                    **({"id": step.id} if step.id else {}),
                    "uri": step.uri,
                    **({"payload": step.payload} if step.payload else {}),
                    **({"after": step.after} if step.after else {}),
                }
                for step in doc.steps
            ],
        }
    import yaml

    data = yaml.safe_load(str(flow)) or {}
    if not isinstance(data, dict):
        raise FlowCompileError("flow document must be a YAML mapping")
    return data


def expand_flow_compiled(flow: str | dict[str, Any] | Path, *, flow_id: str | None = None) -> dict[str, Any]:
    """Expand compact flow YAML using uri2flow; add legacy workflow_graph key."""
    if not uri2flow_available():
        raise ImportError("uri2flow is required — pip install -e '.[packs]'")

    from uri2flow import expand_flow as _expand
    from uri2flow import parse_flow, validate_expanded_flow, validate_flow_document

    data = _parse_flow_input(flow)
    if flow_id:
        data.setdefault("flow", {})
        if isinstance(data["flow"], dict):
            data["flow"]["id"] = flow_id

    doc = parse_flow(data)
    expanded = _expand(doc)
    validation: dict[str, Any] = {"document": [], "expanded": []}
    try:
        validation["document"] = validate_flow_document(data)
        validation["expanded"] = validate_expanded_flow(data)
    except ValueError as exc:
        validation["error"] = str(exc)
    graph = expanded.get("graph") or {}
    legacy_nodes = [
        {
            "id": node.get("id"),
            "uri": node.get("uri"),
            "scheme": _scheme(node.get("uri") or ""),
            **({"operation": node.get("operation")} if node.get("operation") else {}),
            **({"kind": node.get("kind")} if node.get("kind") else {}),
            **({"depends_on": node.get("depends_on")} if node.get("depends_on") else {}),
        }
        for node in graph.get("nodes") or []
        if node.get("uri")
    ]
    return {
        "compiler": "uri2flow",
        "nl2uri": expanded.get("nl2uri"),
        "graph": graph,
        "workflow_graph": {
            "id": graph.get("id") or doc.id,
            "nodes": legacy_nodes,
            "edges": graph.get("edges") or [],
        },
        "validation": validation,
    }


def flow_steps_from_document(flow: str | dict[str, Any] | Path) -> list[dict[str, Any]]:
    """Extract executable URI steps from a compact flow document."""
    if uri2flow_available():
        from uri2flow import parse_flow

        data = _parse_flow_input(flow)
        doc = parse_flow(data)
        steps: list[dict[str, Any]] = []
        for step in doc.steps:
            if not step.uri:
                continue
            item: dict[str, Any] = {
                "id": step.id or step.uri.split("://", 1)[0],
                "uri": step.uri,
                "payload": step.payload or {},
            }
            if step.after:
                item["after"] = step.after
            steps.append(item)
        if steps:
            return steps

    from .flow_engine import extract_steps

    if isinstance(flow, Path):
        text = flow.read_text(encoding="utf-8")
    elif isinstance(flow, dict):
        import yaml

        text = yaml.safe_dump(flow, allow_unicode=True)
    else:
        text = str(flow)
    return [{"id": s["id"], "uri": s["uri"], "payload": {}} for s in extract_steps(text)]


def validate_flow_compiled(flow: str | dict[str, Any] | Path) -> dict[str, Any]:
    """Validate compact flow via uri2flow; return warnings or error."""
    if not uri2flow_available():
        raise ImportError("uri2flow is required — pip install -e '.[packs]'")

    from uri2flow import validate_expanded_flow, validate_flow_document

    data = _parse_flow_input(flow)
    try:
        doc_warnings = validate_flow_document(data)
        expanded_warnings = validate_expanded_flow(data)
        return {"ok": True, "document_warnings": doc_warnings, "expanded_warnings": expanded_warnings}
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}


def _scheme(uri: str) -> str:
    if "://" not in uri:
        return "unknown"
    return uri.split("://", 1)[0].lower()
