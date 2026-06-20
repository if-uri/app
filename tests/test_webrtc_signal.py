# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Tests for WebRTC signaling inbox."""

from __future__ import annotations

from ifuri_app.webrtc_signal import (
    is_webrtc_initiator,
    poll_signals,
    post_signal,
    webrtc_room_id,
)


def test_webrtc_room_id_is_symmetric():
    a = "http://192.168.1.10:8766"
    b = "http://192.168.1.20:8766"
    assert webrtc_room_id(a, b) == webrtc_room_id(b, a)


def test_initiator_is_lexicographically_smaller_url():
    a = "http://192.168.1.10:8766"
    b = "http://192.168.1.20:8766"
    assert is_webrtc_initiator(a, b) is True
    assert is_webrtc_initiator(b, a) is False


def test_signal_post_and_poll():
    room = "webrtc-peer:test"
    posted = post_signal(room, from_peer="http://a", signal_type="offer", data={"type": "offer", "sdp": "v=0"})
    assert posted["ok"] is True
    inbox = poll_signals(room, since=0)
    assert inbox["ok"] is True
    assert len(inbox["signals"]) == 1
    assert inbox["signals"][0]["type"] == "offer"
    empty = poll_signals(room, since=inbox["next"])
    assert empty["signals"] == []
