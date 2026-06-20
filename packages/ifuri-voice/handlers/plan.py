# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Map spoken/text commands to urisys-examples flow references."""

from __future__ import annotations

from typing import Any


def plan(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text") or payload.get("prompt") or payload.get("transcript") or "").strip()
    if not text:
        return {"ok": False, "error": "empty text"}

    try:
        from ifuri_app.voice_planner import plan_voice_command
        from ifuri_app.urisys_client import UrisysNodeClient

        ep = (context or {}).get("endpoint")
        client = UrisysNodeClient(str(ep)) if ep else UrisysNodeClient()
        planner = payload.get("planner") or (context or {}).get("planner")
        result = plan_voice_command(text, client=client, planner=str(planner) if planner else None)
        return {"ok": True, "text": text, "plan": result}
    except Exception as exc:
        return {"ok": False, "text": text, "error": str(exc)}
