"""Tests for voice capabilities and install-packs API."""

from __future__ import annotations

import json
import os
import urllib.request

import pytest

from ifuri_app.runtime import RuntimeServer, find_free_port
from ifuri_app.voice_pipeline import install_voice_packs, voice_capabilities


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    home = tmp_path_factory.mktemp("ifuri-voice-cap")
    os.environ["IFURI_HOME"] = str(home)
    port = find_free_port("127.0.0.1", 18790, attempts=20)
    srv = RuntimeServer("127.0.0.1", port).start()
    yield srv
    srv.stop()


class FakeClient:
    endpoint = "http://127.0.0.1:8790"

    def health(self):
        return {"ok": True, "packs_loaded": ["node", "stt"], "routes_count": 70}


def test_voice_capabilities_structure():
    out = voice_capabilities(FakeClient())
    assert out["ok"] is True
    assert out["capabilities"]["stt"] is True
    assert out["voice_pack_hint"]["needed"] is False


def test_install_skips_when_packs_present():
    out = install_voice_packs(client=FakeClient(), dry_run=True)
    assert out.get("skipped") is True


def test_api_voice_capabilities(server):
    with urllib.request.urlopen(f"{server.url}/api/voice/capabilities?endpoint=http://127.0.0.1:8790", timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    assert data.get("ok") is True
    assert "capabilities" in data
