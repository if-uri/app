# ifURI App — Makefile
#
# Common commands for development, testing, and running the app.
# Run `make help` for a short overview.

PYTHON ?= python
export PYTHONPATH := src
PORT ?= 8766
URISYS ?= http://192.168.188.201:8790
VENV ?= .venv

.PHONY: help install install-dev test test-api test-e2e install-e2e test-gui test-gui-docker \
	run run-gui run-voice run-voice-bg run-tauri-dev stop health api-smoke chat-status chat-migrate \
	voice-capabilities voice-install-packs webrtc-capabilities webrtc-install-pack webrtc-smoke \
	urirun-info vendor-uricore-js wheel build clean

help:
	@echo "ifURI app — make targets"
	@echo ""
	@echo "  install          pip install package (editable)"
	@echo "  install-dev      editable install + flows extra + pytest"
	@echo "  test             run pytest (unit + API)"
	@echo "  test-api         API smoke tests only"
	@echo "  test-e2e         Playwright /voice UI (uv sync --group e2e && make install-e2e)"
	@echo "  test-gui-docker  Docker GUI smoke (debian/ubuntu/fedora)"
	@echo ""
	@echo "  run ARGS='...'   run arbitrary ifuri-app CLI command"
	@echo "  run-gui          Tkinter desktop (flows + czaty + LAN)"
	@echo "  run-voice        HTTP /voice UI (PORT=$(PORT), URISYS=$(URISYS))"
	@echo "  run-voice-bg     voice server in background → /tmp/ifuri-voice.pid"
	@echo "  run-tauri-dev    Tauri native window → /voice (needs Rust)"
	@echo "  stop             stop background voice server"
	@echo "  health           curl /api/health"
	@echo "  api-smoke        quick curl checks for main endpoints"
	@echo "  chat-status      check urisys /app/chat on URISYS"
	@echo "  chat-migrate     upload local chat history to urisys-node"
	@echo "  urirun-info      optional urirun runtime status"
	@echo "  upgrade-node     hint/script for lenovo urisys-node >= 0.1.15"
	@echo "  vendor-uricore-js  copy @uricore/js + ifuri-page into web/"
	@echo ""
	@echo "  wheel            build wheel to dist/"
	@echo "  build            native platform tarball/zip"
	@echo "  clean            remove caches and dist artifacts"

install:
	$(PYTHON) -m pip install -e .

install-dev:
	@if command -v uv >/dev/null 2>&1; then \
		uv sync --group dev --group tellmesh; \
	else \
		$(PYTHON) -m pip install -e ".[flows,dev,packs]"; \
		$(PYTHON) -m pip install -e ../../tellmesh/uri2flow ../../tellmesh/uricore 2>/dev/null || true; \
	fi

vendor-uricore-js:
	bash scripts/vendor-uricore-js.sh

test:
	PYTHONPATH=src $(PYTHON) -m pytest -q --ignore=tests/e2e

test-api:
	PYTHONPATH=src $(PYTHON) -m pytest tests/test_api_runtime.py -q

test-e2e:
	PYTHONPATH=src uv run --group e2e pytest tests/e2e -q

install-e2e:
	uv sync --group e2e
	uv run --group e2e python -m playwright install chromium

test-gui:
	PYTHONPATH=src $(PYTHON) -m pytest tests/test_gui_smoke.py -q

test-gui-docker:
	bash scripts/test-gui-docker.sh

run:
	PYTHONPATH=src $(PYTHON) -m ifuri_app $(ARGS)

run-gui:
	PYTHONPATH=src $(PYTHON) -m ifuri_app app

run-voice:
	PYTHONPATH=src $(PYTHON) -m ifuri_app voice \
		--urisys-endpoint $(URISYS) --port $(PORT) --auto-port

run-voice-bg:
	@! test -f /tmp/ifuri-voice.pid || { echo "already running (pid $$(cat /tmp/ifuri-voice.pid))"; exit 1; }
	PYTHONPATH=src nohup $(PYTHON) -m ifuri_app voice \
		--urisys-endpoint $(URISYS) --port $(PORT) --no-auto-port \
		>/tmp/ifuri-voice.log 2>&1 & echo $$! > /tmp/ifuri-voice.pid
	@sleep 0.8
	@grep -m1 'voice UI:' /tmp/ifuri-voice.log || tail -3 /tmp/ifuri-voice.log

run-tauri-dev:
	PORT=$(PORT) URISYS=$(URISYS) PYTHON=$(PYTHON) bash desktop/dev-server.sh
	cd desktop && cargo tauri dev

stop:
	@if test -f /tmp/ifuri-voice.pid; then \
		kill $$(cat /tmp/ifuri-voice.pid) 2>/dev/null || true; \
		rm -f /tmp/ifuri-voice.pid; \
		echo "stopped"; \
	else \
		echo "no pid file (/tmp/ifuri-voice.pid)"; \
	fi

health:
	@curl -fsS "http://127.0.0.1:$(PORT)/api/health" | $(PYTHON) -m json.tool | head -20

api-smoke: health
	@echo "== /voice =="
	@curl -fsS "http://127.0.0.1:$(PORT)/voice" | head -c 120; echo
	@echo "== /api/packs =="
	@curl -fsS "http://127.0.0.1:$(PORT)/api/packs" | $(PYTHON) -m json.tool | head -12
	@echo "== /api/chat/channels =="
	@curl -fsS "http://127.0.0.1:$(PORT)/api/chat/channels?timeout=0.5" | $(PYTHON) -m json.tool | head -15
	@echo "== /api/chat/history =="
	@curl -fsS "http://127.0.0.1:$(PORT)/api/chat/history?channel_id=smoke" | $(PYTHON) -m json.tool | head -10

chat-status:
	PYTHONPATH=src $(PYTHON) -m ifuri_app chat-status --endpoint $(URISYS)

chat-migrate:
	PYTHONPATH=src $(PYTHON) -m ifuri_app chat-migrate --endpoint $(URISYS)

chat-migrate-dry:
	PYTHONPATH=src $(PYTHON) -m ifuri_app chat-migrate --endpoint $(URISYS) --dry-run

voice-capabilities:
	PYTHONPATH=src $(PYTHON) -m ifuri_app voice-capabilities --endpoint $(URISYS)

voice-install-packs:
	PYTHONPATH=src $(PYTHON) -m ifuri_app voice-install-packs --endpoint $(URISYS)

webrtc-capabilities:
	PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-capabilities --endpoint $(URISYS)

webrtc-install-pack:
	PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-install-pack --endpoint $(URISYS)

webrtc-smoke:
	PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-smoke --endpoint $(URISYS)

urirun-info:
	PYTHONPATH=src $(PYTHON) -m ifuri_app urirun-info

upgrade-node:
	@if ssh -o ConnectTimeout=5 -o BatchMode=yes "$${URISYS_SSH_USER:-tom}@$${URISYS_HOST:-192.168.188.201}" 'echo ok' 2>/dev/null; then \
		bash scripts/upgrade-lenovo-node.sh; \
	else \
		echo "SSH unavailable — upgrading via shell:// URI…"; \
		$(PYTHON) scripts/upgrade-lenovo-remote.py; \
	fi

wheel:
	$(PYTHON) -m pip wheel -w dist .

build:
	$(PYTHON) scripts/build-platform.py

clean:
	rm -rf dist/*.whl dist/*.tar.gz dist/*.zip .pytest_cache **/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
