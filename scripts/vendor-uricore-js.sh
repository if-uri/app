#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

# Vendor @uricore/js into ifURI static web/ for browser ES modules.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${URICORE_JS_ROOT:-$ROOT/../../tellmesh/uricore-js}/src"
DEST="$ROOT/src/ifuri_app/web/vendor/uricore"
PAGE_SRC="$ROOT/packages/ifuri-page"
PAGE_DEST="$ROOT/src/ifuri_app/web/page"

if [[ ! -d "$SRC" ]]; then
  echo "uricore-js not found at $SRC — set URICORE_JS_ROOT" >&2
  exit 1
fi

mkdir -p "$DEST" "$PAGE_DEST"
rsync -a --delete "$SRC/" "$DEST/"
cp "$PAGE_SRC/manifest.js" "$PAGE_DEST/manifest.js"
cp "$PAGE_SRC/handlers.js" "$PAGE_DEST/handlers.js"
echo "Vendored uricore-js → $DEST"
echo "Synced ifuri-page → $PAGE_DEST"
