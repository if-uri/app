#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

# Headless desktop GUI smoke: Xvfb → ifuri IfuriDesktop → screenshot + API checks.
set -euo pipefail

export DISPLAY="${DISPLAY:-:99}"
URISYS_ENDPOINT="${URISYS_ENDPOINT:-}"
if [ -n "${URISYS_ENDPOINT}" ]; then
  export URISYS_NODE_ENDPOINT="${URISYS_ENDPOINT}"
  export IFURI_URISYS_ENDPOINT="${URISYS_ENDPOINT}"
fi
SMOKE_OUT="${SMOKE_OUT:-/tmp/ifuri-gui-smoke}"

log() { echo "[ifuri-gui-test] $*"; }

start_xvfb() {
  if command -v xdpyinfo >/dev/null 2>&1 && xdpyinfo >/dev/null 2>&1; then
    log "display ${DISPLAY} already up"
    return 0
  fi
  if [ -f /tmp/xvfb.pid ] && kill -0 "$(cat /tmp/xvfb.pid)" 2>/dev/null; then
    sleep 0.5
    return 0
  fi
  log "starting Xvfb on ${DISPLAY}"
  Xvfb "${DISPLAY}" -screen 0 1280x720x24 -ac >/tmp/xvfb.log 2>&1 &
  echo $! >/tmp/xvfb.pid
  for _ in $(seq 1 40); do
    if command -v xdpyinfo >/dev/null 2>&1 && xdpyinfo >/dev/null 2>&1; then
      return 0
    fi
    if scrot -o /tmp/xvfb-probe.png >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  log "Xvfb failed"; tail -20 /tmp/xvfb.log 2>/dev/null || true
  return 1
}

mkdir -p "${SMOKE_OUT}"
start_xvfb

log "python GUI smoke"
python3 /app/scripts/gui_smoke.py \
  --out "${SMOKE_OUT}" \
  ${URISYS_ENDPOINT:+--urisys-endpoint "${URISYS_ENDPOINT}"}

log "ifuri-app CLI smoke"
ifuri-app --help >/dev/null
ifuri-app status 2>/dev/null || true

if [ -f "${SMOKE_OUT}/gui.png" ]; then
  size=$(wc -c < "${SMOKE_OUT}/gui.png")
  log "screenshot ${SMOKE_OUT}/gui.png (${size} bytes)"
  if [ "${size}" -lt 5000 ]; then
    log "screenshot too small — GUI may not have rendered"
    exit 1
  fi
else
  log "missing screenshot ${SMOKE_OUT}/gui.png"
  exit 1
fi

log "PASS $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2- | tr -d '\"' || uname -a)"
