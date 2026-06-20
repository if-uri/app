# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Build and parse shareable ifURI /voice query strings."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

VOICE_PARAMS = (
    "lang",
    "theme",
    "view",
    "channel",
    "prompt",
    "action",
    "dry_run",
    "screen_auto",
)


def voice_query(**params: str | None) -> str:
    clean = {k: str(v) for k, v in params.items() if v not in (None, "")}
    return urlencode(clean)


def voice_url(base: str, **params: str | None) -> str:
    root = base.rstrip("/")
    q = voice_query(**params)
    return f"{root}/voice?{q}" if q else f"{root}/voice"


def merge_voice_url(url: str, **params: str | None) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    merged = {k: (v[0] if v else "") for k, v in qs.items()}
    for key, value in params.items():
        if value in (None, ""):
            merged.pop(key, None)
        else:
            merged[key] = str(value)
    q = urlencode(merged)
    return urlunparse(parsed._replace(path="/voice", query=q))
