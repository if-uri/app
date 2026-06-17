#!/usr/bin/env bash
# Run ifURI desktop GUI smoke tests in Docker on Debian, Ubuntu, and Fedora.
#
# Optional:
#   URISYS_ENDPOINT=http://192.168.188.201:8790  — remote control probe during smoke
#   IFURI_GUI_DISTROS=debian,ubuntu             — subset of services
#   IFURI_GUI_KEEP=1                            — keep images after run
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="${ROOT}/docker/docker-compose.gui.yml"
DISTROS="${IFURI_GUI_DISTROS:-debian,ubuntu,fedora}"
KEEP="${IFURI_GUI_KEEP:-0}"
FAILED=0
PASSED=0

log() { echo "[ifuri-gui-docker] $*"; }
fail() { log "FAIL: $*"; FAILED=$((FAILED + 1)); }
pass() { log "PASS: $*"; PASSED=$((PASSED + 1)); }

IFS=',' read -ra TARGETS <<< "${DISTROS}"

log "distros: ${TARGETS[*]}"
log "urisys endpoint: ${URISYS_ENDPOINT:-<none>}"

for distro in "${TARGETS[@]}"; do
  svc="ifuri-gui-${distro}"
  log "=== ${svc} ==="
  if ! docker compose -f "${COMPOSE}" build "${svc}"; then
    fail "${svc} build"
    continue
  fi
  if docker compose -f "${COMPOSE}" run --rm --no-deps "${svc}"; then
    pass "${svc}"
  else
    fail "${svc} smoke"
  fi
done

log "summary: ${PASSED} passed, ${FAILED} failed"
if [ "${KEEP}" != "1" ]; then
  log "prune dangling smoke containers (images kept)"
fi

if [ "${FAILED}" -gt 0 ]; then
  exit 1
fi
