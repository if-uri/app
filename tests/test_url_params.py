"""Tests for voice URL query helpers."""

from __future__ import annotations

from ifuri_app.url_params import merge_voice_url, voice_query, voice_url


def test_voice_url_builds_prompt():
    url = voice_url("http://127.0.0.1:8766", lang="pl", prompt="health", channel="node:x")
    assert "prompt=health" in url
    assert "lang=pl" in url
    assert url.startswith("http://127.0.0.1:8766/voice?")


def test_voice_query_skips_empty():
    assert voice_query(lang="pl", prompt=None) == "lang=pl"


def test_merge_voice_url():
    url = merge_voice_url("http://127.0.0.1:8766/voice?lang=pl", prompt="ping", action="send")
    assert "prompt=ping" in url
    assert "action=send" in url
    assert "lang=pl" in url
