#!/usr/bin/env bash
# Xvfb -> x11vnc -> noVNC -> ifURI Tkinter GUI. Open http://localhost:6080/vnc.html
set -Eeuo pipefail

export DISPLAY="${DISPLAY:-:99}"
GEOMETRY="${IFURI_GUI_GEOMETRY:-1280x800x24}"
NOVNC_PORT="${NOVNC_PORT:-6080}"
VNC_PORT="${VNC_PORT:-5900}"

log() { echo "[ifuri-novnc] $*"; }

log "starting Xvfb on ${DISPLAY} (${GEOMETRY})"
Xvfb "${DISPLAY}" -screen 0 "${GEOMETRY}" -ac >/tmp/xvfb.log 2>&1 &
for _ in $(seq 1 40); do
  xdpyinfo >/dev/null 2>&1 && break
  sleep 0.25
done
xdpyinfo >/dev/null 2>&1 || { log "Xvfb failed"; tail -20 /tmp/xvfb.log; exit 1; }

log "starting x11vnc on :${VNC_PORT##*:}"
x11vnc -display "${DISPLAY}" -forever -shared -nopw -rfbport "${VNC_PORT}" -quiet >/tmp/x11vnc.log 2>&1 &

# noVNC web client (websockify serves the static client and proxies to VNC).
NOVNC_WEB=/usr/share/novnc
[ -f "${NOVNC_WEB}/vnc.html" ] || NOVNC_WEB=/usr/share/novnc/utils
log "starting noVNC on :${NOVNC_PORT} (web=${NOVNC_WEB})"
websockify --web "${NOVNC_WEB}" "${NOVNC_PORT}" "localhost:${VNC_PORT}" >/tmp/novnc.log 2>&1 &

log "ready -> http://localhost:${NOVNC_PORT}/vnc.html  (auto: ?autoconnect=1&resize=remote)"

# Run the GUI; keep the container alive and restart the GUI if it is closed.
while true; do
  log "launching ifuri-app app"
  ifuri-app app || log "GUI exited ($?); relaunching in 2s"
  sleep 2
done
