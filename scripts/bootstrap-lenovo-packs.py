#!/usr/bin/env python3
"""Install KVM flow packs on lenovo from dev wheel server (one-shot bootstrap)."""

from __future__ import annotations

import json
import os
import sys
import urllib.request

WHEEL = os.environ.get("URISYS_WHEEL_SERVER", "http://192.168.188.212:8765")
NODE = os.environ.get("URISYS_NODE_ENDPOINT", "http://192.168.188.201:8790").rstrip("/")

PACKS = [
    ("kv", f"{WHEEL}/urikv-0.1.0-py3-none-any.whl"),
    ("browser", f"{WHEEL}/uribrowser-0.1.4-py3-none-any.whl"),
    ("kvm", f"{WHEEL}/urikvm-0.1.1-py3-none-any.whl"),
    ("him", f"{WHEEL}/urihim-0.1.5-py3-none-any.whl"),
    ("img2nl", f"{WHEEL}/uriimg2nl-0.1.2-py3-none-any.whl"),
    ("stt", f"{WHEEL}/urisys_automation_lab-0.1.1-py3-none-any.whl"),
]


def call(uri: str, payload: dict | None = None) -> dict:
    body = json.dumps(
        {"uri": uri, "payload": payload or {}, "context": {"approved": True, "allow_real": True}}
    ).encode()
    req = urllib.request.Request(
        f"{NODE}/uri/call",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read())


def main() -> int:
    ok = True
    for pack, spec in PACKS:
        print(f"install {pack} …", file=sys.stderr)
        resp = call(
            "node://lenovo/command/install-pack",
            {"pack": pack, "install": True, "force": True, "specs": [spec]},
        )
        result = resp.get("result") or {}
        step_ok = bool(result.get("ok"))
        ok = ok and step_ok
        print(json.dumps({"pack": pack, "ok": step_ok, "routes": result.get("new_routes")}, ensure_ascii=False))
    health = urllib.request.urlopen(f"{NODE}/health", timeout=10)
    print(json.dumps({"health": json.loads(health.read())}, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
