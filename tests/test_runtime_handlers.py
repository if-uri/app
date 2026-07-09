# Author: Tom Sapletta · Part of the ifURI solution.

from __future__ import annotations

from ifuri_app.runtime_handlers import make_handler
from ifuri_app.runtime_state import RuntimeState


def test_make_handler_registers_core_routes():
    """Regression (IFURI-239): handler factory exposes expected API routes."""
    state = RuntimeState("127.0.0.1", 8765)
    handler_cls = make_handler(state)
    get_paths = set(handler_cls._GET_ROUTES)
    post_paths = set(handler_cls._POST_ROUTES)
    assert "/api/health" in get_paths
    assert "/api/urirun" in get_paths
    assert "/api/uri/call" in post_paths
    assert "/api/flow/run" in post_paths
    assert len(get_paths) >= 15
    assert len(post_paths) >= 15
