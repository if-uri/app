"""Tests for voice pack install hints."""

from __future__ import annotations

from ifuri_app.voice_pipeline import voice_pack_install_hint


def test_voice_pack_hint_when_no_stt():
    class FakeClient:
        endpoint = "http://127.0.0.1:8790"

        def health(self):
            return {"ok": True, "packs_loaded": ["node", "screen"], "routes_count": 23}

    hint = voice_pack_install_hint(FakeClient())
    assert hint["needed"] is True
    assert "02b-install-voice-packs" in hint["flow_ref"]
    assert "voice-install-packs" in hint["cli"]
