# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Voice command planning: catalog → regex → llm:// → voice:// fallback."""

from __future__ import annotations

import json
import os
import re
from difflib import SequenceMatcher
from typing import Any

from .flow_runner import examples_root
from .urisys_client import UrisysNodeClient

LLM_PACK_NAMES = frozenset({"llm", "urillm"})

# Fast path — kept for offline / zero-latency matches.
VOICE_FLOW_TRIGGERS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(health|zdrow|status node|sprawd[źz] health)\b", re.I), "lenovo-remote/01-health-probe.uri.flow.yaml"),
    (re.compile(r"\b(linkedin|post|kvm|compose)\b", re.I), "lenovo-remote/08-kvm-linkedin.uri.flow.yaml"),
    (re.compile(r"\b(playwright|browser test)\b", re.I), "lenovo-remote/07-playwright-linkedin.uri.flow.yaml"),
    (re.compile(r"\b(install pack|packi|hot.?load|voice pack|głos)\b", re.I), "lenovo-remote/02b-install-voice-packs.uri.flow.yaml"),
    (re.compile(r"\b(introspect|screen|discover)\b", re.I), "lenovo-remote/03-system-introspect.uri.flow.yaml"),
]

_CATALOG_CACHE: list[dict[str, Any]] | None = None


def voice_planner_mode() -> str:
    """auto | regex | catalog | llm — IFURI_VOICE_PLANNER env."""
    mode = os.environ.get("IFURI_VOICE_PLANNER", "auto").strip().lower()
    return mode if mode in {"auto", "regex", "catalog", "llm"} else "auto"


