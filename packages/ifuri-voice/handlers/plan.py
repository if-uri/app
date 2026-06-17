"""Map spoken/text commands to urisys-examples flow references."""

from __future__ import annotations

from typing import Any


def plan(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text") or payload.get("prompt") or "").strip()
    if not text:
        return {"ok": False, "error": "empty text"}

    try:
        from ifuri_app.voice_pipeline import plan_voice_command

        result = plan_voice_command(text)
        return {"ok": True, "text": text, "plan": result}
    except Exception as exc:
        return {"ok": False, "text": text, "error": str(exc)}
