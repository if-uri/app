"""LAN discovery: ifURI peers, urisys-node hosts, MCP/agent services."""

from __future__ import annotations

import ipaddress
import json
import os
import socket
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .discovery import discover
from .storage import load_workspace, now_iso
from .urisys_client import UrisysNodeClient

SERVICE_SCHEMES = frozenset({"mcp", "agent", "a2a", "llm", "browser"})


def _local_ipv4() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


def _subnet_hosts(ip: str) -> list[str]:
    try:
        net = ipaddress.ip_network(f"{ip}/24", strict=False)
        return [str(h) for h in net.hosts()]
    except ValueError:
        return []


def probe_urisys_node(host: str, port: int = 8790, *, timeout: float = 0.35) -> dict[str, Any] | None:
    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not data.get("ok"):
            return None
        return {
            "kind": "urisys-node",
            "host": host,
            "port": port,
            "endpoint": f"http://{host}:{port}",
            "node_id": data.get("node_id"),
            "him_driver": data.get("him_driver"),
            "routes_count": data.get("routes_count"),
            "packs_loaded": data.get("packs_loaded") or [],
            "health": data,
        }
    except Exception:
        return None


def probe_ifuri_peer(api_url: str, *, timeout: float = 0.5) -> dict[str, Any] | None:
    base = api_url.rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/health", timeout=timeout) as resp:
            health = json.loads(resp.read().decode("utf-8"))
        services: list[dict[str, Any]] = []
        try:
            with urllib.request.urlopen(f"{base}/api/services", timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                services = body.get("services") or []
        except Exception:
            pass
        return {"api_url": base, "health": health, "services": services}
    except Exception:
        return None


def _collect_local_services() -> list[dict[str, Any]]:
    data = load_workspace()
    out: list[dict[str, Any]] = []
    for svc in data.get("services") or []:
        scheme = str(svc.get("scheme") or "").lower()
        if scheme not in SERVICE_SCHEMES and scheme not in {"ifuri"}:
            continue
        if svc.get("enabled") is False:
            continue
        out.append(
            {
                "name": svc.get("name") or svc.get("uri"),
                "scheme": scheme,
                "uri": svc.get("uri"),
                "scope": svc.get("scope", "private"),
                "source": "local",
                "enabled": bool(svc.get("enabled", True)),
            }
        )
    return out


def _services_from_peers(peers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for peer in peers:
        peer_name = peer.get("name") or peer.get("id") or peer.get("address")
        for svc in peer.get("services") or []:
            scheme = str(svc.get("scheme") or "").lower()
            if scheme not in SERVICE_SCHEMES:
                continue
            out.append(
                {
                    "name": svc.get("name") or svc.get("uri"),
                    "scheme": scheme,
                    "uri": svc.get("uri"),
                    "scope": svc.get("scope", "shared"),
                    "source": f"peer:{peer_name}",
                    "peer_id": peer.get("id"),
                    "peer_url": peer.get("api_url"),
                    "enabled": bool(svc.get("enabled", True)),
                }
            )
    return out


def scan_urisys_nodes(
    *,
    timeout: float = 1.5,
    port: int = 8790,
    scan_subnet: bool = True,
    extra_hosts: list[str] | None = None,
) -> list[dict[str, Any]]:
    hosts: set[str] = {"127.0.0.1", "localhost"}
    if extra_hosts:
        hosts.update(h for h in extra_hosts if h)
    data = load_workspace()
    ep = (data.get("urisys") or {}).get("endpoint") or os.environ.get("URISYS_NODE_ENDPOINT")
    if ep:
        try:
            from urllib.parse import urlparse

            parsed = urlparse(str(ep))
            if parsed.hostname:
                hosts.add(parsed.hostname)
        except Exception:
            pass
    local = _local_ipv4()
    if scan_subnet and local:
        hosts.update(_subnet_hosts(local))
    found: dict[str, dict[str, Any]] = {}
    per_host_timeout = min(0.4, max(0.15, timeout / 8))
    with ThreadPoolExecutor(max_workers=48) as pool:
        futures = {pool.submit(probe_urisys_node, h, port, timeout=per_host_timeout): h for h in hosts}
        deadline = timeout
        try:
            for fut in as_completed(futures, timeout=deadline):
                hit = fut.result()
                if hit:
                    found[hit["endpoint"]] = hit
        except TimeoutError:
            pass
    return list(found.values())


def scan_network(*, timeout: float = 1.5, scan_subnet: bool = True) -> dict[str, Any]:
    """Full LAN scan: ifURI peers + urisys-node + MCP/agent services."""
    ifuri_peers = discover(timeout=min(timeout, 2.0))
    urisys_nodes = scan_urisys_nodes(timeout=timeout, scan_subnet=scan_subnet)
    local_node = probe_urisys_node("127.0.0.1")
    if local_node and local_node["endpoint"] not in {n["endpoint"] for n in urisys_nodes}:
        urisys_nodes.insert(0, local_node)

    services = _collect_local_services()
    enriched_peers: list[dict[str, Any]] = []
    for peer in ifuri_peers:
        p = dict(peer)
        api_url = p.get("api_url") or (
            f"http://{p.get('address')}:{p.get('api_port', 8765)}" if p.get("address") else None
        )
        if api_url and not p.get("services"):
            detail = probe_ifuri_peer(api_url)
            if detail:
                p["services"] = detail.get("services") or []
                p["live_health"] = detail.get("health")
        p.setdefault("api_url", api_url)
        enriched_peers.append(p)

    services.extend(_services_from_peers(enriched_peers))

    # Dedupe services by uri+source
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for svc in services:
        key = (str(svc.get("uri")), str(svc.get("source")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(svc)

    mcp_agent = [s for s in deduped if s.get("scheme") in {"mcp", "agent", "a2a"}]
    llm_services = [s for s in deduped if s.get("scheme") == "llm"]
    mdns_nodes = try_mdns_urisys(min(timeout, 2.0))

    return {
        "ok": True,
        "scanned_at": now_iso(),
        "ifuri_peers": enriched_peers,
        "urisys_nodes": urisys_nodes,
        "mdns_nodes": mdns_nodes,
        "services": deduped,
        "mcp_agent_services": mcp_agent,
        "llm_services": llm_services,
        "counts": {
            "ifuri_peers": len(enriched_peers),
            "urisys_nodes": len(urisys_nodes),
            "mcp_agent": len(mcp_agent),
            "services_total": len(deduped),
        },
    }


def try_mdns_urisys(timeout: float = 2.0) -> list[dict[str, Any]]:
    try:
        from urisysnode.client import discover_mdns  # type: ignore

        return discover_mdns(timeout)
    except Exception:
        return []
