# ifURI App — Makefile
#
# Common commands for development, testing, and running the app.
# Run `make help` for a short overview.

PYTHON ?= python
export PYTHONPATH := src
PORT ?= 8766
URISYS ?= http://192.168.188.201:8790
VENV ?= .venv

.PHONY: help install install-dev test test-api test-e2e install-e2e test-gui test-gui-docker smoke-novnc \
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
	@echo "  test-e2e         Playwright /voice UI"
	@echo "  test-gui-docker  Docker GUI smoke (debian/ubuntu/fedora)"
	@echo "  smoke-novnc      bring up noVNC demo + drive GUI against a live node"
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
	@echo "  chat-migrate-dry preview chat history upload"
	@echo "  voice-capabilities check node voice pack availability"
	@echo "  voice-install-packs install voice packs on URISYS"
	@echo "  webrtc-capabilities check node WebRTC pack availability"
	@echo "  webrtc-install-pack install WebRTC pack on URISYS"
	@echo "  webrtc-smoke     run WebRTC session/data smoke"
	@echo "  urirun-info      optional urirun runtime status"
	@echo "  upgrade-node     hint/script for lenovo urisys-node >= 0.1.15"
	@echo "  vendor-uricore-js  copy @uricore/js + ifuri-page into web/"
	@echo ""
	@echo "  wheel            build wheel to dist/"
	@echo "  build            native platform tarball/zip"
	@echo "  clean            remove caches and dist artifacts"
	@echo ""
	@echo "Koru + twin-human (kvm/lenovo desktop):"
	@echo "  koru-cycle       uruchom cykl z apply (twin-human dla kvm ticketów + logi URI)"
	@echo "  koru-plan        dry-run plan (pokaże co zrobi)"
	@echo "  koru-execute-twin  bezpośrednie wywołanie twin dla IFURI-226"
	@echo "  koru-logs        tail queue.log (to co widać w panelu Na żywo)"
	@echo "  koru-status      stan koru + otwarte tickety"

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
	PYTHONPATH=src $(PYTHON) -m pytest tests/e2e -q

install-e2e:
	$(PYTHON) -m pip install pytest-playwright playwright
	$(PYTHON) -m playwright install chromium

test-gui:
	PYTHONPATH=src $(PYTHON) -m pytest tests/test_gui_smoke.py -q

test-gui-docker:
	bash scripts/test-gui-docker.sh

# App + noVNC GUI smoke: brings up examples/11-novnc_lan_flow, then drives the GUI
# headless against a live node and checks the route table, logs and workflow graph.
# NODE defaults to the demo's pc1 API; override with NODE=http://host:port.
NODE ?= http://127.0.0.1:9001
smoke-novnc:
	$(MAKE) -C ../examples/11-novnc_lan_flow up
	PYTHONPATH=src xvfb-run -a $(PYTHON) scripts/gui_smoke.py --urisys-endpoint $(NODE) --out dist/gui-smoke --timeout 30

run-gui-novnc:
	docker compose -f docker/docker-compose.novnc.yml up --build
	@echo "open http://localhost:6080/vnc.html?autoconnect=1&resize=remote"

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

# --- Koru autonomy + twin-human for kvm/lenovo tasks (IFURI-226 style) ---
# Po zmianach w loop + executor + twin: dla ticketów z labelami kvm/lenovo
# cykl używa execute-via-twin-human zamiast chat-drive.
# To sprawia, że realne komendy (kvm://laptop/...) trafiają do queue.log
# i są widoczne w panelu "Na żywo — koru (realne komendy URI)".

.PHONY: koru-cycle koru-plan koru-execute-twin koru-logs koru-status

koru-cycle:
	@echo "▶ Koru cycle (apply=true) — użyje execute-via-twin-human dla kvm/lenovo (realne kvm://laptop/... do queue.log + done z actor)"
	$(PYTHON) -m urirun_connector_loop cycle --project . --apply || $(PYTHON) -c '\
import sys; sys.path.insert(0, "urirun-connector-loop"); \
from urirun_connector_loop.core import _execute_via_twin_human; \
print(_execute_via_twin_human(".", "IFURI-226"))'

koru-plan:
	@echo "▶ Dry-run plan (bez apply)"
	$(PYTHON) -m urirun_connector_loop cycle --project .

koru-execute-twin:
	@echo "▶ Bezpośrednie wykonanie przez twin-human (dla testu IFURI-226 lub podobnego)"
	$(PYTHON) -c '\
import sys; sys.path.insert(0, "urirun-connector-loop"); \
from urirun_connector_loop.core import _execute_via_twin_human; \
print(_execute_via_twin_human(".", "IFURI-226"))'

koru-logs:
	@echo "▶ Ostatnie linie queue.log (to co widać w panelu Na żywo)"
	tail -30 ../.planfile/.koru/queue.log 2>/dev/null || tail -30 .planfile/.koru/queue.log 2>/dev/null || echo "brak queue.log"

koru-status:
	@echo "▶ Stan koru + queue"
	$(PYTHON) -c '\
from urirun.host import work_queue; \
print(work_queue.koru_status()); \
print("tickets open:", len([t for t in work_queue.tickets() if t.get("status")=="open"]))'
