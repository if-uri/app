# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Workspace-backed runtime state extracted from ``runtime.py`` (IFURI-239)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import __version__
from .flow_compile import uri2flow_available
from .flow_engine import dry_run_flow, dry_run_uri, expand_flow
from .flow_runner import examples_root
from .packs.runtime import dispatch_local_uri, get_local_uri_runtime, local_runtime_info
from .storage import add_event, load_workspace, now_iso, save_workspace
from .urirun_bridge import (
    default_urirun_registry,
    dispatch_local as urirun_dispatch,
    urirun_info,
)
from .urisys_client import UrisysNodeClient


def load_urirun_policy(data: dict[str, Any], approved: bool) -> dict[str, Any] | None:
    """Policy for in-process urirun execution."""
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
        urirun_reg = (data.get("urirun") or {}).get("registry") or default_urirun_registry()
        urirun_resp = urirun_dispatch(
            uri,
            payload,
            execute=not dry_run,
            confirm=approved,
            policy=load_urirun_policy(data, approved) if not dry_run else None,
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
        urirun_pol = load_urirun_policy(data, approved)
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
