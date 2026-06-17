"""Voice command pipeline: speech text → plan → stt/tts/voice URIs → flow."""

from __future__ import annotations

import os
from typing import Any

from .flow_runner import run_flow_file
from .urisys_client import UrisysNodeClient, node_voice_capabilities
from .voice_planner import (
    load_flow_catalog,
    plan_voice_command,
    voice_planner_mode,
)

VOICE_PACKS_FLOW = "lenovo-remote/02b-install-voice-packs.uri.flow.yaml"
VOICE_STT_WHEEL = os.environ.get(
    "URISYS_STT_WHEEL",
    f"{os.environ.get('URISYS_WHEEL_HOST', 'http://192.168.188.212:8765')}/urisys_automation_lab-0.1.1-py3-none-any.whl",
)

__all__ = [
    "VOICE_PACKS_FLOW",
    "install_voice_packs",
    "load_flow_catalog",
    "plan_voice_command",
    "run_voice_command",
    "voice_capabilities",
    "voice_pack_install_hint",
    "voice_planner_mode",
]


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
    plan = plan_voice_command(text, client=node)
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

    stt_uri = os.environ.get("IFURI_STT_URI", "stt://local/session/main/query/transcript")
    voice_caps = node_voice_capabilities(node)
    if stt_uri and not dry_run and voice_caps.get("stt"):
        stt = node.call_uri(stt_uri, {"text": text}, dry_run=False)
        out["stt"] = stt
        normalized = _extract_stt_text(stt)
        if normalized:
            text = normalized
            plan = plan_voice_command(text, client=node)
            out["plan"] = plan
    elif stt_uri and not dry_run:
        out["stt"] = {"ok": False, "skipped": True, "reason": "stt pack not loaded on node"}
        out["voice_pack_hint"] = voice_pack_install_hint(node)

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
        out.setdefault("voice_pack_hint", voice_pack_install_hint(node))

    out["summary"] = summary
    if not out["ok"]:
        hint = _connection_hint(out, node.endpoint)
        if hint:
            out["hint"] = hint
    return out


def voice_capabilities(client: UrisysNodeClient | None = None) -> dict[str, Any]:
    node = client or UrisysNodeClient()
    caps = node_voice_capabilities(node)
    hint = voice_pack_install_hint(node)
    return {
        "ok": True,
        "endpoint": node.endpoint,
        "capabilities": caps,
        "planner": voice_planner_mode(),
        "voice_pack_hint": hint,
    }


def install_voice_packs(
    *,
    client: UrisysNodeClient | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    node = client or UrisysNodeClient()
    hint = voice_pack_install_hint(node)
    if not hint.get("needed"):
        return {"ok": True, "skipped": True, "message": "stt/tts already available", "capabilities": node_voice_capabilities(node)}
    result = run_flow_file(VOICE_PACKS_FLOW, client=node, dry_run=dry_run, approved=True, allow_real=not dry_run)
    if not dry_run and not result.get("ok"):
        health = node.health()
        target = str(health.get("node_id") or "local")
        direct = node.call_uri(
            f"node://{target}/command/install-pack",
            {"pack": "stt", "install": True, "force": True, "specs": [VOICE_STT_WHEEL]},
            dry_run=False,
        )
        result = {"ok": bool((direct.get("result") or direct).get("ok", direct.get("ok"))), "fallback": "direct-install-pack", "direct": direct, "flow": result}
    caps = node_voice_capabilities(node)
    return {
        "ok": bool(result.get("ok")) and caps.get("stt") and caps.get("tts"),
        "dry_run": dry_run,
        "flow": VOICE_PACKS_FLOW,
        "endpoint": node.endpoint,
        "result": result,
        "capabilities": caps,
        "voice_pack_hint": voice_pack_install_hint(node),
    }


def voice_pack_install_hint(client: UrisysNodeClient) -> dict[str, Any]:
    """Suggest urisys-examples flow when stt/tts packs missing on node."""
    caps = node_voice_capabilities(client)
    if caps.get("stt") and caps.get("tts"):
        return {"needed": False}
    return {
        "needed": True,
        "endpoint": client.endpoint,
        "flow_ref": VOICE_PACKS_FLOW,
        "cli": f"ifuri-app voice-install-packs --endpoint {client.endpoint}",
        "message": "Install stt/tts packs on urisys-node (flow 02b-install-voice-packs)",
    }


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
