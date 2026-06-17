"""GUI smoke helpers (no display required for import checks)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def test_gui_module_imports():
    import tkinter  # noqa: F401

    from ifuri_app.gui import IfuriDesktop, launch_gui  # noqa: F401

    assert callable(launch_gui)


def test_gui_smoke_script_parse():
    scripts = Path(__file__).resolve().parents[1] / "scripts" / "gui_smoke.py"
    text = scripts.read_text(encoding="utf-8")
    assert "run_gui_smoke" in text
    assert "Sieć lokalna" in text or "notebook_tabs" in text
