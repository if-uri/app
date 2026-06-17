"""Discover and load ifURI URI packs from packages/."""

from .loader import discover_manifests, load_local_registry, packages_root

__all__ = ["discover_manifests", "load_local_registry", "packages_root"]