def load_flow_catalog(*, refresh: bool = False) -> list[dict[str, Any]]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None and not refresh:
        return _CATALOG_CACHE

    root = examples_root()
    flows: list[dict[str, Any]] = []
    if not root.is_dir():
        _CATALOG_CACHE = flows
        return flows

    try:
        import yaml
    except ImportError:
        _CATALOG_CACHE = flows
        return flows

    for path in sorted(root.rglob("*.uri.flow.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        meta = data.get("flow") if isinstance(data.get("flow"), dict) else {}
        try:
            rel = path.relative_to(root)
            ref = str(rel).replace("\\", "/")
        except ValueError:
            ref = str(path.name)
        flows.append(
            {
                "ref": ref,
                "id": str(meta.get("id") or path.stem),
                "description": str(meta.get("description") or "").strip(),
                "target": str(meta.get("target") or ""),
            }
        )
    _CATALOG_CACHE = flows
    return flows


def node_has_llm(client: UrisysNodeClient) -> bool:
    health = client.health()
    if not health.get("ok"):
        return False
    packs = {str(p).lower() for p in (health.get("packs_loaded") or [])}
    return bool(packs & LLM_PACK_NAMES)


def _flow_plan(flow_ref: str, text: str, *, planner: str, message: str, confidence: float | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": True,
        "transcript": text,
        "plan": "flow",
        "flow_ref": flow_ref,
        "planner": planner,
        "message": message,
    }
    if confidence is not None:
        out["confidence"] = confidence
    return out


def plan_with_regex(text: str) -> dict[str, Any] | None:
    for pattern, flow_ref in VOICE_FLOW_TRIGGERS:
        if pattern.search(text):
            return _flow_plan(flow_ref, text, planner="regex", message=f"Regex → {flow_ref}")
    return None


def _catalog_tokens(item: dict[str, Any]) -> set[str]:
    blob = " ".join(
        str(part)
        for part in (
            item.get("id") or "",
            item.get("ref") or "",
            item.get("description") or "",
            item.get("target") or "",
        )
    )
    blob = blob.replace("/", " ").replace("-", " ").replace("_", " ").lower()
    return {w for w in blob.split() if len(w) > 2}


def plan_with_catalog(text: str, catalog: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """Score flows by keyword + fuzzy overlap (works offline)."""
    catalog = catalog or load_flow_catalog()
    if not catalog:
        return None

    text_l = text.lower()
    words = {w for w in re.split(r"\W+", text_l) if len(w) > 2}
    best: dict[str, Any] | None = None
    best_score = 0.0

    for item in catalog:
        tokens = _catalog_tokens(item)
        overlap = len(words & tokens)
        ratio = SequenceMatcher(None, text_l, (item.get("description") or item.get("id") or "").lower()).ratio()
        score = overlap * 2.0 + ratio
        if score > best_score:
            best_score = score
            best = item

    if best is None or best_score < 2.5:
        return None
    return _flow_plan(
        str(best["ref"]),
        text,
        planner="catalog",
        message=f"Catalog match → {best['ref']}",
        confidence=round(min(best_score / 10.0, 1.0), 2),
    )


def _parse_llm_plan_json(raw: Any, text: str) -> dict[str, Any] | None:
    if isinstance(raw, dict):
        data = raw
    elif isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
    else:
        return None

    if data.get("plan") == "flow" and data.get("flow_ref"):
        return _flow_plan(str(data["flow_ref"]), text, planner="llm", message=str(data.get("reason") or "LLM flow plan"))
    if data.get("plan") == "uri" and data.get("uri"):
        return {
            "ok": True,
            "transcript": text,
            "plan": "uri",
            "uri": str(data["uri"]),
            "payload": data.get("payload") if isinstance(data.get("payload"), dict) else {"text": text},
            "planner": "llm",
            "message": str(data.get("reason") or "LLM URI plan"),
        }
    return None


def _unwrap_llm_result(resp: dict[str, Any]) -> Any:
    for layer in (resp, resp.get("result") if isinstance(resp.get("result"), dict) else {}):
        for key in ("content", "text", "message"):
            if key in layer and layer[key] is not None:
                return layer[key]
        inner = layer.get("result")
        if isinstance(inner, dict):
            for key in ("content", "text"):
                if key in inner:
                    return inner[key]
    return None


def plan_with_llm(text: str, client: UrisysNodeClient, catalog: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """Plan via urisys-node llm:// pack when loaded."""
    if not node_has_llm(client):
        return None

    catalog = catalog or load_flow_catalog()
    flow_lines = "\n".join(
        f"- {item['ref']}: {item.get('description') or item.get('id')}" for item in catalog[:25]
    )
    system = (
        "You are ifURI voice planner. Pick the best automation flow or URI for the user transcript. "
        "Reply with JSON only: "
        '{"plan":"flow","flow_ref":"<path>","reason":"..."} OR '
        '{"plan":"uri","uri":"<scheme://...>","payload":{},"reason":"..."}'
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Available flows:\n{flow_lines or '(none)'}\n\nTranscript: {text}"},
    ]

    # Prefer text/query/plan (urillm) when available.
    plan_resp = client.call_uri(
        "llm://local/text/query/plan",
        {"transcript": text, "text": text, "allowed_schemes": ["flow", "voice", "node", "screen", "browser", "him", "kvm"]},
        dry_run=False,
    )
    if plan_resp.get("ok") and plan_resp.get("uri"):
        uri = str(plan_resp["uri"])
        if uri.endswith(".uri.flow.yaml") or "lenovo-remote/" in uri:
            ref = uri.split("flows/", 1)[-1] if "flows/" in uri else uri
            return _flow_plan(ref, text, planner="llm", message="llm://text/query/plan")
        return {
            "ok": True,
            "transcript": text,
            "plan": "uri",
            "uri": uri,
            "payload": plan_resp.get("payload") if isinstance(plan_resp.get("payload"), dict) else {"text": text},
            "planner": "llm",
            "message": "llm://text/query/plan",
        }

    chat_resp = client.call_uri(
        "llm://local/chat/query/completion",
        {"messages": messages, "format": "json"},
        dry_run=False,
    )
    if not chat_resp.get("ok"):
        return None
    parsed = _parse_llm_plan_json(_unwrap_llm_result(chat_resp), text)
    if parsed:
        return parsed
    return None


def plan_voice_command(
    text: str,
    *,
    client: UrisysNodeClient | None = None,
    planner: str | None = None,
) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty transcript"}

    mode = (planner or voice_planner_mode()).lower()
    catalog = load_flow_catalog()
    steps: list[str] = []

    if mode in {"auto", "regex"}:
        hit = plan_with_regex(text)
        if hit:
            hit["catalog_size"] = len(catalog)
            return hit
        steps.append("regex")

    if mode in {"auto", "catalog"}:
        hit = plan_with_catalog(text, catalog)
        if hit:
            hit["catalog_size"] = len(catalog)
            return hit
        steps.append("catalog")

    if mode in {"auto", "llm"} and client is not None:
        hit = plan_with_llm(text, client, catalog)
        if hit:
            hit["catalog_size"] = len(catalog)
            return hit
        steps.append("llm")

    return {
        "ok": True,
        "transcript": text,
        "plan": "uri",
        "uri": "voice://command/from-text",
        "payload": {"text": text},
        "planner": "fallback",
        "message": "No flow match — delegate to voice:// on urisys-node",
        "tried": steps,
        "catalog_size": len(catalog),
    }
