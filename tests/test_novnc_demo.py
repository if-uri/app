# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Unit tests for ifuri_app.novnc_demo launch helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ifuri_app import novnc_demo as nv  # noqa: E402


def test_dashboard_url_defaults():
    url = nv.dashboard_url({})
    assert url.startswith("http://127.0.0.1:8192/?")
    assert "pc1NovncPort=7901" in url
    assert "pc2NovncPort=7902" in url
    assert "pc1ApiPort=9001" in url
    assert "pc2ApiPort=9002" in url
    assert "DASHBOARD_PORT" not in url  # dashboard port goes in host, not query


def test_dashboard_url_honours_overrides():
    ports = {
        "DASHBOARD_PORT": "18192",
        "PC1_NOVNC_PORT": "17901",
        "PC2_NOVNC_PORT": "17902",
        "PC1_API_PORT": "19001",
        "PC2_API_PORT": "19002",
    }
    url = nv.dashboard_url(ports)
    assert url.startswith("http://127.0.0.1:18192/?")
    assert "pc1NovncPort=17901" in url
    assert "pc2ApiPort=19002" in url


def test_dashboard_ports_reads_env(monkeypatch):
    monkeypatch.setenv("DASHBOARD_PORT", "20000")
    monkeypatch.delenv("PC1_NOVNC_PORT", raising=False)
    ports = nv.dashboard_ports()
    assert ports["DASHBOARD_PORT"] == "20000"
    assert ports["PC1_NOVNC_PORT"] == "7901"  # falls back to default


def test_compose_args():
    assert nv.compose_args("up") == ["docker", "compose", "up", "-d", "--build"]
    assert nv.compose_args("down")[:3] == ["docker", "compose", "down"]
    assert nv.compose_args("logs")[-1] == "--tail=200"
    with pytest.raises(ValueError):
        nv.compose_args("bogus")


def test_read_env_file(tmp_path):
    (tmp_path / ".env").write_text(
        "# comment\nDASHBOARD_PORT=18192\nPC1_NOVNC_PORT=17901\n\nQUOTED=\"19001\"\n",
        encoding="utf-8",
    )
    values = nv.read_env_file(tmp_path)
    assert values["DASHBOARD_PORT"] == "18192"
    assert values["PC1_NOVNC_PORT"] == "17901"
    assert values["QUOTED"] == "19001"  # quotes stripped
    assert nv.read_env_file(tmp_path / "missing") == {}
    assert nv.read_env_file(None) == {}


def test_dashboard_ports_reads_dotenv(tmp_path, monkeypatch):
    # .env declares the +10000 port set; no shell overrides present
    (tmp_path / ".env").write_text("DASHBOARD_PORT=18192\nPC1_NOVNC_PORT=17901\n", encoding="utf-8")
    for env, _key, _default in nv._PORT_SPEC:
        monkeypatch.delenv(env, raising=False)
    ports = nv.dashboard_ports(tmp_path)
    assert ports["DASHBOARD_PORT"] == "18192"  # from .env
    assert ports["PC1_NOVNC_PORT"] == "17901"  # from .env
    assert ports["PC2_NOVNC_PORT"] == "7902"   # default (not in .env)
    url = nv.dashboard_url(directory=tmp_path)
    assert url.startswith("http://127.0.0.1:18192/?")
    assert "pc1NovncPort=17901" in url


def test_shell_env_overrides_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("DASHBOARD_PORT=18192\n", encoding="utf-8")
    monkeypatch.setenv("DASHBOARD_PORT", "28192")  # shell wins over .env
    assert nv.dashboard_ports(tmp_path)["DASHBOARD_PORT"] == "28192"


def test_demo_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("IFURI_NOVNC_DEMO_DIR", str(tmp_path))
    assert nv.demo_dir() == tmp_path
    monkeypatch.setenv("IFURI_NOVNC_DEMO_DIR", str(tmp_path / "missing"))
    assert nv.demo_dir() is None


def test_demo_dir_resolves_sibling_examples(monkeypatch):
    # The real repo layout: if-uri/app (this package) + if-uri/examples/11-…
    monkeypatch.delenv("IFURI_NOVNC_DEMO_DIR", raising=False)
    found = nv.demo_dir()
    # may be None in a stripped checkout, but if present it must be the example dir
    if found is not None:
        assert found.name == "11-novnc_lan_flow"
        assert found.is_dir()


def test_launch_info_shape():
    info = nv.launch_info()
    assert set(info) == {"dir", "available", "docker", "dashboard_url"}
    assert info["dashboard_url"].startswith("http://127.0.0.1:")
    assert isinstance(info["docker"], bool)
