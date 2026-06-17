"""Tests for local uricore pack runtime."""

from __future__ import annotations

from ifuri_app.packs.runtime import dispatch_local_uri, get_local_uri_runtime, local_runtime_info


def test_local_runtime_info():
    info = local_runtime_info()
    if not info.get("available"):
        return
    assert info.get("routes", 0) >= 3


def test_voice_plan_local_pack():
    runtime = get_local_uri_runtime()
    if runtime is None:
        return
    out = dispatch_local_uri(
        "voice://local/query/plan",
        {"text": "sprawdź health node"},
        context={"approved": True},
    )
    assert out is not None
    assert out.get("ok") is True
    assert out.get("via") == "uricore-local"
    assert out.get("result", {}).get("plan")
