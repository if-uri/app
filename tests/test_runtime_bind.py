# Author: Tom Sapletta · Part of the ifURI solution.

from __future__ import annotations

from ifuri_app.runtime_bind import find_free_port, format_port_in_use_error


def test_find_free_port_returns_available_port():
    port = find_free_port("127.0.0.1", 39000, attempts=20)
    assert 39000 <= port < 39020


def test_format_port_in_use_error_mentions_host_and_port():
    msg = format_port_in_use_error("127.0.0.1", 8765)
    assert "8765" in msg
    assert "127.0.0.1" in msg
