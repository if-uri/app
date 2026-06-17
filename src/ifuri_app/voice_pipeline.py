"""Voice command pipeline: speech text → plan → stt/tts/voice URIs → flow."""

from __future__ import annotations

import os
import re
from typing import Any

from .flow_runner import run_flow_file
from .urisys_client import UrisysNodeClient, node_voice_capabilities

# Simple phrase → urisys-examples flow (extend or replace with llm:// / voice:// on node).
VOICE_FLOW_TRIGGERS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(health|zdrow|status node|sprawd[źz] health)\b", re.I), "lenovo-remote/01-health-probe.uri.flow.yaml"),
    (re.compile(r"\b(linkedin|post|kvm|compose)\b", re.I), "lenovo-remote/08-kvm-linkedin.uri.flow.yaml"),
    (re.compile(r"\b(playwright|browser test)\b", re.I), "lenovo-remote/07-playwright-linkedin.uri.flow.yaml"),
    (re.compile(r"\b(install pack|packi|hot.?load|voice pack|głos)\b", re.I), "lenovo-remote/02b-install-voice-packs.uri.flow.yaml"),
    (re.compile(r"\b(introspect|screen|discover)\b", re.I), "lenovo-remote/03-system-introspect.uri.flow.yaml"),
]


def plan_voice_command(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty transcript"}
    for pattern, flow_ref in VOICE_FLOW_TRIGGERS:
        if pattern.search(text):
            return {
                "ok": True,
                "transcript": text,
                "plan": "flow",
                "flow_ref": flow_ref,
                "message": f"Matched flow {flow_ref}",
            }
    return {
        "ok": True,
        "transcript": text,
        "plan": "uri",
        "uri": "voice://command/from-text",
        "payload": {"text": text},
        "message": "No local flow match — delegate to voice:// on urisys-node",
    }


def _extract_stt_text(stt: dict[str, Any]) -> str | None:
    if not isinstance(stt, dict):
        return None
    for layer in (stt, stt.get("result") if isinstance(stt.get("result"), dict) else {}):
        for key in ("text", "transcript"):
            value = layer.get(key)
            if value:
                return str(value)
        inner = layer.get("result")
        if isinstance(inner, dict):
            for key in ("text", "transcript"):
                value = inner.get(key)
                if value:
                    return str(value)
    return None


def run_voice_command(
    text: str,
    *,
    client: UrisysNodeClient | None = None,
    dry_run: bool = False,
    speak: bool = True,
) -> dict[str, Any]:
    node = client or UrisysNodeClient()
    plan = plan_voice_command(text)
    if not plan.get("ok"):
        return plan

    out: dict[str, Any] = {
        "ok": True,
        "plan": plan,
        "endpoint": node.endpoint,
        "stt": None,
        "voice": None,
        "flow": None,
        "tts": None,
    }

    # Optional: normalize via stt:// on node (browser may already provide text).
    stt_uri = os.environ.get("IFURI_STT_URI", "stt://local/session/main/query/transcript")
    voice_caps = node_voice_capabilities(node)
    if stt_uri and not dry_run and voice_caps.get("stt"):
        stt = node.call_uri(stt_uri, {"text": text}, dry_run=False)
        out["stt"] = stt
        normalized = _extract_stt_text(stt)
        if normalized:
            text = normalized
            plan = plan_voice_command(text)
            out["plan"] = plan
    elif stt_uri and not dry_run:
        out["stt"] = {"ok": False, "skipped": True, "reason": "stt pack not loaded on node"}

    if plan.get("plan") == "flow":
        flow_result = run_flow_file(
            plan["flow_ref"],
            client=node,
            dry_run=dry_run,
            approved=True,
            allow_real=not dry_run,
        )
        out["flow"] = flow_result
        out["ok"] = bool(flow_result.get("ok"))
        summary = f"Flow {'completed' if out['ok'] else 'failed'}: {plan['flow_ref']}"
    else:
        voice = node.call_uri(plan["uri"], plan.get("payload") or {}, dry_run=dry_run)
        out["voice"] = voice
        out["ok"] = bool(voice.get("ok", True)) and not voice.get("error")
        inner = voice.get("result") if isinstance(voice.get("result"), dict) else {}
        summary = (inner or {}).get("message") or str(voice)

    if speak and not dry_run and voice_caps.get("tts"):
        tts_uri = os.environ.get("IFURI_TTS_URI", "tts://local/session/main/command/speak")
        tts = node.call_uri(tts_uri, {"text": summary}, dry_run=False)
        out["tts"] = tts
    elif speak and not dry_run:
        out["tts"] = {"ok": False, "skipped": True, "reason": "tts pack not loaded on node"}

    out["summary"] = summary
    if not out["ok"]:
        hint = _connection_hint(out, node.endpoint)
        if hint:
            out["hint"] = hint
    return out


def _connection_hint(result: dict[str, Any], endpoint: str) -> str | None:
    parts = [result.get("stt"), result.get("voice"), result.get("tts")]
    flow = result.get("flow") or {}
    for step in flow.get("steps") or []:
        parts.append(step.get("response"))
    for part in parts:
        if not isinstance(part, dict):
            continue
        err = str(part.get("error") or "")
        if "Connection refused" in err or "111" in err:
            return (
                f"urisys-node unreachable at {endpoint}. "
                "Start local node (urisys node serve) or point to lenovo: "
                f"--endpoint http://192.168.188.201:8790"
            )
    return None
