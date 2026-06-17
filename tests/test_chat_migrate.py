"""Tests for chat migration to urisys-node."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ifuri_app.chat_channels import migrate_local_chat_to_urisys, urisys_chat_available


def test_chat_available_false_on_404():
    mock_client = MagicMock()
    mock_client.app_chat_messages.return_value = {"ok": False, "error": "HTTP 404"}
    with patch("ifuri_app.chat_channels.UrisysNodeClient", return_value=mock_client):
        out = urisys_chat_available(router_endpoint="http://127.0.0.1:8790")
    assert out["available"] is False


def test_migrate_skips_when_unavailable():
    with patch("ifuri_app.chat_channels.urisys_chat_available", return_value={"ok": True, "available": False}):
        out = migrate_local_chat_to_urisys(router_endpoint="http://127.0.0.1:8790")
    assert out["ok"] is False


def test_migrate_uploads_local_messages(tmp_path, monkeypatch):
    store_path = tmp_path / "chat.jsonl"
    monkeypatch.setenv("IFURI_CHAT_STORE", str(store_path))
    from ifuri_app.chat_store import LocalChatStore

    store = LocalChatStore(store_path)
    store.append("ch1", "user", "hello")

    mock_client = MagicMock()
    mock_client.app_chat_messages.return_value = {"ok": True, "messages": []}
    mock_client.app_chat_append.return_value = {"ok": True}

    with patch("ifuri_app.chat_channels.urisys_chat_available", return_value={"ok": True, "available": True, "endpoint": "http://n:8790"}):
        with patch("ifuri_app.chat_channels.UrisysNodeClient", return_value=mock_client):
            out = migrate_local_chat_to_urisys(router_endpoint="http://n:8790")
    assert out["ok"] is True
    assert out["messages_uploaded"] == 1
    assert mock_client.app_chat_append.call_count == 1
