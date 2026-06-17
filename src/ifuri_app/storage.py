from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from .sample_data import default_workspace

_workspace_lock = threading.Lock()


def app_home() -> Path:
    override = os.environ.get("IFURI_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".ifuri"


def workspace_path() -> Path:
    return app_home() / "workspace.json"


def ensure_home() -> Path:
    home = app_home()
    home.mkdir(parents=True, exist_ok=True)
    return home


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_workspace() -> dict[str, Any]:
    ensure_home()
    path = workspace_path()
    if not path.exists():
        data = default_workspace()
        save_workspace(data)
        return data
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError:
        backup = path.with_suffix(f".broken-{int(time.time())}.json")
        path.rename(backup)
        data = default_workspace()
        data.setdefault("events", []).append({"time": now_iso(), "type": "workspace.recovered", "backup": str(backup)})
        save_workspace(data)
    normalize_workspace(data)
    return data


def normalize_workspace(data: dict[str, Any]) -> dict[str, Any]:
    data.setdefault("version", 1)
    data.setdefault("node", {})
    data["node"].setdefault("id", default_workspace()["node"]["id"])
    data["node"].setdefault("name", default_workspace()["node"]["name"])
    data["node"].setdefault("role", "host")
    data["node"].setdefault("port", 8765)
    data.setdefault("urisys", {})
    data["urisys"].setdefault("endpoint", "http://127.0.0.1:8790")
    data["urisys"].setdefault("role", "client")
    data["urisys"].setdefault("examples_root", "")
    data.setdefault("groups", [])
    data.setdefault("services", [])
    data.setdefault("peers", [])
    data.setdefault("events", [])
    return data


def save_workspace(data: dict[str, Any]) -> Path:
    normalize_workspace(data)
    with _workspace_lock:
        ensure_home()
        path = workspace_path()
        tmp = path.with_suffix(f".json.{os.getpid()}.{threading.get_ident()}.tmp")
        try:
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
    return path


def add_event(data: dict[str, Any], event_type: str, **payload: Any) -> None:
    data.setdefault("events", []).append({"time": now_iso(), "type": event_type, **payload})
    data["events"] = data["events"][-250:]
