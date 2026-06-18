#!/usr/bin/env bash
# Start ifURI voice HTTP server for Tauri dev (idempotent).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8766}"
URISYS="${URISYS:-http://192.168.188.201:8790}"
PYTHON="${PYTHON:-python3}"

health() {
  curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1
}

if health; then
  echo "ifURI voice already listening on :${PORT}"
  exit 0
fi

cd "$ROOT"
if test -f /tmp/ifuri-voice.pid && kill -0 "$(cat /tmp/ifuri-voice.pid)" 2>/dev/null; then
  echo "pid file present, waiting for health…"
else
  PYTHONPATH=src "$PYTHON" -m ifuri_app voice \
    --urisys-endpoint "$URISYS" --port "$PORT" --no-auto-port \
    >/tmp/ifuri-voice.log 2>&1 &
  echo $! >/tmp/ifuri-voice.pid
fi

for _ in $(seq 1 30); do
  if health; then
    echo "ifURI voice ready: http://127.0.0.1:${PORT}/voice"
    exit 0
  fi
  sleep 0.2
done

echo "voice server failed to start — see /tmp/ifuri-voice.log" >&2
tail -20 /tmp/ifuri-voice.log >&2 || true
exit 1
