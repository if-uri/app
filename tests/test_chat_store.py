# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Tests for local chat store fallback."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ifuri_app.chat_channels import fetch_chat_history, persist_chat_turn
from ifuri_app.chat_store import LocalChatStore


@pytest.fixture()
def local_store(tmp_path, monkeypatch):
    path = tmp_path / "app-chat.jsonl"
    monkeypatch.setenv("IFURI_CHAT_STORE", str(path))
    return LocalChatStore(path)


def test_local_store_roundtrip(local_store):
    local_store.append("ch1", "user", "hello")
    local_store.append("ch1", "assistant", "world")
    msgs = local_store.list_messages("ch1")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"


def test_fetch_history_falls_back_on_404(local_store):
    mock_client = MagicMock()
    mock_client.app_chat_messages.return_value = {"ok": False, "error": "HTTP 404"}
    mock_client.call_uri.return_value = {"ok": False, "type": "route_not_found"}
    with patch("ifuri_app.chat_channels.UrisysNodeClient", return_value=mock_client):
        local_store.append("node:x", "user", "cached")
        out = fetch_chat_history("node:x", router_endpoint="http://127.0.0.1:8790")
    assert out["ok"] is True
    assert out["via"] == "local"
    assert out["messages"][0]["text"] == "cached"


def test_fetch_history_falls_back_when_router_unreachable(local_store):
    mock_client = MagicMock()
    mock_client.app_chat_messages.return_value = {
        "ok": False,
        "error": "<urlopen error [WinError 10061] connection refused>",
    }
    with patch("ifuri_app.chat_channels.UrisysNodeClient", return_value=mock_client):
        local_store.append("node:x", "user", "cached")
        out = fetch_chat_history("node:x", router_endpoint="http://127.0.0.1:8790")
    assert out["ok"] is True
    assert out["via"] == "local"
    assert out["messages"][0]["text"] == "cached"
    mock_client.call_uri.assert_not_called()


def test_persist_falls_back_on_404(local_store):
    mock_client = MagicMock()
    mock_client.app_chat_append.return_value = {"ok": False, "error": "HTTP 404"}
    with patch("ifuri_app.chat_channels.UrisysNodeClient", return_value=mock_client):
        out = persist_chat_turn("node:x", "hi", "there", router_endpoint="http://127.0.0.1:8790")
    assert out["ok"] is True
    assert out["via"] == "local"
    assert len(local_store.list_messages("node:x")) == 2


def test_persist_falls_back_when_router_unreachable(local_store):
    mock_client = MagicMock()
    mock_client.app_chat_append.return_value = {
        "ok": False,
        "error": "<urlopen error [WinError 10061] connection refused>",
    }
    with patch("ifuri_app.chat_channels.UrisysNodeClient", return_value=mock_client):
        out = persist_chat_turn("node:x", "hi", "there", router_endpoint="http://127.0.0.1:8790")
    assert out["ok"] is True
    assert out["via"] == "local"
    assert len(local_store.list_messages("node:x")) == 2
    mock_client.call_uri.assert_not_called()
