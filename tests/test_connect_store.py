# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Unit tests for ifuri_app.connect_store — hub catalog, install plan, payload forms."""

from __future__ import annotations

import json
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ifuri_app import connect_store as cs  # noqa: E402

SAMPLE = {
    "ok": True,
    "packages": [
        {
            "name": "browser-control",
            "version": "0.3.1",
            "scheme": "browser",
            "summary": "Drive Chromium via browser:// URIs",
            "install": {"kind": "pip", "spec": "git+https://github.com/if-uri/urirun-connector-browser-control.git"},
            "routes": [{"uri": "browser://{node}/page/command/open", "params": [{"name": "url", "required": True}]}],
        },
        {
            "name": "time-tools",
            "version": "0.1.0",
            "scheme": "time",
            "install": {"kind": "manual", "spec": ""},
            "routes": ["time://local/now"],
        },
    ],
}


def test_catalog_url_env_override(monkeypatch):
    monkeypatch.delenv("IFURI_CONNECT_CATALOG", raising=False)
    assert cs.catalog_url() == cs.DEFAULT_CATALOG_URL
    monkeypatch.setenv("IFURI_CONNECT_CATALOG", "http://localhost:9999/c")
    assert cs.catalog_url() == "http://localhost:9999/c"


# Real connect.ifuri.com hub shape: connectors[] with id / uriSchemes / install.pipSpec.
HUB_SAMPLE = {
    "version": "ifuri.connectors.v1",
    "connectors": [
        {
            "id": "planfile",
            "name": "Planfile Tasks",
            "status": "available",
            "category": "Planning",
            "summary": "Plan tasks via task:// URIs.",
            "uriSchemes": ["task", "planfile"],
            "routes": ["task://host/tickets/query/list", "planfile://host/dsl/command/run"],
            "install": {"mode": "urirun-extra",
                        "pipSpec": "urirun-connector-planfile @ git+https://github.com/if-uri/urirun-connector-planfile.git@v0.1.1"},
        }
    ],
}


def test_normalize_packages_shapes():
    pkgs = cs.normalize_packages(SAMPLE)
    assert [p["name"] for p in pkgs] == ["browser-control", "time-tools"]  # sorted
    bc = pkgs[0]
    assert bc["install"]["kind"] == "pip"
    assert bc["install"]["spec"] == "git+https://github.com/if-uri/urirun-connector-browser-control.git"
    assert bc["routes"][0]["params"] == [{"name": "url", "required": True}]
    # string route normalised to dict with empty params
    assert pkgs[1]["routes"][0] == {"uri": "time://local/now", "params": []}


def test_normalize_real_hub_shape():
    pkgs = cs.normalize_packages(HUB_SAMPLE)
    assert len(pkgs) == 1
    p = pkgs[0]
    assert p["id"] == "planfile" and p["name"] == "Planfile Tasks"
    assert p["schemes"] == ["task", "planfile"] and p["scheme"] == "task"
    assert p["category"] == "Planning" and p["status"] == "available"
    assert p["version"] == "v0.1.1"  # parsed from the pipSpec @v0.1.1
    assert p["install"]["spec"].startswith("urirun-connector-planfile @ git+")
    assert cs.install_command(p) == [
        "python", "-m", "pip", "install",
        "urirun-connector-planfile @ git+https://github.com/if-uri/urirun-connector-planfile.git@v0.1.1",
    ]
    assert [r["uri"] for r in p["routes"]] == ["task://host/tickets/query/list", "planfile://host/dsl/command/run"]


def test_normalize_skips_invalid_and_accepts_bare_list():
    pkgs = cs.normalize_packages([{"no_name": 1}, {"name": "x"}, "junk"])
    assert [p["name"] for p in pkgs] == ["x"]


def test_install_command_pip_and_unknown():
    pkgs = cs.normalize_packages(SAMPLE)
    assert cs.install_command(pkgs[0]) == [
        "python", "-m", "pip", "install",
        "git+https://github.com/if-uri/urirun-connector-browser-control.git",
    ]
    assert cs.install_command(pkgs[1]) is None  # manual kind → no auto install


def test_payload_form_fields_from_params_and_placeholders():
    route = {"uri": "browser://{node}/page/command/open", "params": [{"name": "url", "required": True}]}
    fields = cs.payload_form_fields(route)
    names = [f["name"] for f in fields]
    assert names == ["url", "node"]  # params first, then placeholders
    assert fields[0]["required"] is True
    assert fields[1]["required"] is True  # placeholders are required


def test_payload_form_fields_dedup():
    route = {"uri": "x://{node}/{node}", "params": [{"name": "node"}]}
    assert [f["name"] for f in cs.payload_form_fields(route)] == ["node"]


class _CatalogHandler(BaseHTTPRequestHandler):
    def log_message(self, *_a):
        pass

    def do_GET(self):  # noqa: N802
        body = json.dumps(SAMPLE).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def test_fetch_catalog_live_mock():
    httpd = HTTPServer(("127.0.0.1", 0), _CatalogHandler)
    host, port = httpd.server_address
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://{host}:{port}/catalog"
    for _ in range(50):
        try:
            urllib.request.urlopen(base, timeout=1)
            break
        except Exception:
            time.sleep(0.05)
    try:
        result = cs.fetch_catalog(base, timeout=2.0)
        assert result["ok"] is True
        assert {p["name"] for p in result["packages"]} == {"browser-control", "time-tools"}
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_fetch_catalog_unreachable():
    out = cs.fetch_catalog("http://127.0.0.1:1/catalog", timeout=0.2)
    assert out["ok"] is False and out["packages"] == [] and out["error"]


# Path to the real hub catalog in the sibling connect.ifuri.com repo.
_REAL_CATALOG = Path(__file__).resolve().parents[2] / "connect.ifuri.com" / "data" / "connectors.json"


@pytest.mark.skipif(not _REAL_CATALOG.is_file(), reason="connect.ifuri.com/data/connectors.json not present")
def test_normalize_against_real_catalog_file():
    """Normalise the actual hub catalog — proves the contract matches the live data."""
    payload = json.loads(_REAL_CATALOG.read_text(encoding="utf-8"))
    pkgs = cs.normalize_packages(payload)
    assert len(pkgs) >= 5, "real catalog should list several connectors"
    # every package has the keys the GUI relies on
    for p in pkgs:
        assert p["id"] and p["name"]
        assert isinstance(p["schemes"], list)
        assert set(p["install"]) == {"kind", "spec", "mode"}
    # at least one connector installs via pip and yields a runnable command
    installable = [p for p in pkgs if cs.install_command(p)]
    assert installable, "expected at least one pip-installable connector"
    assert installable[0]["install"]["spec"]
