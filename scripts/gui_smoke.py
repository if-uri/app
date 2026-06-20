#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Headless smoke test for ifURI Tkinter desktop GUI (run under Xvfb)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

# Allow running from repo without install
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ifURI desktop GUI smoke test")
    p.add_argument("--out", type=Path, default=Path("/tmp/ifuri-gui-smoke"))
    p.add_argument("--urisys-endpoint", default="", help="optional urisys-node for remote checks")
    p.add_argument("--timeout", type=float, default=25.0)
    return p.parse_args()


def take_screenshot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for cmd in (
        ["scrot", "-o", str(path)],
        ["import", "-window", "root", str(path)],
    ):
        try:
            subprocess.run(cmd, check=True, timeout=10, capture_output=True)
            if path.is_file() and path.stat().st_size > 0:
                return
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    raise RuntimeError("could not capture screenshot (install scrot or imagemagick)")


def run_gui_smoke(out: Path, urisys_endpoint: str, timeout: float) -> dict:
    import tkinter as tk
    from tkinter import ttk

    from ifuri_app.gui import IfuriDesktop
    from ifuri_app.storage import load_workspace, save_workspace

    result: dict = {"ok": False, "checks": {}, "platform": sys.platform}

    if urisys_endpoint:
        ws = load_workspace()
        ws.setdefault("urisys", {})["endpoint"] = urisys_endpoint
        save_workspace(ws)

    app = IfuriDesktop()
    done = threading.Event()
    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(msg)

    def verify_widgets() -> None:
        try:
            tabs = app.notebook.tabs()
            result["checks"]["notebook_tabs"] = len(tabs)
            if len(tabs) < 4:
                fail(f"expected >=4 tabs, got {len(tabs)}")
            titles = [app.notebook.tab(t, "text") for t in tabs]
            result["checks"]["tab_titles"] = titles
            if "Sieć lokalna" not in titles:
                fail("missing Sieć lokalna tab")
            if not isinstance(app.device_tree, ttk.Treeview):
                fail("device_tree missing")
            if not isinstance(app.editor, tk.Text):
                fail("flow editor missing")
            result["checks"]["geometry"] = app.geometry()
        except Exception as exc:
            fail(f"widget verify: {exc}")

    def exercise_network_tab() -> None:
        try:
            app.notebook.select(0)
            app.update_idletasks()
            app.discover_peers()
            app.update_idletasks()
            devices = app.device_tree.get_children()
            result["checks"]["devices_after_scan"] = len(devices)
        except Exception as exc:
            fail(f"network scan: {exc}")

    def exercise_runtime() -> None:
        try:
            from ifuri_app.runtime import find_free_port

            free = find_free_port("127.0.0.1", 18765)
            app.port_var.set(free)
            app.start_runtime()
            app.update_idletasks()
            running = app.runtime is not None
            result["checks"]["runtime_started"] = running
            if not running:
                fail("runtime did not start")
            app.stop_runtime()
        except Exception as exc:
            fail(f"runtime: {exc}")

    def exercise_remote_control() -> None:
        if not urisys_endpoint:
            return
        try:
            from ifuri_app.remote_screen import probe_remote_control
            from ifuri_app.urisys_client import UrisysNodeClient

            probe = probe_remote_control(UrisysNodeClient(urisys_endpoint), node_id="lenovo")
            result["checks"]["remote_control"] = {
                "ok": probe.get("ok"),
                "screen": (probe.get("checks") or {}).get("screen"),
            }
            if not probe.get("ok"):
                fail(f"remote control probe failed: {probe.get('error') or probe.get('checks')}")
        except Exception as exc:
            fail(f"remote control: {exc}")

    def finish() -> None:
        try:
            verify_widgets()
            exercise_network_tab()
            exercise_runtime()
            exercise_remote_control()
            take_screenshot(out / "gui.png")
            result["checks"]["screenshot"] = str(out / "gui.png")
        except Exception as exc:
            fail(str(exc))
        finally:
            done.set()
            app.after(100, app.destroy)

    app.after(800, finish)

    def watchdog() -> None:
        if not done.wait(timeout):
            errors.append(f"timeout after {timeout}s")
            try:
                app.destroy()
            except tk.TclError:
                pass

    threading.Thread(target=watchdog, daemon=True).start()
    app.mainloop()

    result["errors"] = errors
    result["ok"] = not errors
    return result


def main() -> int:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report = run_gui_smoke(args.out, args.urisys_endpoint.strip(), args.timeout)
    report_path = args.out / "report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
