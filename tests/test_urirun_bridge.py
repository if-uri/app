# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

from __future__ import annotations

import os

import pytest

from ifuri_app import urirun_bridge


def test_urirun_info_shape():
    info = urirun_bridge.urirun_info()
    assert info["package"] == "urirun"
    assert "available" in info
    assert "install" in info


def test_call_without_installed_urirun(monkeypatch):
    monkeypatch.setattr(urirun_bridge.importlib.util, "find_spec", lambda name: None)
    result = urirun_bridge.call_urirun("tool://local/report/render", {"format": "html"})
    assert result["ok"] is False
    assert result["available"] is False
    assert result["via"] == "urirun"
    assert "pip install" in result["install"]


def test_parse_json_object_rejects_arrays():
    with pytest.raises(ValueError):
        urirun_bridge.parse_json_object("[]", name="payload")


def test_service_map_env_restores_previous(monkeypatch):
    monkeypatch.setenv("URI_SERVICE_MAP", '{"old":"http://old"}')
    with urirun_bridge.service_map_env({"new": "http://new"}):
        assert os.environ["URI_SERVICE_MAP"] == '{"new": "http://new"}'
    assert os.environ["URI_SERVICE_MAP"] == '{"old":"http://old"}'
