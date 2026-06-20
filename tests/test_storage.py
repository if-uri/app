# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Unit tests for ifuri_app.storage — workspace persistence and recovery."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ifuri_app import storage  # noqa: E402


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Isolate IFURI_HOME so tests never touch the real ~/.ifuri."""
    monkeypatch.setenv("IFURI_HOME", str(tmp_path))
    return tmp_path


def test_app_home_honours_env(home):
    assert storage.app_home() == home
    assert storage.workspace_path() == home / "workspace.json"


def test_now_iso_format():
    ts = storage.now_iso()
    assert ts.endswith("Z") and "T" in ts and len(ts) == 20  # YYYY-MM-DDTHH:MM:SSZ


def test_load_creates_default_when_missing(home):
    assert not storage.workspace_path().exists()
    data = storage.load_workspace()
    assert storage.workspace_path().exists()
    # default workspace is normalised
    for key in ("version", "node", "urisys", "groups", "services", "peers", "events"):
        assert key in data


def test_normalize_fills_defaults():
    data = storage.normalize_workspace({})
    assert data["version"] == 1
    assert data["node"]["port"] == 8765
    assert data["urisys"]["endpoint"] == "http://127.0.0.1:8790"
    assert data["groups"] == [] and data["services"] == [] and data["events"] == []


def test_save_load_round_trip(home):
    data = storage.load_workspace()
    data.setdefault("urisys", {})["endpoint"] = "http://192.168.1.50:8790"
    data["services"].append({"name": "fs", "uri": "mcp://fs/list"})
    storage.save_workspace(data)

    reloaded = storage.load_workspace()
    assert reloaded["urisys"]["endpoint"] == "http://192.168.1.50:8790"
    assert reloaded["services"][0]["uri"] == "mcp://fs/list"


def test_save_is_atomic_no_tmp_left(home):
    storage.save_workspace({"services": []})
    leftovers = list(home.glob("*.tmp"))
    assert not leftovers, f"atomic save left temp files: {leftovers}"


def test_load_recovers_from_corrupt_json(home):
    storage.ensure_home()
    storage.workspace_path().write_text("{ this is not json", encoding="utf-8")
    data = storage.load_workspace()
    # corrupt file is backed up and a fresh default returned
    backups = list(home.glob("workspace.broken-*.json"))
    assert backups, "corrupt workspace should be backed up"
    assert any(e.get("type") == "workspace.recovered" for e in data["events"])


def test_add_event_appends_and_caps():
    data = {"events": []}
    for i in range(300):
        storage.add_event(data, "test.event", i=i)
    assert len(data["events"]) == 250  # capped
    assert data["events"][-1]["i"] == 299  # newest kept
    assert data["events"][0]["i"] == 50   # oldest trimmed
    assert "time" in data["events"][0]
