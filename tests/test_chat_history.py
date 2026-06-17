"""Tests for chat history via urisys-node."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ifuri_app.chat_channels import fetch_chat_history, persist_chat_turn


def test_fetch_chat_history_from_node():
    mock_client = MagicMock()
    mock_client.app_chat_messages.return_value = {
        "ok": True,
        "messages": [{"role": "user", "text": "hi", "at": "2026-01-01T00:00:00+00:00"}],
    }
    with patch("ifuri_app.chat_channels.UrisysNodeClient", return_value=mock_client):
        data = fetch_chat_history("node:8790", router_endpoint="http://127.0.0.1:8790")
    assert data["ok"] is True
    assert data["messages"][0]["text"] == "hi"


def test_persist_chat_turn():
    mock_client = MagicMock()
    mock_client.app_chat_append.side_effect = [
        {"ok": True, "message": {"role": "user"}},
        {"ok": True, "message": {"role": "assistant"}},
    ]
    with patch("ifuri_app.chat_channels.UrisysNodeClient", return_value=mock_client):
        out = persist_chat_turn(
            "node:8790",
            "hello",
            "world",
            router_endpoint="http://127.0.0.1:8790",
        )
    assert out["ok"] is True
    assert mock_client.app_chat_append.call_count == 2
