"""Load *.uri.flow.yaml steps and execute them via urisys-node."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .flow_compile import flow_steps_from_document
from .urisys_client import UrisysNodeClient

_URI_STEP = re.compile(
    r"^\s*-\s+(?:id:\s*(?P<id>\S+)\s*\n\s*)?(?:uri:\s*)?(?P<uri>[a-zA-Z][a-zA-Z0-9+.-]*://\S+)",
    re.MULTILINE,
)


def examples_root() -> Path:
    import os

    env = os.environ.get("URISYS_EXAMPLES_ROOT") or os.environ.get("IFURI_EXAMPLES_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    # tellmesh layout: if-uri/app -> tellmesh/urisys-examples
    here = Path(__file__).resolve()
    candidate = here.parents[4] / "tellmesh" / "urisys-examples"
    if candidate.is_dir():
        return candidate
    return Path.home() / "github" / "tellmesh" / "urisys-examples"


def resolve_flow_path(ref: str) -> Path:
    p = Path(ref)
    if p.is_file():
        return p.resolve()
    root = examples_root()
    for candidate in (root / ref, root / "lenovo-remote" / ref, root / ref.lstrip("/")):
        if candidate.is_file():
            return candidate.resolve()
    return (root / ref).resolve()


def load_flow_steps(flow_path: Path) -> list[dict[str, Any]]:
    try:
        return flow_steps_from_document(flow_path)
    except Exception:
        text = flow_path.read_text(encoding="utf-8")
        from .flow_engine import extract_steps

        return [{"id": item["id"], "uri": item["uri"], "payload": {}} for item in extract_steps(text)]


def run_flow_file(
    flow_ref: str | Path,
    *,
    client: UrisysNodeClient | None = None,
    dry_run: bool = False,
    approved: bool = True,
    allow_real: bool = True,
) -> dict[str, Any]:
    flow_path = resolve_flow_path(str(flow_ref))
    if not flow_path.is_file():
        return {"ok": False, "error": f"flow not found: {flow_ref}", "resolved": str(flow_path)}
    node = client or UrisysNodeClient()
    steps_out: list[dict[str, Any]] = []
    ok = True
    for step in load_flow_steps(flow_path):
        if dry_run:
            steps_out.append({"id": step["id"], "uri": step["uri"], "ok": True, "dry_run": True})
            continue
        resp = node.call_uri(
            step["uri"],
            step.get("payload") or {},
            approved=approved,
            allow_real=allow_real,
        )
        step_ok = bool(resp.get("ok", True)) and not resp.get("error")
        ok = ok and step_ok
        steps_out.append({"id": step["id"], "uri": step["uri"], "ok": step_ok, "response": resp})
        if not step_ok:
            break
    return {
        "ok": ok,
        "flow": str(flow_path),
        "dry_run": dry_run,
        "steps": steps_out,
    }
