"""Playwright E2E tests for /voice UI (optional: uv sync --group e2e && playwright install chromium)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from ifuri_app.runtime import RuntimeServer, find_free_port

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

def launch_chromium(playwright):
    for candidate in (
        os.environ.get("CHROME_BIN"),
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ):
        if candidate and shutil.which(candidate):
            return playwright.chromium.launch(headless=True, executable_path=shutil.which(candidate))
    if Path(playwright.chromium.executable_path).is_file():
        return playwright.chromium.launch(headless=True)
    pytest.skip("Chromium missing; run `make install-e2e` or set CHROME_BIN")


@pytest.fixture(scope="module")
def voice_server(tmp_path_factory):
    home = tmp_path_factory.mktemp("ifuri-e2e")
    os.environ["IFURI_HOME"] = str(home)
    os.environ["IFURI_CHAT_STORE"] = str(home / "app-chat.jsonl")
    port = find_free_port("127.0.0.1", 18780, attempts=30)
    srv = RuntimeServer("127.0.0.1", port).start()
    yield srv
    srv.stop()


def test_voice_page_loads_and_lang_toggle(voice_server):
    base = voice_server.url
    with sync_playwright() as p:
        browser = launch_chromium(p)
        page = browser.new_page()
        page.goto(f"{base}/voice?lang=pl")
        page.wait_for_selector("#chatTitle")
        assert "ifURI" in page.title()
        assert page.locator("#input").get_attribute("placeholder")

        page.select_option("#langSelect", "en")
        page.wait_for_function("() => document.documentElement.lang === 'en'")
        assert page.locator("#btnSend").inner_text().lower() == "send"
        placeholder = page.locator("#input").get_attribute("placeholder") or ""
        assert "endpoint" in placeholder.lower()

        page.goto(f"{base}/voice?lang=en&theme=dark&view=chat&prompt=hello")
        page.wait_for_function("() => new URL(window.location.href).searchParams.get('prompt') === 'hello'")
        assert page.locator("#input").input_value() == "hello"
        browser.close()


def test_voice_static_i18n_bundle(voice_server):
    import urllib.request

    body = urllib.request.urlopen(f"{voice_server.url}/web/i18n.js", timeout=10).read().decode("utf-8")
    assert "IfuriI18n" in body
    assert "scanSummary" in body
