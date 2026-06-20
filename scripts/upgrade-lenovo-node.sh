#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

# Upgrade urisys-node on a remote host to get /app/chat/* endpoints (>= 0.1.15).
#
# Usage (on lenovo or via SSH when port 22 is open):
#   URISYS_HOST=192.168.188.201 URISYS_SSH_USER=tom bash scripts/upgrade-lenovo-node.sh
#
# Local dev install from sibling repo:
#   cd ../tellmesh/urisys-node && pip install -e . && urisys-node serve --port 8790
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${URISYS_HOST:-192.168.188.201}"
SSH_USER="${URISYS_SSH_USER:-tom}"
NODE_REPO="${URISYS_NODE_REPO:-$ROOT/../../tellmesh/urisys-node}"
PORT="${URISYS_NODE_PORT:-8790}"

echo "== urisys-node app/chat upgrade =="
echo "host: ${SSH_USER}@${HOST}"
echo "repo: ${NODE_REPO}"

if [[ ! -d "${NODE_REPO}" ]]; then
  echo "missing urisys-node repo at ${NODE_REPO}" >&2
  exit 1
fi

probe() {
  curl -fsS "http://${HOST}:${PORT}/app/chat/messages?channel_id=probe" 2>/dev/null || true
}

if curl -fsS "http://${HOST}:${PORT}/health" | grep -q '"ok": true'; then
  if probe | grep -q '"ok": true'; then
    echo "already has /app/chat — nothing to do"
    exit 0
  fi
  echo "node reachable but /app/chat missing (upgrade required)"
else
  echo "warning: node not reachable at http://${HOST}:${PORT}/health"
fi

if ssh -o ConnectTimeout=5 -o BatchMode=yes "${SSH_USER}@${HOST}" 'echo ok' 2>/dev/null; then
  echo "deploying via SSH…"
  rsync -avz --exclude .venv --exclude .git \
    "${NODE_REPO}/urisysnode/" "${SSH_USER}@${HOST}:~/github/tellmesh/urisys-node/urisysnode/"
  ssh "${SSH_USER}@${HOST}" "cd ~/github/tellmesh/urisys-node && pip install -e . && systemctl --user restart urisys-node.service || true"
else
  echo "SSH unavailable — manual steps:"
  echo "  1. cd ${NODE_REPO} && pip install -e ."
  echo "  2. restart urisys-node on ${HOST}:${PORT}"
  echo "  3. verify: curl http://${HOST}:${PORT}/app/chat/messages?channel_id=test"
  exit 2
fi

sleep 2
probe || true
echo "done"
