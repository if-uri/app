#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

# Install Tkinter + Xvfb deps for Debian/Ubuntu/Fedora/Alpine base images.
set -euo pipefail

if grep -qi ubuntu /etc/os-release 2>/dev/null; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends \
    ca-certificates curl procps \
    python3 python3-pip python3-tk python3-venv \
    xvfb x11-utils scrot \
    fonts-dejavu-core
  rm -rf /var/lib/apt/lists/*
elif [ -f /etc/debian_version ]; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends \
    ca-certificates curl procps \
    python3 python3-pip python3-tk python3-venv \
    xvfb x11-utils scrot \
    fonts-dejavu-core
  rm -rf /var/lib/apt/lists/*
elif [ -f /etc/fedora-release ] || grep -qi fedora /etc/os-release 2>/dev/null; then
  dnf install -y \
    ca-certificates curl procps-ng \
    python3 python3-pip python3-tkinter \
    xorg-x11-server-Xvfb scrot \
    dejavu-sans-fonts
  dnf clean all
elif grep -qi alpine /etc/os-release 2>/dev/null; then
  apk add --no-cache \
    ca-certificates curl procps \
    python3 py3-pip py3-tkinter \
    xvfb x11-utils scrot \
    ttf-dejavu
else
  echo "Unsupported base image for GUI deps" >&2
  exit 1
fi
