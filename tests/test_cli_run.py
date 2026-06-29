# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Branch coverage for `ifuri-app run` (cmd_run): dry-run vs --execute, errors.

Hermetic — the execute branch is exercised via a fake RuntimeState so it needs
neither a running node nor the optional urirun package.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ifuri_app import cli  # noqa: E402


def run_cli(args, capsys):
    """Parse `run ...` argv, invoke cmd_run, return (exit_code, parsed_json|None)."""
    ns = cli.build_parser().parse_args(["run", *args])
    code = ns.func(ns)
    out = capsys.readouterr().out.strip()
    try:
        return code, json.loads(out)
    except json.JSONDecodeError:
        return code, None


def test_run_uri_dry_run_default(capsys):
    code, data = run_cli(["sys://local/echo/hello"], capsys)
    assert code == 0
    assert data is not None  # dry-run produces a JSON plan
    assert data.get("dry_run", True) is not False  # not an execute result


def test_run_flow_file_dry_run(tmp_path, capsys):
    flow = tmp_path / "f.uri.flow.yaml"
    flow.write_text("do:\n  - sys://local/echo/hello\n", encoding="utf-8")
    code, data = run_cli([str(flow), "--dry-run"], capsys)
    assert code == 0
    assert data is not None


def test_resolve_flow_path_finds_filename_in_any_examples_subdir(tmp_path, monkeypatch):
    from ifuri_app import flow_runner

    flow_dir = tmp_path / "office"
    flow_dir.mkdir()
    flow = flow_dir / "health.uri.flow.yaml"
    flow.write_text("do:\n  - sys://local/echo/hello\n", encoding="utf-8")
    monkeypatch.setattr(flow_runner, "examples_root", lambda: tmp_path)

    assert flow_runner.resolve_flow_path("health.uri.flow.yaml") == flow.resolve()


def test_run_invalid_payload_json(capsys):
    code, data = run_cli(["sys://x/y", "--payload", "{not json"], capsys)
    assert code == 2
    assert data["ok"] is False and data["error"]  # surfaces the JSON parse error


def test_run_target_not_file_or_uri(capsys):
    ns = cli.build_parser().parse_args(["run", "definitely-not-a-uri"])
    code = ns.func(ns)
    err = capsys.readouterr().err
    assert code == 2
    assert "not a file or URI" in err


def test_run_uri_execute_uses_runtime_not_dry(monkeypatch, capsys):
    """--execute must call the real runner (dry_run=False, approved=True), not dry-run."""
    calls = {}

    class FakeRuntimeState:
        def call_uri(self, uri, payload, *, dry_run, approved):
            calls["uri"] = (uri, payload, dry_run, approved)
            return {"ok": True, "via": "fake-runtime", "uri": uri}

        def run_flow(self, text, *, dry_run, approved):
            calls["flow"] = (dry_run, approved)
            return {"ok": True, "via": "fake-runtime"}

    monkeypatch.setattr(cli, "RuntimeState", FakeRuntimeState)
    # also ensure dry_run_uri is NOT used on the execute path
    monkeypatch.setattr(cli, "dry_run_uri", lambda *a, **k: pytest.fail("execute must not dry-run"))

    code, data = run_cli(["sys://local/echo/hello", "--execute", "--payload", '{"x": 1}'], capsys)
    assert code == 0
    assert data["via"] == "fake-runtime"
    assert calls["uri"] == ("sys://local/echo/hello", {"x": 1}, False, True)


def test_run_flow_execute_uses_runtime(monkeypatch, tmp_path, capsys):
    calls = {}

    class FakeRuntimeState:
        def run_flow(self, text, *, dry_run, approved):
            calls["flow"] = (dry_run, approved)
            return {"ok": True, "via": "fake-runtime"}

    monkeypatch.setattr(cli, "RuntimeState", FakeRuntimeState)
    monkeypatch.setattr(cli, "dry_run_flow", lambda *a, **k: pytest.fail("execute must not dry-run"))
    flow = tmp_path / "f.uri.flow.yaml"
    flow.write_text("do:\n  - sys://local/echo/hello\n", encoding="utf-8")

    code, data = run_cli([str(flow), "--execute"], capsys)
    assert code == 0
    assert calls["flow"] == (False, True)
