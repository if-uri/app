# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Tests for voice planner (regex, catalog, llm)."""

from __future__ import annotations

from unittest.mock import MagicMock

from ifuri_app.voice_planner import (
    load_flow_catalog,
    plan_voice_command,
    plan_with_catalog,
    plan_with_llm,
    plan_with_regex,
)


def test_regex_health():
    out = plan_with_regex("sprawdź health node")
    assert out and out["plan"] == "flow"
    assert "01-health-probe" in out["flow_ref"]


def test_catalog_loads_examples():
    catalog = load_flow_catalog(refresh=True)
    if not catalog:
        return
    refs = {item["ref"] for item in catalog}
    assert any("01-health-probe" in r for r in refs)


def test_catalog_matches_description_keywords():
    catalog = load_flow_catalog(refresh=True)
    if not catalog:
        return
    out = plan_with_catalog("probe lenovo node reachability health packs", catalog)
    assert out is not None
    assert out["plan"] == "flow"
    assert out["planner"] == "catalog"


def test_auto_planner_fallback():
    out = plan_voice_command("xyz totally unknown phrase qwerty", planner="regex")
    assert out["ok"]
    assert out["plan"] == "uri"
    assert out["planner"] == "fallback"


def test_llm_planner_flow_json():
    class FakeClient:
        endpoint = "http://127.0.0.1:8790"

        def health(self):
            return {"ok": True, "packs_loaded": ["llm"]}

        def call_uri(self, uri, payload, **kwargs):
            if uri.endswith("text/query/plan"):
                return {"ok": False}
            return {
                "ok": True,
                "result": {
                    "content": '{"plan":"flow","flow_ref":"lenovo-remote/01-health-probe.uri.flow.yaml","reason":"health"}'
                },
            }

    out = plan_with_llm("check node health please", FakeClient())
    assert out is not None
    assert out["plan"] == "flow"
    assert out["planner"] == "llm"
