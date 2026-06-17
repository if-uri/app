"""Tests for uri2flow integration."""

from __future__ import annotations

from ifuri_app.flow_compile import expand_flow_compiled, flow_steps_from_document, uri2flow_available
from ifuri_app.flow_engine import expand_flow


def test_uri2flow_available():
    assert uri2flow_available() is True


def test_expand_flow_uses_uri2flow():
    text = "do:\n  - kv://session/key/x/query/get\n  - screen://local/monitor/1/query/frame"
    out = expand_flow(text)
    assert out.get("compiler") == "uri2flow"
    nodes = out["workflow_graph"]["nodes"]
    uris = [n["uri"] for n in nodes]
    assert any(u.startswith("kv://") for u in uris)
    assert any(u.startswith("screen://") for u in uris)
    assert out.get("validation")


def test_expand_flow_compiled_graph_edges():
    text = "do:\n  - kv://a/x/query/get\n  - kv://b/y/query/get"
    out = expand_flow_compiled(text)
    edges = out["graph"]["edges"]
    assert edges
    assert edges[0]["type"] == "depends_on"


def test_flow_steps_from_kvm_linkedin_flow():
    from ifuri_app.flow_runner import examples_root

    path = examples_root() / "lenovo-remote" / "08-kvm-linkedin.uri.flow.yaml"
    if not path.is_file():
        return
    steps = flow_steps_from_document(path)
    assert len(steps) >= 5
    assert all(s.get("uri") for s in steps)
