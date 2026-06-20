# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Load YAML URI packs from repo packages/ into uricore CapabilityRegistry."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any


def packages_root() -> Path:
    """Repo-root packages/ (sibling of src/)."""
    from ifuri_app.paths import repo_root

    return repo_root() / "packages"


def discover_manifests(root: Path | None = None) -> list[Path]:
    base = root or packages_root()
    if not base.is_dir():
        return []
    return sorted(base.glob("*/manifest.yaml"))


def _ensure_pack_path(pack_dir: Path) -> None:
    path = str(pack_dir.resolve())
    if path not in sys.path:
        sys.path.insert(0, path)


@lru_cache(maxsize=1)
def load_local_registry(manifest_paths: tuple[str, ...] | None = None):
    """Build uricore registry from packages/*/manifest.yaml."""
    try:
        from uri_control import CapabilityRegistry
    except ImportError as exc:
        raise ImportError(
            "uricore is required for local URI packs — pip install -e '.[packs]'"
        ) from exc

    paths = [Path(p) for p in manifest_paths] if manifest_paths else discover_manifests()
    registry = CapabilityRegistry()
    loaded: list[str] = []

    for manifest_path in paths:
        pack_dir = manifest_path.parent
        _ensure_pack_path(pack_dir)
        manifest = registry.load_manifest_file(manifest_path)
        loaded.append(manifest.id)

    registry._ifuri_loaded_packs = loaded  # type: ignore[attr-defined]
    return registry


def pack_summary(root: Path | None = None) -> list[dict[str, Any]]:
    """List packs without requiring uricore (for health / CLI)."""
    out: list[dict[str, Any]] = []
    for manifest_path in discover_manifests(root):
        kind = "python"
        if (manifest_path.parent / "manifest.js").is_file():
            kind = "python+js"
        out.append(
            {
                "id": manifest_path.parent.name,
                "path": str(manifest_path),
                "kind": kind,
            }
        )
    js_only = sorted((root or packages_root()).glob("*/manifest.js"))
    for js_path in js_only:
        if (js_path.parent / "manifest.yaml").is_file():
            continue
        out.append({"id": js_path.parent.name, "path": str(js_path), "kind": "javascript"})
    return out
