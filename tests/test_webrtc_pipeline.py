"""Tests for WebRTC pack install and capabilities."""

from __future__ import annotations

from ifuri_app.urisys_client import node_voice_capabilities
from ifuri_app.webrtc_pipeline import install_webrtc_pack, webrtc_capabilities, webrtc_pack_install_hint


class FakeClient:
    endpoint = "http://127.0.0.1:8790"

    def health(self):
        return {"ok": True, "packs_loaded": ["node", "webrtc"], "routes_count": 72}


class MissingWebRtcClient:
    endpoint = "http://127.0.0.1:8790"

    def health(self):
        return {"ok": True, "packs_loaded": ["node", "stt"], "routes_count": 70}


def test_node_voice_capabilities_includes_webrtc():
    caps = node_voice_capabilities(FakeClient())
    assert caps["webrtc"] is True


def test_webrtc_capabilities_when_loaded():
    out = webrtc_capabilities(FakeClient())
    assert out["ok"] is True
    assert out["webrtc"] is True
    assert out["webrtc_pack_hint"]["needed"] is False


def test_webrtc_pack_hint_when_missing():
    hint = webrtc_pack_install_hint(MissingWebRtcClient())
    assert hint["needed"] is True
    assert "02c-install-webrtc-pack" in hint["flow_ref"]
    assert "webrtc-install-pack" in hint["cli"]


def test_install_skips_when_webrtc_present():
    out = install_webrtc_pack(client=FakeClient(), dry_run=True)
    assert out.get("skipped") is True
