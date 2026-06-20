#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Upgrade lenovo urisys-node over URI (no SSH) — enables /app/chat/* for ifURI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TELLMESH = Path(__file__).resolve().parents[2].parent / "tellmesh"
if not TELLMESH.is_dir():
    TELLMESH = Path.home() / "github" / "tellmesh"

sys.path.insert(0, str(TELLMESH / "urisys-node"))

from urisysnode.remote import upgrade_lenovo_node  # noqa: E402


def main() -> int:
    import os

    endpoint = os.environ.get("URISYS", "http://192.168.188.201:8790")
    wheel_host = os.environ.get("URISYS_WHEEL_HOST", "http://192.168.188.212:8765")
    out = upgrade_lenovo_node(
        tellmesh_root=TELLMESH,
        wheel_host=wheel_host,
        endpoint=endpoint,
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
