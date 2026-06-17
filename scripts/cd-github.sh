#!/usr/bin/env bash
# Local CD: test → wheel + native app → GitHub Release (tag vVERSION)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="$(tr -d '[:space:]' < VERSION)"
TAG="v${VERSION}"

echo "== ifURI CD ${TAG} =="

python -m pip install --upgrade pip
python -m pip install pytest pyyaml pyinstaller
python -m pip install -e ".[flows]"

python -m pytest tests/ -q
python -m pip wheel -w dist .
python scripts/build-platform.py --skip-install

WHEEL="$(ls -1 dist/ifuri-"${VERSION}"-py3-none-any.whl)"
APP=""
for candidate in dist/ifuri-"${VERSION}"-*.tar.gz dist/ifuri-"${VERSION}"-*.zip; do
  if [[ -f "${candidate}" ]]; then
    APP="${candidate}"
    break
  fi
done
if [[ -z "${APP}" ]]; then
  echo "Native app artifact not found in dist/" >&2
  exit 1
fi

echo "wheel: ${WHEEL}"
echo "app:   ${APP}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found — artifacts in dist/"
  exit 0
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  gh release upload "$TAG" "$WHEEL" "$APP" --clobber
  echo "Uploaded to existing release ${TAG}"
else
  gh release create "$TAG" "$WHEEL" "$APP" \
    --title "ifURI ${VERSION}" \
    --generate-notes
  echo "Created release ${TAG}"
fi

gh release view "$TAG" --web 2>/dev/null || gh release view "$TAG"
