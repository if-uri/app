# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""CLI smoke tests for chat commands."""

from __future__ import annotations

from unittest.mock import patch

from ifuri_app.cli import cmd_chat_status


def test_cli_chat_status_calls_urisys_chat_available():
    with patch("ifuri_app.cli.urisys_chat_available", return_value={"ok": True, "available": False}) as mock:
        code = cmd_chat_status(type("Args", (), {"endpoint": "http://127.0.0.1:8790"})())
    assert code == 0
    mock.assert_called_once_with(router_endpoint="http://127.0.0.1:8790")
