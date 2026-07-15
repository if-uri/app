# ifURI App

ifURI desktop app — voice UI, urisys-node client, and URI flow runner for urisys-examples.

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `ifuri`
- **version**: `0.2.10`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(2), app.doql.less, goal.yaml, .env.example, docker-compose.gui.yml, project/(3 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: ifuri;
  version: 0.2.10;
}

dependencies {
  flows: pyyaml>=6.0;
  packs: "uricore>=0.1.8, pyyaml>=6.0";
  urirun: "urirun @ git+https://github.com/if-uri/urirun.git@v0.3.14#subdirectory=adapters/python";
  build: "pyinstaller>=6.0, pyyaml>=6.0";
  dev: "pytest>=8.0, pyyaml>=6.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="ifuri-app"] {
  entry: ifuri_app.cli:main;
}
interface[type="cli"] page[name="ifuri"] {
  entry: ifuri_app.cli:main;
}

interface[type="desktop"] {
  type: tauri;
  framework: tauri;
}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pip install -e .;
}

workflow[name="install-dev"] {
  trigger: manual;
  step-1: run cmd=if command -v uv >/dev/null 2>&1; then \;
  step-2: run cmd=uv sync --group dev --group tellmesh; \;
  step-3: run cmd=else \;
  step-4: run cmd=$(PYTHON) -m pip install -e ".[flows,dev,packs]"; \;
  step-5: run cmd=$(PYTHON) -m pip install -e ../../tellmesh/uri2flow ../../tellmesh/uricore 2>/dev/null || true; \;
  step-6: run cmd=fi;
}

workflow[name="vendor-uricore-js"] {
  trigger: manual;
  step-1: run cmd=bash scripts/vendor-uricore-js.sh;
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m pytest -q --ignore=tests/e2e;
}

workflow[name="test-api"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m pytest tests/test_api_runtime.py -q;
}

workflow[name="test-e2e"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m pytest tests/e2e -q;
}

workflow[name="install-e2e"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pip install pytest-playwright playwright;
  step-2: run cmd=$(PYTHON) -m playwright install chromium;
}

workflow[name="test-gui"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m pytest tests/test_gui_smoke.py -q;
}

workflow[name="test-gui-docker"] {
  trigger: manual;
  step-1: run cmd=bash scripts/test-gui-docker.sh;
}

workflow[name="smoke-novnc"] {
  trigger: manual;
  step-1: run cmd=$(MAKE) -C ../examples/11-novnc_lan_flow up;
  step-2: run cmd=PYTHONPATH=src xvfb-run -a $(PYTHON) scripts/gui_smoke.py --urisys-endpoint $(NODE) --out dist/gui-smoke --timeout 30;
}

workflow[name="run-gui-novnc"] {
  trigger: manual;
  step-1: run cmd=docker compose -f docker/docker-compose.novnc.yml up --build;
  step-2: run cmd=echo "open http://localhost:6080/vnc.html?autoconnect=1&resize=remote";
}

workflow[name="run"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app $(ARGS);
}

workflow[name="run-gui"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app app;
}

workflow[name="run-voice"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app voice \;
  step-2: run cmd=--urisys-endpoint $(URISYS) --port $(PORT) --auto-port;
}

workflow[name="run-voice-bg"] {
  trigger: manual;
  step-1: run cmd=! test -f /tmp/ifuri-voice.pid || { echo "already running (pid $$(cat /tmp/ifuri-voice.pid))"; exit 1; };
  step-2: run cmd=PYTHONPATH=src nohup $(PYTHON) -m ifuri_app voice \;
  step-3: run cmd=--urisys-endpoint $(URISYS) --port $(PORT) --no-auto-port \;
  step-4: run cmd=>/tmp/ifuri-voice.log 2>&1 & echo $$! > /tmp/ifuri-voice.pid;
  step-5: run cmd=sleep 0.8;
  step-6: run cmd=grep -m1 'voice UI:' /tmp/ifuri-voice.log || tail -3 /tmp/ifuri-voice.log;
}

workflow[name="run-tauri-dev"] {
  trigger: manual;
  step-1: run cmd=PORT=$(PORT) URISYS=$(URISYS) PYTHON=$(PYTHON) bash desktop/dev-server.sh;
  step-2: run cmd=cd desktop && cargo tauri dev;
}

workflow[name="stop"] {
  trigger: manual;
  step-1: run cmd=if test -f /tmp/ifuri-voice.pid; then \;
  step-2: run cmd=kill $$(cat /tmp/ifuri-voice.pid) 2>/dev/null || true; \;
  step-3: run cmd=rm -f /tmp/ifuri-voice.pid; \;
  step-4: run cmd=echo "stopped"; \;
  step-5: run cmd=else \;
  step-6: run cmd=echo "no pid file (/tmp/ifuri-voice.pid)"; \;
  step-7: run cmd=fi;
}

workflow[name="health"] {
  trigger: manual;
  step-1: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/api/health" | $(PYTHON) -m json.tool | head -20;
}

workflow[name="api-smoke"] {
  trigger: manual;
  step-1: run cmd=echo "== /voice ==";
  step-2: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/voice" | head -c 120; echo;
  step-3: run cmd=echo "== /api/packs ==";
  step-4: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/api/packs" | $(PYTHON) -m json.tool | head -12;
  step-5: run cmd=echo "== /api/chat/channels ==";
  step-6: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/api/chat/channels?timeout=0.5" | $(PYTHON) -m json.tool | head -15;
  step-7: run cmd=echo "== /api/chat/history ==";
  step-8: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/api/chat/history?channel_id=smoke" | $(PYTHON) -m json.tool | head -10;
}

workflow[name="chat-status"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app chat-status --endpoint $(URISYS);
}

workflow[name="chat-migrate"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app chat-migrate --endpoint $(URISYS);
}

workflow[name="chat-migrate-dry"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app chat-migrate --endpoint $(URISYS) --dry-run;
}

workflow[name="voice-capabilities"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app voice-capabilities --endpoint $(URISYS);
}

workflow[name="voice-install-packs"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app voice-install-packs --endpoint $(URISYS);
}

workflow[name="webrtc-capabilities"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-capabilities --endpoint $(URISYS);
}

workflow[name="webrtc-install-pack"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-install-pack --endpoint $(URISYS);
}

workflow[name="webrtc-smoke"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-smoke --endpoint $(URISYS);
}

workflow[name="urirun-info"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app urirun-info;
}

workflow[name="upgrade-node"] {
  trigger: manual;
  step-1: run cmd=if ssh -o ConnectTimeout=5 -o BatchMode=yes "$${URISYS_SSH_USER:-tom}@$${URISYS_HOST:-192.168.188.201}" 'echo ok' 2>/dev/null; then \;
  step-2: run cmd=bash scripts/upgrade-lenovo-node.sh; \;
  step-3: run cmd=else \;
  step-4: run cmd=echo "SSH unavailable — upgrading via shell:// URI…"; \;
  step-5: run cmd=$(PYTHON) scripts/upgrade-lenovo-remote.py; \;
  step-6: run cmd=fi;
}

workflow[name="wheel"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pip wheel -w dist .;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) scripts/build-platform.py;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=rm -rf dist/*.whl dist/*.tar.gz dist/*.zip .pytest_cache **/__pycache__;
  step-2: run cmd=find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true;
}

workflow[name="koru-cycle"] {
  trigger: manual;
  step-1: run cmd=echo "▶ Koru cycle (apply=true) — użyje execute-via-twin-human dla kvm/lenovo (realne kvm://laptop/... do queue.log + done z actor)";
  step-2: run cmd=$(PYTHON) -m urirun_connector_loop cycle --project . --apply || $(PYTHON) -c '\;
}

workflow[name="koru-plan"] {
  trigger: manual;
  step-1: run cmd=echo "▶ Dry-run plan (bez apply)";
  step-2: run cmd=$(PYTHON) -m urirun_connector_loop cycle --project .;
}

workflow[name="koru-execute-twin"] {
  trigger: manual;
  step-1: run cmd=echo "▶ Bezpośrednie wykonanie przez twin-human (dla testu IFURI-226 lub podobnego)";
  step-2: run cmd=$(PYTHON) -c '\;
}

workflow[name="koru-logs"] {
  trigger: manual;
  step-1: run cmd=echo "▶ Ostatnie linie queue.log (to co widać w panelu Na żywo)";
  step-2: run cmd=tail -30 ../.planfile/.koru/queue.log 2>/dev/null || tail -30 .planfile/.koru/queue.log 2>/dev/null || echo "brak queue.log";
}

workflow[name="koru-status"] {
  trigger: manual;
  step-1: run cmd=echo "▶ Stan koru + queue";
  step-2: run cmd=$(PYTHON) -c '\;
}

tests {
  import: testql-scenarios/**/*.testql.toon.yaml;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_MAX_RETRIES, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_CREATE_BACKUPS, URI_SERVICE_MAP, IFURI_URIRUN_REGISTRY, IFURI_CONNECT_CATALOG, URISYS_EXAMPLES_ROOT, IFURI_EXAMPLES_ROOT, IFURI_VOICE_PLANNER, URISYS_WEBRTC_WHEEL, URISYS_WHEEL_HOST, IFURI_NOVNC_DEMO_DIR, URISYS_NODE_ENDPOINT, IFURI_HOME, URISYS_STT_WHEEL, IFURI_STT_URI, IFURI_TTS_URI;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  template_file: .env.example;
  python_version: >=3.10;
  vars: LLM_MODEL, OPENROUTER_API_KEY, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
  runtime_llm: OPENROUTER_API_KEY;
  runtime_pfix: PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
}
```

## Interfaces

### CLI Entry Points

- `ifuri-app`
- `ifuri`

### testql Scenarios

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -m app
  timeout_ms, 10000

# Test 1: CLI help command
SHELL "python -m app --help" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "usage"

# Test 2: CLI version command
SHELL "python -m app --version" 5000
ASSERT_EXIT_CODE 0

# Test 3: CLI main workflow (dry-run)
SHELL "python -m app --help" 10000
ASSERT_EXIT_CODE 0
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, ${api_url:-http://localhost:8101}
  timeout_ms, 10000

# Converted 82 assertions from pytest
ASSERT[82]{field, operator, expected}:
  status, ==, 200
  status, ==, 200
  package, ==, "urirun"
  status, ==, 200
  via, ==, "urirun"
  uri, ==, "tool://local/report/render"
  exc.code, ==, 400
  status, ==, 200
  exc.code, ==, 404
  error, ==, "not_found"
  status, ==, 200
  status, ==, 200
  len(inbox.signals or []), ==, 1
  webrtc_room_id(a, b), ==, webrtc_room_id(b
  len(inbox.signals), ==, 1
  inbox.signals[0].type, ==, "offer"
  empty.signals, ==, []
  out.plan, ==, "flow"
  out.planner, ==, "llm"
  os.environ.URI_SERVICE_MAP, ==, '{"new": "http://new"}'
  os.environ.URI_SERVICE_MAP, ==, '{"old":"http://old"}'
  run.result.stdout.strip(), ==, "served-by-urirun"
  len(t.tools), ==, 2
  card.name, ==, "ifuri-urirun"
  out.messages_uploaded, ==, 1
  mock_client.app_chat_append.call_count, ==, 1
  messages[0].text, ==, "hi"
  mock_client.app_chat_append.call_count, ==, 2
  out.via, ==, "local"
  out.messages[0].text, ==, "cached"
  out.via, ==, "local"
  len(local_store.list_messages("node:x")), ==, 2
  any(c.endpoint, ==, "http://192.0.2.1:8790" for c in channels)
  any(c.type, ==, "webrtc-peer" for c in channels)
  len(result.ifuri_peers), ==, 1
  len(result.urisys_nodes), ==, 1
  result.counts.ifuri_peers, ==, 1
  result.counts.urisys_nodes, ==, 1
  any(s.scheme, ==, "mcp" for s in result["mcp_agent_services"])
  out.png, ==, b"hello"
  code, ==, 0
  status, ==, 200
  status, ==, 200
  package, ==, "urirun"
  status, ==, 200
  via, ==, "urirun"
  uri, ==, "tool://local/report/render"
  exc.code, ==, 400
  status, ==, 200
  exc.code, ==, 404
  error, ==, "not_found"
  status, ==, 200
  status, ==, 200
  len(inbox.signals or []), ==, 1
  webrtc_room_id(a, b), ==, webrtc_room_id(b
  len(inbox.signals), ==, 1
  inbox.signals[0].type, ==, "offer"
  empty.signals, ==, []
  out.plan, ==, "flow"
  out.planner, ==, "llm"
  os.environ.URI_SERVICE_MAP, ==, '{"new": "http://new"}'
  os.environ.URI_SERVICE_MAP, ==, '{"old":"http://old"}'
  run.result.stdout.strip(), ==, "served-by-urirun"
  len(t.tools), ==, 2
  card.name, ==, "ifuri-urirun"
  out.messages_uploaded, ==, 1
  mock_client.app_chat_append.call_count, ==, 1
  messages[0].text, ==, "hi"
  mock_client.app_chat_append.call_count, ==, 2
  out.via, ==, "local"
  out.messages[0].text, ==, "cached"
  out.via, ==, "local"
  len(local_store.list_messages("node:x")), ==, 2
  any(c.endpoint, ==, "http://192.0.2.1:8790" for c in channels)
  any(c.type, ==, "webrtc-peer" for c in channels)
  len(result.ifuri_peers), ==, 1
  len(result.urisys_nodes), ==, 1
  result.counts.ifuri_peers, ==, 1
  result.counts.urisys_nodes, ==, 1
  any(s.scheme, ==, "mcp" for s in result["mcp_agent_services"])
  out.png, ==, b"hello"
  code, ==, 0
```

## Workflows

## Configuration

```yaml
project:
  name: ifuri
  version: 0.2.10
  env: local
```

## Dependencies

### Runtime

*(see pyproject.toml)*

### Development

```text markpact:deps python scope=dev
pytest>=8.0
pyyaml>=6.0
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Deployment

```bash markpact:run
pip install ifuri

# development install
pip install -e .[dev]
```

### Docker Compose (`docker-compose.gui.yml`)

- **ifuri-gui-debian** image=`ifuri-gui-test:debian`
- **ifuri-gui-ubuntu** image=`ifuri-gui-test:ubuntu`
- **ifuri-gui-fedora** image=`ifuri-gui-test:fedora`

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Get your API key from: https://openrouter.ai/keys |
| `LLM_MODEL` | `llm://openrouter/deepseek/deepseek-v4-pro` |  |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`ifuri-app`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `desktop/src-tauri/Cargo.toml:version`, `src/ifuri_app/__init__.py:__version__`

## Makefile Targets

- `help`
- `install`
- `install-dev`
- `vendor-uricore-js`
- `test`
- `test-api`
- `test-e2e`
- `install-e2e`
- `test-gui`
- `test-gui-docker`
- `smoke-novnc`
- `run-gui-novnc`
- `run`
- `run-gui`
- `run-voice`
- `run-voice-bg`
- `run-tauri-dev`
- `stop`
- `health`
- `api-smoke`
- `chat-status`
- `chat-migrate`
- `chat-migrate-dry`
- `voice-capabilities`
- `voice-install-packs`
- `webrtc-capabilities`
- `webrtc-install-pack`
- `webrtc-smoke`
- `urirun-info`
- `upgrade-node`
- `wheel`
- `build`
- `clean`
- `koru-cycle`
- `koru-plan`
- `koru-execute-twin`
- `koru-logs`
- `koru-status`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# app | 99f 12382L | python:73,shell:11,javascript:10,rust:3,less:1,css:1 | 2026-07-14
# stats: 404 func | 17 cls | 99 mod | CC̄=4.5 | critical:31 | cycles:0
# alerts[5]: CC _normalize_package_item=25; CC run_voice_command=23; CC send_chat_message_routed=19; CC cmd_chat_send=19; CC send_chat_message=18
# hotspots[5]: make_handler fan=78; run_gui_smoke fan=49; serve_http fan=27; test_urirun_serve_http fan=22; send_chat_message fan=20
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[99]:
  app.doql.less,276
  desktop/dev-server.sh,42
  desktop/src-tauri/build.rs,7
  desktop/src-tauri/src/lib.rs,20
  desktop/src-tauri/src/main.rs,10
  docker/entrypoint-gui-novnc.sh,40
  docker/entrypoint-gui-test.sh,68
  docker/install-gui-deps.sh,43
  packages/ifuri-bridge/handlers/__init__.py,5
  packages/ifuri-bridge/handlers/urisys_call.py,63
  packages/ifuri-chat/handlers/__init__.py,5
  packages/ifuri-chat/handlers/messages.py,33
  packages/ifuri-page/handlers.js,55
  packages/ifuri-page/manifest.js,39
  packages/ifuri-voice/handlers/__init__.py,5
  packages/ifuri-voice/handlers/plan.py,27
  project.sh,66
  scripts/bootstrap-lenovo-packs.py,61
  scripts/build-platform.py,149
  scripts/cd-github.sh,56
  scripts/gui_smoke.py,223
  scripts/ifuri_app_entry.py,10
  scripts/run-ifuri-app.sh,7
  scripts/test-gui-docker.sh,51
  scripts/upgrade-lenovo-node.sh,59
  scripts/upgrade-lenovo-remote.py,38
  scripts/vendor-uricore-js.sh,24
  src/ifuri_app/__init__.py,10
  src/ifuri_app/__main__.py,8
  src/ifuri_app/chat_channels.py,549
  src/ifuri_app/chat_store.py,91
  src/ifuri_app/cli.py,676
  src/ifuri_app/connect_store.py,217
  src/ifuri_app/connectors.py,122
  src/ifuri_app/discovery.py,127
  src/ifuri_app/flow_compile.py,195
  src/ifuri_app/flow_engine.py,130
  src/ifuri_app/flow_runner.py,96
  src/ifuri_app/gui.py,1006
  src/ifuri_app/gui_chat.py,293
  src/ifuri_app/network_scan.py,229
  src/ifuri_app/novnc_demo.py,122
  src/ifuri_app/packs/__init__.py,17
  src/ifuri_app/packs/loader.py,78
  src/ifuri_app/packs/runtime.py,63
  src/ifuri_app/paths.py,37
  src/ifuri_app/remote_screen.py,146
  src/ifuri_app/runtime.py,45
  src/ifuri_app/runtime_bind.py,79
  src/ifuri_app/runtime_handlers.py,639
  src/ifuri_app/runtime_state.py,172
  src/ifuri_app/sample_data.py,80
  src/ifuri_app/storage.py,98
  src/ifuri_app/urirun_bridge.py,429
  src/ifuri_app/urisys_client.py,159
  src/ifuri_app/url_params.py,44
  src/ifuri_app/voice_pipeline.py,198
  src/ifuri_app/voice_planner.py,290
  src/ifuri_app/web/i18n.js,115
  src/ifuri_app/web/page/handlers.js,55
  src/ifuri_app/web/page/manifest.js,39
  src/ifuri_app/web/page_runtime.js,24
  src/ifuri_app/web/theme.js,43
  src/ifuri_app/web/url_state.js,71
  src/ifuri_app/web/voice.css,364
  src/ifuri_app/web/voice.js,642
  src/ifuri_app/web/webrtc_peer.js,233
  src/ifuri_app/webrtc_pipeline.py,132
  src/ifuri_app/webrtc_signal.py,107
  tests/e2e/test_voice_playwright.py,73
  tests/test_api_runtime.py,249
  tests/test_chat_channels.py,101
  tests/test_chat_history.py,40
  tests/test_chat_migrate.py,45
  tests/test_chat_store.py,80
  tests/test_cli_chat.py,18
  tests/test_cli_run.py,114
  tests/test_connect_store.py,232
  tests/test_connectors.py,84
  tests/test_flow_compile.py,59
  tests/test_gui_smoke.py,239
  tests/test_ifuri_app.py,143
  tests/test_novnc_demo.py,113
  tests/test_packs_loader.py,48
  tests/test_packs_runtime.py,31
  tests/test_paths.py,49
  tests/test_remote_node_e2e.py,199
  tests/test_runtime_bind.py,17
  tests/test_runtime_handlers.py,21
  tests/test_storage.py,87
  tests/test_urirun_bridge.py,39
  tests/test_urirun_integration.py,286
  tests/test_url_params.py,27
  tests/test_voice_capabilities.py,52
  tests/test_voice_pack_hint.py,22
  tests/test_voice_planner.py,70
  tests/test_webrtc_pipeline.py,48
  tests/test_webrtc_signal.py,39
  tree.sh,5
D:
  packages/ifuri-bridge/handlers/__init__.py:
  packages/ifuri-bridge/handlers/urisys_call.py:
    e: _endpoint,urisys_call,node_health
    _endpoint(payload;context)
    urisys_call(payload;context)
    node_health(payload;context)
  packages/ifuri-chat/handlers/__init__.py:
  packages/ifuri-chat/handlers/messages.py:
    e: list_messages,list_channels
    list_messages(payload;context)
    list_channels(payload;context)
  packages/ifuri-voice/handlers/__init__.py:
  packages/ifuri-voice/handlers/plan.py:
    e: plan
    plan(payload;context)
  scripts/bootstrap-lenovo-packs.py:
    e: call,main
    call(uri;payload)
    main()
  scripts/build-platform.py:
    e: read_version,platform_tag,add_data_arg,run_pyinstaller,package_artifact,main
    read_version()
    platform_tag()
    add_data_arg(src;dest)
    run_pyinstaller()
    package_artifact(binary;version;tag)
    main(argv)
  scripts/gui_smoke.py:
    e: parse_args,take_screenshot,run_gui_smoke,main
    parse_args()
    take_screenshot(path)
    run_gui_smoke(out;urisys_endpoint;timeout)
    main()
  scripts/ifuri_app_entry.py:
  scripts/upgrade-lenovo-remote.py:
    e: main
    main()
  src/ifuri_app/__init__.py:
  src/ifuri_app/__main__.py:
  src/ifuri_app/chat_channels.py:
    e: _channel_id,_urisys_node_channels,_ifuri_peer_channels,_service_channels,channels_from_scan,list_chat_channels,resolve_data_endpoint,_urisys_chat_unavailable,_router_unreachable,_local_chat_store,fetch_chat_history,fetch_chat_channel_index,persist_chat_turn,urisys_chat_available,migrate_local_chat_to_urisys,send_chat_message,send_chat_message_routed,_payload_for_scheme,_short_json,_format_json_reply,_format_voice_reply
    _channel_id(kind;key)
    _urisys_node_channels(nodes)
    _ifuri_peer_channels(peers;local_api_url)
    _service_channels(services)
    channels_from_scan(scan)
    list_chat_channels()
    resolve_data_endpoint()
    _urisys_chat_unavailable(data)
    _router_unreachable(data)
    _local_chat_store()
    fetch_chat_history(channel_id)
    fetch_chat_channel_index()
    persist_chat_turn(channel_id;user_text;assistant_text)
    urisys_chat_available()
    migrate_local_chat_to_urisys()
    send_chat_message(channel;text)
    send_chat_message_routed(channel;text)
    _payload_for_scheme(kind;text)
    _short_json(obj;limit)
    _format_json_reply(data)
    _format_voice_reply(result)
  src/ifuri_app/chat_store.py:
    e: chat_store_path,LocalChatStore
    LocalChatStore: __init__(1),append(3),list_messages(1),list_channels(0)
    chat_store_path()
  src/ifuri_app/cli.py:
    e: print_json,cmd_init,cmd_app,cmd_serve,cmd_discover,cmd_voice,cmd_node_health,cmd_node_call,cmd_node_control_test,cmd_node_screen,cmd_flow_run,cmd_voice_plan,cmd_voice_catalog,cmd_voice_capabilities,cmd_voice_install_packs,cmd_webrtc_capabilities,cmd_webrtc_install_pack,cmd_webrtc_smoke,cmd_voice_run,cmd_chat_channels,cmd_chat_send,cmd_chat_migrate,cmd_chat_status,cmd_packs,cmd_urirun_info,cmd_urirun_call,cmd_urirun_scan,cmd_urirun_serve,cmd_urirun_mcp,cmd_flow_validate,cmd_run,cmd_expand,build_parser,main
    print_json(data)
    cmd_init(args)
    cmd_app(_args)
    cmd_serve(args)
    cmd_discover(args)
    cmd_voice(args)
    cmd_node_health(args)
    cmd_node_call(args)
    cmd_node_control_test(args)
    cmd_node_screen(args)
    cmd_flow_run(args)
    cmd_voice_plan(args)
    cmd_voice_catalog(_args)
    cmd_voice_capabilities(args)
    cmd_voice_install_packs(args)
    cmd_webrtc_capabilities(args)
    cmd_webrtc_install_pack(args)
    cmd_webrtc_smoke(args)
    cmd_voice_run(args)
    cmd_chat_channels(args)
    cmd_chat_send(args)
    cmd_chat_migrate(args)
    cmd_chat_status(args)
    cmd_packs(_args)
    cmd_urirun_info(args)
    cmd_urirun_call(args)
    cmd_urirun_scan(args)
    cmd_urirun_serve(args)
    cmd_urirun_mcp(args)
    cmd_flow_validate(args)
    cmd_run(args)
    cmd_expand(args)
    build_parser()
    main(argv)
  src/ifuri_app/connect_store.py:
    e: catalog_url,_normalize_route,_normalize_install,_version_of,_normalize_package_item,normalize_packages,fetch_catalog,install_command,local_registry_status,example_payload_for,payload_form_fields
    catalog_url()
    _normalize_route(route)
    _normalize_install(install)
    _version_of(install;pkg)
    _normalize_package_item(pkg)
    normalize_packages(payload)
    fetch_catalog(url)
    install_command(pkg)
    local_registry_status()
    example_payload_for(uri;examples)
    payload_form_fields(route;examples)
  src/ifuri_app/connectors.py:
    e: route_scheme,_detail,_row,normalize_routes,group_by_scheme,fetch_node_routes
    route_scheme(uri)
    _detail(binding)
    _row(uri;binding)
    normalize_routes(payload)
    group_by_scheme(rows)
    fetch_node_routes(endpoint)
  src/ifuri_app/discovery.py:
    e: local_descriptor,discover,DiscoveryResponder
    DiscoveryResponder: __init__(2),start(0),stop(0),_loop(0)
    local_descriptor(api_port)
    discover(timeout;api_port;discovery_port)
  src/ifuri_app/flow_compile.py:
    e: uri2flow_available,_parse_flow_input,expand_flow_compiled,flow_steps_from_document,validate_flow_compiled,validate_flow,_scheme,FlowCompileError
    FlowCompileError:  # Flow text could not be compiled.
    uri2flow_available()
    _parse_flow_input(flow)
    expand_flow_compiled(flow)
    flow_steps_from_document(flow)
    validate_flow_compiled(flow)
    validate_flow(flow)
    _scheme(uri)
  src/ifuri_app/flow_engine.py:
    e: expand_flow,_legacy_expand_flow,clean_uri,uri_scheme,extract_steps,flow_id_from_text,classify_route,dry_run_uri,dry_run_flow,as_pretty_json
    expand_flow(flow_text;flow_id)
    _legacy_expand_flow(flow_text;flow_id)
    clean_uri(value)
    uri_scheme(uri)
    extract_steps(flow_text)
    flow_id_from_text(flow_text;default)
    classify_route(uri)
    dry_run_uri(uri;payload)
    dry_run_flow(flow_text)
    as_pretty_json(data)
  src/ifuri_app/flow_runner.py:
    e: examples_root,resolve_flow_path,load_flow_steps,run_flow_file
    examples_root()
    resolve_flow_path(ref)
    load_flow_steps(flow_path)
    run_flow_file(flow_ref)
  src/ifuri_app/gui.py:
    e: launch_gui,IfuriDesktop,FirstRunWizard
    IfuriDesktop: __init__(0),_set_app_icon(0),_build_style(0),_build_ui(0),_build_flows_tab(0),_build_services_tab(0),_build_network_tab(0),_build_connectors_tab(0),_connector_endpoints(0),refresh_connectors(0),_connectors_done(1),_toggle_connectors(0),_build_connect_tab(0),refresh_catalog(0),_catalog_done(1),_selected_package(0),_on_package_select(1),_render_payload_form(1),install_selected_connector(0),_install_done(3),refresh_registry_status(0),_connect_log(1),_build_events_tab(0),_groups(0),_flows(0),_load_groups(0),_load_flows(0),_load_current_flow_text(0),_on_group_select(0),_on_flow_select(0),new_group(0),new_flow(0),save_current_flow(0),dry_run_current_flow(0),_refresh_services(0),add_service(0),start_runtime(0),open_voice_ui(0),stop_runtime(0),discover_peers(0),_refresh_network_views(1),_novnc_precheck(0),_run_compose(2),_compose_done(4),start_novnc_demo(0),stop_novnc_demo(0),open_novnc_dashboard(0),_on_device_select(1),_apply_node_endpoint(1),_maybe_first_run(0),_refresh_peers(0),refresh_log(0),append_log(1),save_all(0),_urirun_serve_cmd(1),start_urirun_serve(0),stop_urirun_serve(0),show_urirun_routes(0),_on_close(0)
    FirstRunWizard: __init__(1),_scan(0),_scan_done(2),_on_pick(1),_save(0),_skip(0),_finish(0)  # First-run setup: scan the LAN, pick (or type) a urirun node 
    launch_gui()
  src/ifuri_app/gui_chat.py:
    e: ChatTabMixin
    ChatTabMixin: _build_chat_tab(0),_router_endpoint(0),_runtime_base_url(0),_chat_prompt_text(0),_sync_chat_prompt_url(0),_open_chat_in_browser(0),_refresh_chat_channels(0),_apply_chat_channels(1),_on_chat_channel_select(1),_load_chat_history_from_urisys(1),_apply_chat_history(2),_render_chat_thread(0),_append_chat(2),_send_chat_message(0),_finish_chat_reply(2)  # Mixin for IfuriDesktop — call _build_chat_tab() from _build_
  src/ifuri_app/network_scan.py:
    e: _local_ipv4,_subnet_hosts,probe_urisys_node,probe_ifuri_peer,_collect_local_services,_services_from_peers,scan_urisys_nodes,scan_network,try_mdns_urisys
    _local_ipv4()
    _subnet_hosts(ip)
    probe_urisys_node(host;port)
    probe_ifuri_peer(api_url)
    _collect_local_services()
    _services_from_peers(peers)
    scan_urisys_nodes()
    scan_network()
    try_mdns_urisys(timeout)
  src/ifuri_app/novnc_demo.py:
    e: demo_dir,read_env_file,dashboard_ports,dashboard_url,docker_available,compose_args,launch_info
    demo_dir()
    read_env_file(directory)
    dashboard_ports(directory)
    dashboard_url(ports)
    docker_available()
    compose_args(action)
    launch_info()
  src/ifuri_app/packs/__init__.py:
  src/ifuri_app/packs/loader.py:
    e: packages_root,discover_manifests,_ensure_pack_path,load_local_registry,pack_summary
    packages_root()
    discover_manifests(root)
    _ensure_pack_path(pack_dir)
    load_local_registry(manifest_paths)
    pack_summary(root)
  src/ifuri_app/packs/runtime.py:
    e: get_local_uri_runtime,dispatch_local_uri,local_runtime_info
    get_local_uri_runtime()
    dispatch_local_uri(uri;payload)
    local_runtime_info()
  src/ifuri_app/paths.py:
    e: app_package_dir,web_dir,assets_dir,repo_root,packages_dir
    app_package_dir()
    web_dir()
    assets_dir()
    repo_root()
    packages_dir()
  src/ifuri_app/remote_screen.py:
    e: resolve_node_id,unwrap_result,screen_uri,capture_remote_screen,probe_remote_control
    resolve_node_id(client;node_id)
    unwrap_result(response)
    screen_uri()
    capture_remote_screen(client)
    probe_remote_control(client)
  src/ifuri_app/runtime.py:
    e: RuntimeServer
    RuntimeServer: __init__(2),url(0),start(0),stop(0)
  src/ifuri_app/runtime_bind.py:
    e: _port_listeners,format_port_in_use_error,_port_available,find_free_port,bind_runtime_server,PortInUseError,ThreadingHTTPServer
    PortInUseError:  # HTTP bind failed because the port is already taken.
    ThreadingHTTPServer:
    _port_listeners(port)
    format_port_in_use_error(host;port)
    _port_available(host;port)
    find_free_port(host;start)
    bind_runtime_server(host;port;handler)
  src/ifuri_app/runtime_handlers.py:
    e: json_bytes,make_handler
    json_bytes(data)
    make_handler(state)
  src/ifuri_app/runtime_state.py:
    e: load_urirun_policy,RuntimeState
    RuntimeState: __init__(2),load(0),health(0),call_uri(3),run_flow(2)
    load_urirun_policy(data;approved)
  src/ifuri_app/sample_data.py:
    e: default_workspace
    default_workspace()
  src/ifuri_app/storage.py:
    e: app_home,workspace_path,ensure_home,now_iso,load_workspace,normalize_workspace,save_workspace,add_event
    app_home()
    workspace_path()
    ensure_home()
    now_iso()
    load_workspace()
    normalize_workspace(data)
    save_workspace(data)
    add_event(data;event_type)
  src/ifuri_app/urirun_bridge.py:
    e: urirun_info,load_registry,service_map_env,parse_json_object,call_urirun,registry_summary,default_urirun_registry,_is_route_not_found,dispatch_local,list_routes,serve_http,scan_project,mcp_tools,a2a_card,serve_mcp
    urirun_info()
    load_registry(path)
    service_map_env(service_map)
    parse_json_object(value)
    call_urirun(uri;payload)
    registry_summary(path)
    default_urirun_registry()
    _is_route_not_found(result)
    dispatch_local(uri;payload)
    list_routes(registry_path)
    serve_http()
    scan_project(path)
    mcp_tools(registry_path)
    a2a_card(registry_path)
    serve_mcp()
  src/ifuri_app/urisys_client.py:
    e: default_node_endpoint,node_llm_available,node_webrtc_available,node_voice_capabilities,UrisysNodeClient
    UrisysNodeClient: __init__(1),health(0),call_uri(2),app_chat_messages(1),app_chat_channels(0),app_chat_append(3),_get(1),_post(2)
    default_node_endpoint()
    node_llm_available(client)
    node_webrtc_available(client)
    node_voice_capabilities(client)
  src/ifuri_app/url_params.py:
    e: voice_query,voice_url,merge_voice_url
    voice_query()
    voice_url(base)
    merge_voice_url(url)
  src/ifuri_app/voice_pipeline.py:
    e: _extract_stt_text,run_voice_command,voice_capabilities,install_voice_packs,voice_pack_install_hint,_connection_hint
    _extract_stt_text(stt)
    run_voice_command(text)
    voice_capabilities(client)
    install_voice_packs()
    voice_pack_install_hint(client)
    _connection_hint(result;endpoint)
  src/ifuri_app/voice_planner.py:
    e: voice_planner_mode,load_flow_catalog,node_has_llm,_flow_plan,plan_with_regex,_catalog_tokens,plan_with_catalog,_parse_llm_plan_json,_unwrap_llm_result,plan_with_llm,plan_voice_command
    voice_planner_mode()
    load_flow_catalog()
    node_has_llm(client)
    _flow_plan(flow_ref;text)
    plan_with_regex(text)
    _catalog_tokens(item)
    plan_with_catalog(text;catalog)
    _parse_llm_plan_json(raw;text)
    _unwrap_llm_result(resp)
    plan_with_llm(text;client;catalog)
    plan_voice_command(text)
  src/ifuri_app/webrtc_pipeline.py:
    e: webrtc_capabilities,install_webrtc_pack,webrtc_smoke,webrtc_pack_install_hint
    webrtc_capabilities(client)
    install_webrtc_pack()
    webrtc_smoke()
    webrtc_pack_install_hint(client)
  src/ifuri_app/webrtc_signal.py:
    e: local_peer_url,webrtc_room_id,is_webrtc_initiator,_purge_room,post_signal,poll_signals,room_stats
    local_peer_url()
    webrtc_room_id(local_url;remote_url)
    is_webrtc_initiator(local_url;remote_url)
    _purge_room(room;entry)
    post_signal(room)
    poll_signals(room)
    room_stats()
  tests/e2e/test_voice_playwright.py:
    e: launch_chromium,voice_server,test_voice_page_loads_and_lang_toggle,test_voice_static_i18n_bundle
    launch_chromium(playwright)
    voice_server(tmp_path_factory)
    test_voice_page_loads_and_lang_toggle(voice_server)
    test_voice_static_i18n_bundle(voice_server)
  tests/test_api_runtime.py:
    e: server,_get,_post,test_health,test_voice_page,test_static_assets,test_api_packs,test_api_urirun_status,test_api_urirun_call_contract,test_api_urirun_call_local_registry_execute,test_uri_call_voice_plan,test_flow_validate,test_flow_expand,test_flow_expand_missing_text,test_chat_channels,test_chat_history,test_network_scan,test_voice_plan,test_chat_send_empty,test_concurrent_health,test_not_found,test_webrtc_signal_api
    server(tmp_path_factory)
    _get(url)
    _post(url;payload)
    test_health(server)
    test_voice_page(server)
    test_static_assets(server)
    test_api_packs(server)
    test_api_urirun_status(server)
    test_api_urirun_call_contract(server)
    test_api_urirun_call_local_registry_execute(server;tmp_path)
    test_uri_call_voice_plan(server)
    test_flow_validate(server)
    test_flow_expand(server)
    test_flow_expand_missing_text(server)
    test_chat_channels(server)
    test_chat_history(server)
    test_network_scan(server)
    test_voice_plan(server)
    test_chat_send_empty(server)
    test_concurrent_health(server)
    test_not_found(server)
    test_webrtc_signal_api(server)
  tests/test_chat_channels.py:
    e: test_channels_from_scan_groups_endpoints,test_send_empty_message,test_send_mcp_falls_back_when_router_unreachable,test_send_mcp_routes_through_urisys_when_reachable,test_send_mcp_reports_node_error_without_fallback
    test_channels_from_scan_groups_endpoints()
    test_send_empty_message()
    test_send_mcp_falls_back_when_router_unreachable()
    test_send_mcp_routes_through_urisys_when_reachable()
    test_send_mcp_reports_node_error_without_fallback()
  tests/test_chat_history.py:
    e: test_fetch_chat_history_from_node,test_persist_chat_turn
    test_fetch_chat_history_from_node()
    test_persist_chat_turn()
  tests/test_chat_migrate.py:
    e: test_chat_available_false_on_404,test_migrate_skips_when_unavailable,test_migrate_uploads_local_messages
    test_chat_available_false_on_404()
    test_migrate_skips_when_unavailable()
    test_migrate_uploads_local_messages(tmp_path;monkeypatch)
  tests/test_chat_store.py:
    e: local_store,test_local_store_roundtrip,test_fetch_history_falls_back_on_404,test_fetch_history_falls_back_when_router_unreachable,test_persist_falls_back_on_404,test_persist_falls_back_when_router_unreachable
    local_store(tmp_path;monkeypatch)
    test_local_store_roundtrip(local_store)
    test_fetch_history_falls_back_on_404(local_store)
    test_fetch_history_falls_back_when_router_unreachable(local_store)
    test_persist_falls_back_on_404(local_store)
    test_persist_falls_back_when_router_unreachable(local_store)
  tests/test_cli_chat.py:
    e: test_cli_chat_status_calls_urisys_chat_available
    test_cli_chat_status_calls_urisys_chat_available()
  tests/test_cli_run.py:
    e: run_cli,test_run_uri_dry_run_default,test_run_flow_file_dry_run,test_resolve_flow_path_finds_filename_in_any_examples_subdir,test_run_invalid_payload_json,test_run_target_not_file_or_uri,test_run_uri_execute_uses_runtime_not_dry,test_run_flow_execute_uses_runtime
    run_cli(args;capsys)
    test_run_uri_dry_run_default(capsys)
    test_run_flow_file_dry_run(tmp_path;capsys)
    test_resolve_flow_path_finds_filename_in_any_examples_subdir(tmp_path;monkeypatch)
    test_run_invalid_payload_json(capsys)
    test_run_target_not_file_or_uri(capsys)
    test_run_uri_execute_uses_runtime_not_dry(monkeypatch;capsys)
    test_run_flow_execute_uses_runtime(monkeypatch;tmp_path;capsys)
  tests/test_connect_store.py:
    e: test_catalog_url_env_override,test_normalize_packages_shapes,test_normalize_real_hub_shape,test_normalize_skips_invalid_and_accepts_bare_list,test_install_command_pip_and_unknown,test_payload_form_fields_from_params_and_placeholders,test_payload_form_fields_dedup,test_payload_form_fields_from_example_payload,test_payload_form_no_example_match_falls_back,test_example_payload_for,test_fetch_catalog_live_mock,test_fetch_catalog_unreachable,test_local_registry_status_unconfigured,test_local_registry_status_reads_registry,test_normalize_against_real_catalog_file,_CatalogHandler
    _CatalogHandler: log_message(0),do_GET(0)
    test_catalog_url_env_override(monkeypatch)
    test_normalize_packages_shapes()
    test_normalize_real_hub_shape()
    test_normalize_skips_invalid_and_accepts_bare_list()
    test_install_command_pip_and_unknown()
    test_payload_form_fields_from_params_and_placeholders()
    test_payload_form_fields_dedup()
    test_payload_form_fields_from_example_payload()
    test_payload_form_no_example_match_falls_back()
    test_example_payload_for()
    test_fetch_catalog_live_mock()
    test_fetch_catalog_unreachable()
    test_local_registry_status_unconfigured(monkeypatch;tmp_path)
    test_local_registry_status_reads_registry(monkeypatch;tmp_path)
    test_normalize_against_real_catalog_file()
  tests/test_connectors.py:
    e: test_route_scheme_variants,test_normalize_list_of_dicts,test_normalize_dict_of_bindings,test_normalize_list_of_strings_and_bare_list,test_normalize_alternate_uri_keys_and_dedup,test_normalize_ignores_entries_without_uri,test_group_by_scheme,test_fetch_node_routes_handles_unreachable
    test_route_scheme_variants()
    test_normalize_list_of_dicts()
    test_normalize_dict_of_bindings()
    test_normalize_list_of_strings_and_bare_list()
    test_normalize_alternate_uri_keys_and_dedup()
    test_normalize_ignores_entries_without_uri()
    test_group_by_scheme()
    test_fetch_node_routes_handles_unreachable()
  tests/test_flow_compile.py:
    e: test_uri2flow_available,test_expand_flow_uses_uri2flow,test_expand_flow_compiled_graph_edges,test_validate_flow_uses_legacy_fallback_without_uri2flow,test_flow_steps_from_kvm_linkedin_flow
    test_uri2flow_available()
    test_expand_flow_uses_uri2flow()
    test_expand_flow_compiled_graph_edges()
    test_validate_flow_uses_legacy_fallback_without_uri2flow(monkeypatch)
    test_flow_steps_from_kvm_linkedin_flow()
  tests/test_gui_smoke.py:
    e: app,test_gui_module_imports,test_gui_smoke_script_parse,test_connectors_tab_present,test_connectors_render_groups_by_node_and_scheme,test_connectors_empty_state,test_lan_scan_auto_refreshes_connectors,test_novnc_section_present,test_novnc_open_dashboard,test_novnc_precheck_missing_dir,test_novnc_precheck_missing_docker,test_app_icon_asset_present,test_app_icon_set_on_window,test_connect_tab_present,test_connect_catalog_and_payload_form,test_connect_payload_form_enriched_from_example,test_connect_install_manual_no_subprocess,test_connect_catalog_error,test_connect_registry_status_renders,test_connect_registry_status_no_urirun,test_connect_registry_status_registry_without_urirun
    app()
    test_gui_module_imports()
    test_gui_smoke_script_parse()
    test_connectors_tab_present(app)
    test_connectors_render_groups_by_node_and_scheme(app)
    test_connectors_empty_state(app)
    test_lan_scan_auto_refreshes_connectors(app;monkeypatch)
    test_novnc_section_present(app)
    test_novnc_open_dashboard(app;monkeypatch)
    test_novnc_precheck_missing_dir(app;monkeypatch)
    test_novnc_precheck_missing_docker(app;monkeypatch;tmp_path)
    test_app_icon_asset_present()
    test_app_icon_set_on_window(app)
    test_connect_tab_present(app)
    test_connect_catalog_and_payload_form(app)
    test_connect_payload_form_enriched_from_example(app)
    test_connect_install_manual_no_subprocess(app;monkeypatch)
    test_connect_catalog_error(app)
    test_connect_registry_status_renders(app;monkeypatch)
    test_connect_registry_status_no_urirun(app;monkeypatch)
    test_connect_registry_status_registry_without_urirun(app;monkeypatch)
  tests/test_ifuri_app.py:
    e: test_plan_linkedin_flow,test_plan_health_flow,test_plan_voice_fallback,test_expand_flow_extracts_uris,test_scan_network_structure,test_node_voice_capabilities_without_voice_packs,test_node_voice_capabilities_with_stt_pack,test_screen_uri,test_resolve_node_id_order,test_unwrap_result_nested,test_capture_remote_screen_mock,test_connection_hint_on_refused
    test_plan_linkedin_flow()
    test_plan_health_flow()
    test_plan_voice_fallback()
    test_expand_flow_extracts_uris()
    test_scan_network_structure()
    test_node_voice_capabilities_without_voice_packs()
    test_node_voice_capabilities_with_stt_pack()
    test_screen_uri()
    test_resolve_node_id_order(monkeypatch)
    test_unwrap_result_nested()
    test_capture_remote_screen_mock()
    test_connection_hint_on_refused()
  tests/test_novnc_demo.py:
    e: test_dashboard_url_defaults,test_dashboard_url_honours_overrides,test_dashboard_ports_reads_env,test_compose_args,test_read_env_file,test_dashboard_ports_reads_dotenv,test_shell_env_overrides_dotenv,test_demo_dir_env_override,test_demo_dir_resolves_sibling_examples,test_launch_info_shape
    test_dashboard_url_defaults()
    test_dashboard_url_honours_overrides()
    test_dashboard_ports_reads_env(monkeypatch)
    test_compose_args()
    test_read_env_file(tmp_path)
    test_dashboard_ports_reads_dotenv(tmp_path;monkeypatch)
    test_shell_env_overrides_dotenv(tmp_path;monkeypatch)
    test_demo_dir_env_override(monkeypatch;tmp_path)
    test_demo_dir_resolves_sibling_examples(monkeypatch)
    test_launch_info_shape()
  tests/test_packs_loader.py:
    e: test_packages_root_exists,test_discover_manifests_finds_bridge_voice_chat,test_pack_summary_lists_js_page_pack,test_load_local_registry_when_uricore_available
    test_packages_root_exists()
    test_discover_manifests_finds_bridge_voice_chat()
    test_pack_summary_lists_js_page_pack()
    test_load_local_registry_when_uricore_available()
  tests/test_packs_runtime.py:
    e: test_local_runtime_info,test_voice_plan_local_pack
    test_local_runtime_info()
    test_voice_plan_local_pack()
  tests/test_paths.py:
    e: test_app_package_dir_dev,test_web_and_assets_under_package,test_repo_root_and_packages_dir,test_frozen_bundle_branch,test_frozen_bundle_fallback_without_web
    test_app_package_dir_dev()
    test_web_and_assets_under_package()
    test_repo_root_and_packages_dir()
    test_frozen_bundle_branch(monkeypatch;tmp_path)
    test_frozen_bundle_fallback_without_web(monkeypatch;tmp_path)
  tests/test_remote_node_e2e.py:
    e: isolated_home,remote_node,test_probe_discovers_remote_node,test_scan_finds_node_via_extra_hosts,test_route_discovery_covers_uri_mcp_a2a,test_probe_tolerates_novnc_health_schema,test_end_to_end_node_then_routes,_NodeHandler,_NoVncHandler
    _NodeHandler: log_message(0),_send(1),do_GET(0)
    _NoVncHandler: log_message(0),do_GET(0)  # Mimics the noVNC example node: /health uses node/routes (not
    isolated_home(tmp_path;monkeypatch)
    remote_node()
    test_probe_discovers_remote_node(remote_node)
    test_scan_finds_node_via_extra_hosts(remote_node)
    test_route_discovery_covers_uri_mcp_a2a(remote_node)
    test_probe_tolerates_novnc_health_schema()
    test_end_to_end_node_then_routes(remote_node)
  tests/test_runtime_bind.py:
    e: test_find_free_port_returns_available_port,test_format_port_in_use_error_mentions_host_and_port
    test_find_free_port_returns_available_port()
    test_format_port_in_use_error_mentions_host_and_port()
  tests/test_runtime_handlers.py:
    e: test_make_handler_registers_core_routes
    test_make_handler_registers_core_routes()
  tests/test_storage.py:
    e: home,test_app_home_honours_env,test_now_iso_format,test_load_creates_default_when_missing,test_normalize_fills_defaults,test_save_load_round_trip,test_save_is_atomic_no_tmp_left,test_load_recovers_from_corrupt_json,test_add_event_appends_and_caps
    home(tmp_path;monkeypatch)
    test_app_home_honours_env(home)
    test_now_iso_format()
    test_load_creates_default_when_missing(home)
    test_normalize_fills_defaults()
    test_save_load_round_trip(home)
    test_save_is_atomic_no_tmp_left(home)
    test_load_recovers_from_corrupt_json(home)
    test_add_event_appends_and_caps()
  tests/test_urirun_bridge.py:
    e: test_urirun_info_shape,test_call_without_installed_urirun,test_parse_json_object_rejects_arrays,test_service_map_env_restores_previous
    test_urirun_info_shape()
    test_call_without_installed_urirun(monkeypatch)
    test_parse_json_object_rejects_arrays()
    test_service_map_env_restores_previous(monkeypatch)
  tests/test_urirun_integration.py:
    e: _registry,test_dispatch_local_unknown_route_returns_none,test_dispatch_local_dry_run_uses_urirun,test_dispatch_local_execute_with_policy,test_dispatch_local_without_registry_returns_none,test_scan_project_builds_registry,test_run_flow_routes_via_urirun,test_urirun_serve_http,test_cli_urirun_call_in_process_execute,test_cli_run_execute_uses_runtime_state,test_mcp_tools_and_a2a_card
    _registry()
    test_dispatch_local_unknown_route_returns_none()
    test_dispatch_local_dry_run_uses_urirun()
    test_dispatch_local_execute_with_policy()
    test_dispatch_local_without_registry_returns_none(monkeypatch)
    test_scan_project_builds_registry(tmp_path)
    test_run_flow_routes_via_urirun(tmp_path;monkeypatch)
    test_urirun_serve_http(tmp_path)
    test_cli_urirun_call_in_process_execute(tmp_path)
    test_cli_run_execute_uses_runtime_state(tmp_path;monkeypatch)
    test_mcp_tools_and_a2a_card()
  tests/test_url_params.py:
    e: test_voice_url_builds_prompt,test_voice_query_skips_empty,test_merge_voice_url
    test_voice_url_builds_prompt()
    test_voice_query_skips_empty()
    test_merge_voice_url()
  tests/test_voice_capabilities.py:
    e: server,test_voice_capabilities_structure,test_install_skips_when_packs_present,test_api_voice_capabilities,FakeClient
    FakeClient: health(0)
    server(tmp_path_factory)
    test_voice_capabilities_structure()
    test_install_skips_when_packs_present()
    test_api_voice_capabilities(server)
  tests/test_voice_pack_hint.py:
    e: test_voice_pack_hint_when_no_stt
    test_voice_pack_hint_when_no_stt()
  tests/test_voice_planner.py:
    e: test_regex_health,test_catalog_loads_examples,test_catalog_matches_description_keywords,test_auto_planner_fallback,test_llm_planner_flow_json
    test_regex_health()
    test_catalog_loads_examples()
    test_catalog_matches_description_keywords()
    test_auto_planner_fallback()
    test_llm_planner_flow_json()
  tests/test_webrtc_pipeline.py:
    e: test_node_voice_capabilities_includes_webrtc,test_webrtc_capabilities_when_loaded,test_webrtc_pack_hint_when_missing,test_install_skips_when_webrtc_present,FakeClient,MissingWebRtcClient
    FakeClient: health(0)
    MissingWebRtcClient: health(0)
    test_node_voice_capabilities_includes_webrtc()
    test_webrtc_capabilities_when_loaded()
    test_webrtc_pack_hint_when_missing()
    test_install_skips_when_webrtc_present()
  tests/test_webrtc_signal.py:
    e: test_webrtc_room_id_is_symmetric,test_initiator_is_lexicographically_smaller_url,test_signal_post_and_poll
    test_webrtc_room_id_is_symmetric()
    test_initiator_is_lexicographically_smaller_url()
    test_signal_post_and_poll()
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('app', '0.2.10', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 276, 'less').
project_file('desktop/dev-server.sh', 42, 'shell').
project_file('desktop/src-tauri/build.rs', 7, 'rust').
project_file('desktop/src-tauri/src/lib.rs', 20, 'rust').
project_file('desktop/src-tauri/src/main.rs', 10, 'rust').
project_file('docker/entrypoint-gui-novnc.sh', 40, 'shell').
project_file('docker/entrypoint-gui-test.sh', 68, 'shell').
project_file('docker/install-gui-deps.sh', 43, 'shell').
project_file('packages/ifuri-bridge/handlers/__init__.py', 5, 'python').
project_file('packages/ifuri-bridge/handlers/urisys_call.py', 63, 'python').
project_file('packages/ifuri-chat/handlers/__init__.py', 5, 'python').
project_file('packages/ifuri-chat/handlers/messages.py', 33, 'python').
project_file('packages/ifuri-page/handlers.js', 55, 'javascript').
project_file('packages/ifuri-page/manifest.js', 39, 'javascript').
project_file('packages/ifuri-voice/handlers/__init__.py', 5, 'python').
project_file('packages/ifuri-voice/handlers/plan.py', 27, 'python').
project_file('project.sh', 66, 'shell').
project_file('scripts/bootstrap-lenovo-packs.py', 61, 'python').
project_file('scripts/build-platform.py', 149, 'python').
project_file('scripts/cd-github.sh', 56, 'shell').
project_file('scripts/gui_smoke.py', 223, 'python').
project_file('scripts/ifuri_app_entry.py', 10, 'python').
project_file('scripts/run-ifuri-app.sh', 7, 'shell').
project_file('scripts/test-gui-docker.sh', 51, 'shell').
project_file('scripts/upgrade-lenovo-node.sh', 59, 'shell').
project_file('scripts/upgrade-lenovo-remote.py', 38, 'python').
project_file('scripts/vendor-uricore-js.sh', 24, 'shell').
project_file('src/ifuri_app/__init__.py', 10, 'python').
project_file('src/ifuri_app/__main__.py', 8, 'python').
project_file('src/ifuri_app/chat_channels.py', 549, 'python').
project_file('src/ifuri_app/chat_store.py', 91, 'python').
project_file('src/ifuri_app/cli.py', 676, 'python').
project_file('src/ifuri_app/connect_store.py', 217, 'python').
project_file('src/ifuri_app/connectors.py', 122, 'python').
project_file('src/ifuri_app/discovery.py', 127, 'python').
project_file('src/ifuri_app/flow_compile.py', 195, 'python').
project_file('src/ifuri_app/flow_engine.py', 130, 'python').
project_file('src/ifuri_app/flow_runner.py', 96, 'python').
project_file('src/ifuri_app/gui.py', 1006, 'python').
project_file('src/ifuri_app/gui_chat.py', 293, 'python').
project_file('src/ifuri_app/network_scan.py', 229, 'python').
project_file('src/ifuri_app/novnc_demo.py', 122, 'python').
project_file('src/ifuri_app/packs/__init__.py', 17, 'python').
project_file('src/ifuri_app/packs/loader.py', 78, 'python').
project_file('src/ifuri_app/packs/runtime.py', 63, 'python').
project_file('src/ifuri_app/paths.py', 37, 'python').
project_file('src/ifuri_app/remote_screen.py', 146, 'python').
project_file('src/ifuri_app/runtime.py', 45, 'python').
project_file('src/ifuri_app/runtime_bind.py', 79, 'python').
project_file('src/ifuri_app/runtime_handlers.py', 639, 'python').
project_file('src/ifuri_app/runtime_state.py', 172, 'python').
project_file('src/ifuri_app/sample_data.py', 80, 'python').
project_file('src/ifuri_app/storage.py', 98, 'python').
project_file('src/ifuri_app/urirun_bridge.py', 429, 'python').
project_file('src/ifuri_app/urisys_client.py', 159, 'python').
project_file('src/ifuri_app/url_params.py', 44, 'python').
project_file('src/ifuri_app/voice_pipeline.py', 198, 'python').
project_file('src/ifuri_app/voice_planner.py', 290, 'python').
project_file('src/ifuri_app/web/i18n.js', 115, 'javascript').
project_file('src/ifuri_app/web/page/handlers.js', 55, 'javascript').
project_file('src/ifuri_app/web/page/manifest.js', 39, 'javascript').
project_file('src/ifuri_app/web/page_runtime.js', 24, 'javascript').
project_file('src/ifuri_app/web/theme.js', 43, 'javascript').
project_file('src/ifuri_app/web/url_state.js', 71, 'javascript').
project_file('src/ifuri_app/web/voice.css', 364, 'css').
project_file('src/ifuri_app/web/voice.js', 642, 'javascript').
project_file('src/ifuri_app/web/webrtc_peer.js', 233, 'javascript').
project_file('src/ifuri_app/webrtc_pipeline.py', 132, 'python').
project_file('src/ifuri_app/webrtc_signal.py', 107, 'python').
project_file('tests/e2e/test_voice_playwright.py', 73, 'python').
project_file('tests/test_api_runtime.py', 249, 'python').
project_file('tests/test_chat_channels.py', 101, 'python').
project_file('tests/test_chat_history.py', 40, 'python').
project_file('tests/test_chat_migrate.py', 45, 'python').
project_file('tests/test_chat_store.py', 80, 'python').
project_file('tests/test_cli_chat.py', 18, 'python').
project_file('tests/test_cli_run.py', 114, 'python').
project_file('tests/test_connect_store.py', 232, 'python').
project_file('tests/test_connectors.py', 84, 'python').
project_file('tests/test_flow_compile.py', 59, 'python').
project_file('tests/test_gui_smoke.py', 239, 'python').
project_file('tests/test_ifuri_app.py', 143, 'python').
project_file('tests/test_novnc_demo.py', 113, 'python').
project_file('tests/test_packs_loader.py', 48, 'python').
project_file('tests/test_packs_runtime.py', 31, 'python').
project_file('tests/test_paths.py', 49, 'python').
project_file('tests/test_remote_node_e2e.py', 199, 'python').
project_file('tests/test_runtime_bind.py', 17, 'python').
project_file('tests/test_runtime_handlers.py', 21, 'python').
project_file('tests/test_storage.py', 87, 'python').
project_file('tests/test_urirun_bridge.py', 39, 'python').
project_file('tests/test_urirun_integration.py', 286, 'python').
project_file('tests/test_url_params.py', 27, 'python').
project_file('tests/test_voice_capabilities.py', 52, 'python').
project_file('tests/test_voice_pack_hint.py', 22, 'python').
project_file('tests/test_voice_planner.py', 70, 'python').
project_file('tests/test_webrtc_pipeline.py', 48, 'python').
project_file('tests/test_webrtc_signal.py', 39, 'python').
project_file('tree.sh', 5, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('packages/ifuri-bridge/handlers/urisys_call.py', '_endpoint', 2, 10, 3).
python_function('packages/ifuri-bridge/handlers/urisys_call.py', 'urisys_call', 2, 8, 8).
python_function('packages/ifuri-bridge/handlers/urisys_call.py', 'node_health', 2, 2, 6).
python_function('packages/ifuri-chat/handlers/messages.py', 'list_messages', 2, 4, 5).
python_function('packages/ifuri-chat/handlers/messages.py', 'list_channels', 2, 2, 3).
python_function('packages/ifuri-voice/handlers/plan.py', 'plan', 2, 11, 5).
python_function('scripts/bootstrap-lenovo-packs.py', 'call', 2, 2, 6).
python_function('scripts/bootstrap-lenovo-packs.py', 'main', 0, 5, 8).
python_function('scripts/build-platform.py', 'read_version', 0, 4, 6).
python_function('scripts/build-platform.py', 'platform_tag', 0, 4, 3).
python_function('scripts/build-platform.py', 'add_data_arg', 2, 2, 1).
python_function('scripts/build-platform.py', 'run_pyinstaller', 0, 8, 10).
python_function('scripts/build-platform.py', 'package_artifact', 3, 4, 7).
python_function('scripts/build-platform.py', 'main', 1, 2, 9).
python_function('scripts/gui_smoke.py', 'parse_args', 0, 1, 4).
python_function('scripts/gui_smoke.py', 'take_screenshot', 1, 5, 6).
python_function('scripts/gui_smoke.py', 'run_gui_smoke', 3, 2, 49).
python_function('scripts/gui_smoke.py', 'main', 0, 2, 8).
python_function('scripts/upgrade-lenovo-remote.py', 'main', 0, 2, 4).
python_function('src/ifuri_app/chat_channels.py', '_channel_id', 2, 1, 1).
python_function('src/ifuri_app/chat_channels.py', '_urisys_node_channels', 1, 7, 4).
python_function('src/ifuri_app/chat_channels.py', '_ifuri_peer_channels', 2, 11, 6).
python_function('src/ifuri_app/chat_channels.py', '_service_channels', 1, 11, 6).
python_function('src/ifuri_app/chat_channels.py', 'channels_from_scan', 1, 8, 7).
python_function('src/ifuri_app/chat_channels.py', 'list_chat_channels', 0, 2, 6).
python_function('src/ifuri_app/chat_channels.py', 'resolve_data_endpoint', 0, 10, 6).
python_function('src/ifuri_app/chat_channels.py', '_urisys_chat_unavailable', 1, 6, 3).
python_function('src/ifuri_app/chat_channels.py', '_router_unreachable', 1, 4, 4).
python_function('src/ifuri_app/chat_channels.py', '_local_chat_store', 0, 1, 1).
python_function('src/ifuri_app/chat_channels.py', 'fetch_chat_history', 1, 10, 12).
python_function('src/ifuri_app/chat_channels.py', 'fetch_chat_channel_index', 0, 3, 8).
python_function('src/ifuri_app/chat_channels.py', 'persist_chat_turn', 3, 13, 9).
python_function('src/ifuri_app/chat_channels.py', 'urisys_chat_available', 0, 3, 6).
python_function('src/ifuri_app/chat_channels.py', 'migrate_local_chat_to_urisys', 0, 16, 12).
python_function('src/ifuri_app/chat_channels.py', 'send_chat_message', 2, 18, 20).
python_function('src/ifuri_app/chat_channels.py', 'send_chat_message_routed', 2, 19, 11).
python_function('src/ifuri_app/chat_channels.py', '_payload_for_scheme', 2, 4, 0).
python_function('src/ifuri_app/chat_channels.py', '_short_json', 2, 2, 2).
python_function('src/ifuri_app/chat_channels.py', '_format_json_reply', 1, 1, 1).
python_function('src/ifuri_app/chat_channels.py', '_format_voice_reply', 1, 16, 7).
python_function('src/ifuri_app/chat_store.py', 'chat_store_path', 0, 2, 6).
python_function('src/ifuri_app/cli.py', 'print_json', 1, 1, 2).
python_function('src/ifuri_app/cli.py', 'cmd_init', 1, 5, 15).
python_function('src/ifuri_app/cli.py', 'cmd_app', 1, 1, 1).
python_function('src/ifuri_app/cli.py', 'cmd_serve', 1, 8, 13).
python_function('src/ifuri_app/cli.py', 'cmd_discover', 1, 1, 2).
python_function('src/ifuri_app/cli.py', 'cmd_voice', 1, 6, 14).
python_function('src/ifuri_app/cli.py', 'cmd_node_health', 1, 1, 3).
python_function('src/ifuri_app/cli.py', 'cmd_node_call', 1, 2, 4).
python_function('src/ifuri_app/cli.py', 'cmd_node_control_test', 1, 2, 4).
python_function('src/ifuri_app/cli.py', 'cmd_node_screen', 1, 7, 10).
python_function('src/ifuri_app/cli.py', 'cmd_flow_run', 1, 2, 3).
python_function('src/ifuri_app/cli.py', 'cmd_voice_plan', 1, 2, 3).
python_function('src/ifuri_app/cli.py', 'cmd_voice_catalog', 1, 1, 3).
python_function('src/ifuri_app/cli.py', 'cmd_voice_capabilities', 1, 2, 3).
python_function('src/ifuri_app/cli.py', 'cmd_voice_install_packs', 1, 3, 4).
python_function('src/ifuri_app/cli.py', 'cmd_webrtc_capabilities', 1, 2, 3).
python_function('src/ifuri_app/cli.py', 'cmd_webrtc_install_pack', 1, 3, 4).
python_function('src/ifuri_app/cli.py', 'cmd_webrtc_smoke', 1, 3, 4).
python_function('src/ifuri_app/cli.py', 'cmd_voice_run', 1, 3, 4).
python_function('src/ifuri_app/cli.py', 'cmd_chat_channels', 1, 2, 3).
python_function('src/ifuri_app/cli.py', 'cmd_chat_send', 1, 19, 8).
python_function('src/ifuri_app/cli.py', 'cmd_chat_migrate', 1, 2, 3).
python_function('src/ifuri_app/cli.py', 'cmd_chat_status', 1, 1, 2).
python_function('src/ifuri_app/cli.py', 'cmd_packs', 1, 1, 3).
python_function('src/ifuri_app/cli.py', 'cmd_urirun_info', 1, 3, 4).
python_function('src/ifuri_app/cli.py', 'cmd_urirun_call', 1, 6, 6).
python_function('src/ifuri_app/cli.py', 'cmd_urirun_scan', 1, 2, 3).
python_function('src/ifuri_app/cli.py', 'cmd_urirun_serve', 1, 4, 7).
python_function('src/ifuri_app/cli.py', 'cmd_urirun_mcp', 1, 7, 6).
python_function('src/ifuri_app/cli.py', 'cmd_flow_validate', 1, 1, 4).
python_function('src/ifuri_app/cli.py', 'cmd_run', 1, 6, 12).
python_function('src/ifuri_app/cli.py', 'cmd_expand', 1, 1, 4).
python_function('src/ifuri_app/cli.py', 'build_parser', 0, 1, 7).
python_function('src/ifuri_app/cli.py', 'main', 1, 2, 5).
python_function('src/ifuri_app/connect_store.py', 'catalog_url', 0, 2, 1).
python_function('src/ifuri_app/connect_store.py', '_normalize_route', 1, 8, 4).
python_function('src/ifuri_app/connect_store.py', '_normalize_install', 1, 6, 3).
python_function('src/ifuri_app/connect_store.py', '_version_of', 2, 4, 4).
python_function('src/ifuri_app/connect_store.py', '_normalize_package_item', 1, 25, 6).
python_function('src/ifuri_app/connect_store.py', 'normalize_packages', 1, 8, 5).
python_function('src/ifuri_app/connect_store.py', 'fetch_catalog', 1, 6, 9).
python_function('src/ifuri_app/connect_store.py', 'install_command', 1, 5, 2).
python_function('src/ifuri_app/connect_store.py', 'local_registry_status', 0, 5, 7).
python_function('src/ifuri_app/connect_store.py', 'example_payload_for', 2, 5, 2).
python_function('src/ifuri_app/connect_store.py', 'payload_form_fields', 2, 8, 9).
python_function('src/ifuri_app/connectors.py', 'route_scheme', 1, 6, 3).
python_function('src/ifuri_app/connectors.py', '_detail', 1, 5, 4).
python_function('src/ifuri_app/connectors.py', '_row', 2, 4, 4).
python_function('src/ifuri_app/connectors.py', 'normalize_routes', 1, 15, 10).
python_function('src/ifuri_app/connectors.py', 'group_by_scheme', 1, 2, 2).
python_function('src/ifuri_app/connectors.py', 'fetch_node_routes', 1, 6, 9).
python_function('src/ifuri_app/discovery.py', 'local_descriptor', 1, 5, 5).
python_function('src/ifuri_app/discovery.py', 'discover', 3, 9, 20).
python_function('src/ifuri_app/flow_compile.py', 'uri2flow_available', 0, 2, 0).
python_function('src/ifuri_app/flow_compile.py', '_parse_flow_input', 1, 12, 7).
python_function('src/ifuri_app/flow_compile.py', 'expand_flow_compiled', 1, 15, 12).
python_function('src/ifuri_app/flow_compile.py', 'flow_steps_from_document', 1, 11, 10).
python_function('src/ifuri_app/flow_compile.py', 'validate_flow_compiled', 1, 3, 6).
python_function('src/ifuri_app/flow_compile.py', 'validate_flow', 1, 8, 10).
python_function('src/ifuri_app/flow_compile.py', '_scheme', 1, 2, 2).
python_function('src/ifuri_app/flow_engine.py', 'expand_flow', 2, 2, 3).
python_function('src/ifuri_app/flow_engine.py', '_legacy_expand_flow', 2, 4, 5).
python_function('src/ifuri_app/flow_engine.py', 'clean_uri', 1, 1, 2).
python_function('src/ifuri_app/flow_engine.py', 'uri_scheme', 1, 2, 2).
python_function('src/ifuri_app/flow_engine.py', 'extract_steps', 1, 3, 9).
python_function('src/ifuri_app/flow_engine.py', 'flow_id_from_text', 2, 4, 4).
python_function('src/ifuri_app/flow_engine.py', 'classify_route', 1, 6, 3).
python_function('src/ifuri_app/flow_engine.py', 'dry_run_uri', 2, 2, 3).
python_function('src/ifuri_app/flow_engine.py', 'dry_run_flow', 1, 5, 4).
python_function('src/ifuri_app/flow_engine.py', 'as_pretty_json', 1, 1, 1).
python_function('src/ifuri_app/flow_runner.py', 'examples_root', 0, 4, 6).
python_function('src/ifuri_app/flow_runner.py', 'resolve_flow_path', 1, 8, 8).
python_function('src/ifuri_app/flow_runner.py', 'load_flow_steps', 1, 3, 3).
python_function('src/ifuri_app/flow_runner.py', 'run_flow_file', 1, 9, 9).
python_function('src/ifuri_app/gui.py', 'launch_gui', 0, 1, 3).
python_function('src/ifuri_app/network_scan.py', '_local_ipv4', 0, 2, 3).
python_function('src/ifuri_app/network_scan.py', '_subnet_hosts', 1, 3, 3).
python_function('src/ifuri_app/network_scan.py', 'probe_urisys_node', 2, 6, 5).
python_function('src/ifuri_app/network_scan.py', 'probe_ifuri_peer', 1, 4, 6).
python_function('src/ifuri_app/network_scan.py', '_collect_local_services', 0, 8, 6).
python_function('src/ifuri_app/network_scan.py', '_services_from_peers', 1, 9, 5).
python_function('src/ifuri_app/network_scan.py', 'scan_urisys_nodes', 0, 15, 16).
python_function('src/ifuri_app/network_scan.py', 'scan_network', 0, 17, 19).
python_function('src/ifuri_app/network_scan.py', 'try_mdns_urisys', 1, 2, 1).
python_function('src/ifuri_app/novnc_demo.py', 'demo_dir', 0, 4, 5).
python_function('src/ifuri_app/novnc_demo.py', 'read_env_file', 1, 7, 6).
python_function('src/ifuri_app/novnc_demo.py', 'dashboard_ports', 1, 5, 3).
python_function('src/ifuri_app/novnc_demo.py', 'dashboard_url', 1, 4, 3).
python_function('src/ifuri_app/novnc_demo.py', 'docker_available', 0, 1, 1).
python_function('src/ifuri_app/novnc_demo.py', 'compose_args', 1, 4, 1).
python_function('src/ifuri_app/novnc_demo.py', 'launch_info', 0, 3, 4).
python_function('src/ifuri_app/packs/loader.py', 'packages_root', 0, 1, 1).
python_function('src/ifuri_app/packs/loader.py', 'discover_manifests', 1, 3, 4).
python_function('src/ifuri_app/packs/loader.py', '_ensure_pack_path', 1, 2, 3).
python_function('src/ifuri_app/packs/loader.py', 'load_local_registry', 1, 5, 8).
python_function('src/ifuri_app/packs/loader.py', 'pack_summary', 1, 6, 7).
python_function('src/ifuri_app/packs/runtime.py', 'get_local_uri_runtime', 0, 2, 5).
python_function('src/ifuri_app/packs/runtime.py', 'dispatch_local_uri', 2, 5, 5).
python_function('src/ifuri_app/packs/runtime.py', 'local_runtime_info', 0, 3, 4).
python_function('src/ifuri_app/paths.py', 'app_package_dir', 0, 4, 5).
python_function('src/ifuri_app/paths.py', 'web_dir', 0, 1, 1).
python_function('src/ifuri_app/paths.py', 'assets_dir', 0, 1, 1).
python_function('src/ifuri_app/paths.py', 'repo_root', 0, 1, 1).
python_function('src/ifuri_app/paths.py', 'packages_dir', 0, 1, 1).
python_function('src/ifuri_app/remote_screen.py', 'resolve_node_id', 2, 10, 4).
python_function('src/ifuri_app/remote_screen.py', 'unwrap_result', 1, 5, 2).
python_function('src/ifuri_app/remote_screen.py', 'screen_uri', 0, 2, 0).
python_function('src/ifuri_app/remote_screen.py', 'capture_remote_screen', 1, 11, 8).
python_function('src/ifuri_app/remote_screen.py', 'probe_remote_control', 1, 7, 8).
python_function('src/ifuri_app/runtime_bind.py', '_port_listeners', 1, 4, 4).
python_function('src/ifuri_app/runtime_bind.py', 'format_port_in_use_error', 2, 3, 4).
python_function('src/ifuri_app/runtime_bind.py', '_port_available', 2, 2, 3).
python_function('src/ifuri_app/runtime_bind.py', 'find_free_port', 2, 3, 4).
python_function('src/ifuri_app/runtime_bind.py', 'bind_runtime_server', 3, 3, 4).
python_function('src/ifuri_app/runtime_handlers.py', 'json_bytes', 1, 1, 2).
python_function('src/ifuri_app/runtime_handlers.py', 'make_handler', 1, 1, 78).
python_function('src/ifuri_app/runtime_state.py', 'load_urirun_policy', 2, 5, 5).
python_function('src/ifuri_app/sample_data.py', 'default_workspace', 0, 3, 4).
python_function('src/ifuri_app/storage.py', 'app_home', 0, 2, 5).
python_function('src/ifuri_app/storage.py', 'workspace_path', 0, 1, 1).
python_function('src/ifuri_app/storage.py', 'ensure_home', 0, 1, 2).
python_function('src/ifuri_app/storage.py', 'now_iso', 0, 1, 2).
python_function('src/ifuri_app/storage.py', 'load_workspace', 0, 3, 16).
python_function('src/ifuri_app/storage.py', 'normalize_workspace', 1, 1, 2).
python_function('src/ifuri_app/storage.py', 'save_workspace', 1, 2, 14).
python_function('src/ifuri_app/storage.py', 'add_event', 2, 1, 3).
python_function('src/ifuri_app/urirun_bridge.py', 'urirun_info', 0, 3, 2).
python_function('src/ifuri_app/urirun_bridge.py', 'load_registry', 1, 2, 4).
python_function('src/ifuri_app/urirun_bridge.py', 'service_map_env', 1, 3, 3).
python_function('src/ifuri_app/urirun_bridge.py', 'parse_json_object', 1, 5, 3).
python_function('src/ifuri_app/urirun_bridge.py', 'call_urirun', 2, 9, 7).
python_function('src/ifuri_app/urirun_bridge.py', 'registry_summary', 1, 9, 5).
python_function('src/ifuri_app/urirun_bridge.py', 'default_urirun_registry', 0, 5, 3).
python_function('src/ifuri_app/urirun_bridge.py', '_is_route_not_found', 1, 7, 5).
python_function('src/ifuri_app/urirun_bridge.py', 'dispatch_local', 2, 11, 8).
python_function('src/ifuri_app/urirun_bridge.py', 'list_routes', 1, 6, 6).
python_function('src/ifuri_app/urirun_bridge.py', 'serve_http', 0, 7, 27).
python_function('src/ifuri_app/urirun_bridge.py', 'scan_project', 1, 10, 4).
python_function('src/ifuri_app/urirun_bridge.py', 'mcp_tools', 1, 6, 6).
python_function('src/ifuri_app/urirun_bridge.py', 'a2a_card', 1, 6, 6).
python_function('src/ifuri_app/urirun_bridge.py', 'serve_mcp', 0, 7, 6).
python_function('src/ifuri_app/urisys_client.py', 'default_node_endpoint', 0, 6, 4).
python_function('src/ifuri_app/urisys_client.py', 'node_llm_available', 1, 5, 6).
python_function('src/ifuri_app/urisys_client.py', 'node_webrtc_available', 1, 5, 6).
python_function('src/ifuri_app/urisys_client.py', 'node_voice_capabilities', 1, 8, 10).
python_function('src/ifuri_app/url_params.py', 'voice_query', 0, 3, 3).
python_function('src/ifuri_app/url_params.py', 'voice_url', 1, 2, 2).
python_function('src/ifuri_app/url_params.py', 'merge_voice_url', 1, 5, 8).
python_function('src/ifuri_app/voice_pipeline.py', '_extract_stt_text', 1, 9, 3).
python_function('src/ifuri_app/voice_pipeline.py', 'run_voice_command', 1, 23, 13).
python_function('src/ifuri_app/voice_pipeline.py', 'voice_capabilities', 1, 2, 4).
python_function('src/ifuri_app/voice_pipeline.py', 'install_voice_packs', 0, 9, 9).
python_function('src/ifuri_app/voice_pipeline.py', 'voice_pack_install_hint', 1, 3, 2).
python_function('src/ifuri_app/voice_pipeline.py', '_connection_hint', 2, 9, 4).
python_function('src/ifuri_app/voice_planner.py', 'voice_planner_mode', 0, 2, 3).
python_function('src/ifuri_app/voice_planner.py', 'load_flow_catalog', 0, 13, 13).
python_function('src/ifuri_app/voice_planner.py', 'node_has_llm', 1, 4, 5).
python_function('src/ifuri_app/voice_planner.py', '_flow_plan', 2, 2, 0).
python_function('src/ifuri_app/voice_planner.py', 'plan_with_regex', 1, 3, 2).
python_function('src/ifuri_app/voice_planner.py', '_catalog_tokens', 1, 8, 7).
python_function('src/ifuri_app/voice_planner.py', 'plan_with_catalog', 2, 11, 12).
python_function('src/ifuri_app/voice_planner.py', '_parse_llm_plan_json', 2, 11, 5).
python_function('src/ifuri_app/voice_planner.py', '_unwrap_llm_result', 1, 9, 2).
python_function('src/ifuri_app/voice_planner.py', 'plan_with_llm', 3, 13, 12).
python_function('src/ifuri_app/voice_planner.py', 'plan_voice_command', 1, 11, 9).
python_function('src/ifuri_app/webrtc_pipeline.py', 'webrtc_capabilities', 1, 2, 3).
python_function('src/ifuri_app/webrtc_pipeline.py', 'install_webrtc_pack', 0, 8, 9).
python_function('src/ifuri_app/webrtc_pipeline.py', 'webrtc_smoke', 0, 6, 5).
python_function('src/ifuri_app/webrtc_pipeline.py', 'webrtc_pack_install_hint', 1, 2, 1).
python_function('src/ifuri_app/webrtc_signal.py', 'local_peer_url', 0, 4, 2).
python_function('src/ifuri_app/webrtc_signal.py', 'webrtc_room_id', 2, 1, 2).
python_function('src/ifuri_app/webrtc_signal.py', 'is_webrtc_initiator', 2, 1, 1).
python_function('src/ifuri_app/webrtc_signal.py', '_purge_room', 2, 3, 4).
python_function('src/ifuri_app/webrtc_signal.py', 'post_signal', 1, 9, 8).
python_function('src/ifuri_app/webrtc_signal.py', 'poll_signals', 1, 10, 5).
python_function('src/ifuri_app/webrtc_signal.py', 'room_stats', 0, 1, 3).
python_function('tests/e2e/test_voice_playwright.py', 'launch_chromium', 1, 5, 6).
python_function('tests/e2e/test_voice_playwright.py', 'voice_server', 1, 1, 7).
python_function('tests/e2e/test_voice_playwright.py', 'test_voice_page_loads_and_lang_toggle', 1, 7, 14).
python_function('tests/e2e/test_voice_playwright.py', 'test_voice_static_i18n_bundle', 1, 3, 3).
python_function('tests/test_api_runtime.py', 'server', 1, 1, 7).
python_function('tests/test_api_runtime.py', '_get', 1, 2, 4).
python_function('tests/test_api_runtime.py', '_post', 2, 2, 7).
python_function('tests/test_api_runtime.py', 'test_health', 1, 4, 2).
python_function('tests/test_api_runtime.py', 'test_voice_page', 1, 4, 4).
python_function('tests/test_api_runtime.py', 'test_static_assets', 1, 4, 2).
python_function('tests/test_api_runtime.py', 'test_api_packs', 1, 6, 4).
python_function('tests/test_api_runtime.py', 'test_api_urirun_status', 1, 4, 2).
python_function('tests/test_api_runtime.py', 'test_api_urirun_call_contract', 1, 4, 2).
python_function('tests/test_api_runtime.py', 'test_api_urirun_call_local_registry_execute', 2, 6, 8).
python_function('tests/test_api_runtime.py', 'test_uri_call_voice_plan', 1, 4, 2).
python_function('tests/test_api_runtime.py', 'test_flow_validate', 1, 3, 2).
python_function('tests/test_api_runtime.py', 'test_flow_expand', 1, 6, 3).
python_function('tests/test_api_runtime.py', 'test_flow_expand_missing_text', 1, 5, 5).
python_function('tests/test_api_runtime.py', 'test_chat_channels', 1, 4, 2).
python_function('tests/test_api_runtime.py', 'test_chat_history', 1, 4, 3).
python_function('tests/test_api_runtime.py', 'test_network_scan', 1, 3, 1).
python_function('tests/test_api_runtime.py', 'test_voice_plan', 1, 3, 2).
python_function('tests/test_api_runtime.py', 'test_chat_send_empty', 1, 3, 2).
python_function('tests/test_api_runtime.py', 'test_concurrent_health', 1, 2, 8).
python_function('tests/test_api_runtime.py', 'test_not_found', 1, 5, 5).
python_function('tests/test_api_runtime.py', 'test_webrtc_signal_api', 1, 6, 4).
python_function('tests/test_chat_channels.py', 'test_channels_from_scan_groups_endpoints', 0, 9, 3).
python_function('tests/test_chat_channels.py', 'test_send_empty_message', 0, 2, 1).
python_function('tests/test_chat_channels.py', 'test_send_mcp_falls_back_when_router_unreachable', 0, 5, 4).
python_function('tests/test_chat_channels.py', 'test_send_mcp_routes_through_urisys_when_reachable', 0, 3, 5).
python_function('tests/test_chat_channels.py', 'test_send_mcp_reports_node_error_without_fallback', 0, 3, 4).
python_function('tests/test_chat_history.py', 'test_fetch_chat_history_from_node', 0, 3, 3).
python_function('tests/test_chat_history.py', 'test_persist_chat_turn', 0, 3, 3).
python_function('tests/test_chat_migrate.py', 'test_chat_available_false_on_404', 0, 2, 3).
python_function('tests/test_chat_migrate.py', 'test_migrate_skips_when_unavailable', 0, 2, 2).
python_function('tests/test_chat_migrate.py', 'test_migrate_uploads_local_messages', 2, 4, 7).
python_function('tests/test_chat_store.py', 'local_store', 2, 1, 4).
python_function('tests/test_chat_store.py', 'test_local_store_roundtrip', 1, 3, 3).
python_function('tests/test_chat_store.py', 'test_fetch_history_falls_back_on_404', 1, 4, 4).
python_function('tests/test_chat_store.py', 'test_fetch_history_falls_back_when_router_unreachable', 1, 4, 5).
python_function('tests/test_chat_store.py', 'test_persist_falls_back_on_404', 1, 4, 5).
python_function('tests/test_chat_store.py', 'test_persist_falls_back_when_router_unreachable', 1, 4, 6).
python_function('tests/test_cli_chat.py', 'test_cli_chat_status_calls_urisys_chat_available', 0, 2, 4).
python_function('tests/test_cli_run.py', 'run_cli', 2, 2, 6).
python_function('tests/test_cli_run.py', 'test_run_uri_dry_run_default', 1, 4, 2).
python_function('tests/test_cli_run.py', 'test_run_flow_file_dry_run', 2, 3, 3).
python_function('tests/test_cli_run.py', 'test_resolve_flow_path_finds_filename_in_any_examples_subdir', 2, 2, 5).
python_function('tests/test_cli_run.py', 'test_run_invalid_payload_json', 1, 3, 1).
python_function('tests/test_cli_run.py', 'test_run_target_not_file_or_uri', 1, 3, 4).
python_function('tests/test_cli_run.py', 'test_run_uri_execute_uses_runtime_not_dry', 2, 4, 3).
python_function('tests/test_cli_run.py', 'test_run_flow_execute_uses_runtime', 3, 3, 5).
python_function('tests/test_connect_store.py', 'test_catalog_url_env_override', 1, 3, 3).
python_function('tests/test_connect_store.py', 'test_normalize_packages_shapes', 0, 6, 1).
python_function('tests/test_connect_store.py', 'test_normalize_real_hub_shape', 0, 9, 4).
python_function('tests/test_connect_store.py', 'test_normalize_skips_invalid_and_accepts_bare_list', 0, 2, 1).
python_function('tests/test_connect_store.py', 'test_install_command_pip_and_unknown', 0, 3, 2).
python_function('tests/test_connect_store.py', 'test_payload_form_fields_from_params_and_placeholders', 0, 5, 1).
python_function('tests/test_connect_store.py', 'test_payload_form_fields_dedup', 0, 2, 1).
python_function('tests/test_connect_store.py', 'test_payload_form_fields_from_example_payload', 0, 4, 2).
python_function('tests/test_connect_store.py', 'test_payload_form_no_example_match_falls_back', 0, 2, 1).
python_function('tests/test_connect_store.py', 'test_example_payload_for', 0, 4, 1).
python_function('tests/test_connect_store.py', 'test_fetch_catalog_live_mock', 0, 5, 9).
python_function('tests/test_connect_store.py', 'test_fetch_catalog_unreachable', 0, 2, 1).
python_function('tests/test_connect_store.py', 'test_local_registry_status_unconfigured', 2, 4, 5).
python_function('tests/test_connect_store.py', 'test_local_registry_status_reads_registry', 2, 5, 5).
python_function('tests/test_connect_store.py', 'test_normalize_against_real_catalog_file', 0, 10, 9).
python_function('tests/test_connectors.py', 'test_route_scheme_variants', 0, 6, 1).
python_function('tests/test_connectors.py', 'test_normalize_list_of_dicts', 0, 7, 2).
python_function('tests/test_connectors.py', 'test_normalize_dict_of_bindings', 0, 4, 2).
python_function('tests/test_connectors.py', 'test_normalize_list_of_strings_and_bare_list', 0, 3, 2).
python_function('tests/test_connectors.py', 'test_normalize_alternate_uri_keys_and_dedup', 0, 3, 1).
python_function('tests/test_connectors.py', 'test_normalize_ignores_entries_without_uri', 0, 2, 1).
python_function('tests/test_connectors.py', 'test_group_by_scheme', 0, 3, 4).
python_function('tests/test_connectors.py', 'test_fetch_node_routes_handles_unreachable', 0, 5, 1).
python_function('tests/test_flow_compile.py', 'test_uri2flow_available', 0, 2, 2).
python_function('tests/test_flow_compile.py', 'test_expand_flow_uses_uri2flow', 0, 6, 5).
python_function('tests/test_flow_compile.py', 'test_expand_flow_compiled_graph_edges', 0, 3, 2).
python_function('tests/test_flow_compile.py', 'test_validate_flow_uses_legacy_fallback_without_uri2flow', 1, 5, 2).
python_function('tests/test_flow_compile.py', 'test_flow_steps_from_kvm_linkedin_flow', 0, 4, 6).
python_function('tests/test_gui_smoke.py', 'app', 0, 2, 3).
python_function('tests/test_gui_smoke.py', 'test_gui_module_imports', 0, 3, 1).
python_function('tests/test_gui_smoke.py', 'test_gui_smoke_script_parse', 0, 3, 3).
python_function('tests/test_gui_smoke.py', 'test_connectors_tab_present', 1, 4, 5).
python_function('tests/test_gui_smoke.py', 'test_connectors_render_groups_by_node_and_scheme', 1, 5, 6).
python_function('tests/test_gui_smoke.py', 'test_connectors_empty_state', 1, 2, 3).
python_function('tests/test_gui_smoke.py', 'test_lan_scan_auto_refreshes_connectors', 2, 2, 3).
python_function('tests/test_gui_smoke.py', 'test_novnc_section_present', 1, 2, 1).
python_function('tests/test_gui_smoke.py', 'test_novnc_open_dashboard', 2, 3, 5).
python_function('tests/test_gui_smoke.py', 'test_novnc_precheck_missing_dir', 2, 3, 3).
python_function('tests/test_gui_smoke.py', 'test_novnc_precheck_missing_docker', 3, 3, 4).
python_function('tests/test_gui_smoke.py', 'test_app_icon_asset_present', 0, 2, 2).
python_function('tests/test_gui_smoke.py', 'test_app_icon_set_on_window', 1, 2, 1).
python_function('tests/test_gui_smoke.py', 'test_connect_tab_present', 1, 4, 5).
python_function('tests/test_gui_smoke.py', 'test_connect_catalog_and_payload_form', 1, 4, 7).
python_function('tests/test_gui_smoke.py', 'test_connect_payload_form_enriched_from_example', 1, 3, 7).
python_function('tests/test_gui_smoke.py', 'test_connect_install_manual_no_subprocess', 2, 3, 8).
python_function('tests/test_gui_smoke.py', 'test_connect_catalog_error', 1, 3, 3).
python_function('tests/test_gui_smoke.py', 'test_connect_registry_status_renders', 2, 2, 3).
python_function('tests/test_gui_smoke.py', 'test_connect_registry_status_no_urirun', 2, 2, 3).
python_function('tests/test_gui_smoke.py', 'test_connect_registry_status_registry_without_urirun', 2, 2, 3).
python_function('tests/test_ifuri_app.py', 'test_plan_linkedin_flow', 0, 4, 1).
python_function('tests/test_ifuri_app.py', 'test_plan_health_flow', 0, 4, 1).
python_function('tests/test_ifuri_app.py', 'test_plan_voice_fallback', 0, 4, 2).
python_function('tests/test_ifuri_app.py', 'test_expand_flow_extracts_uris', 0, 6, 4).
python_function('tests/test_ifuri_app.py', 'test_scan_network_structure', 0, 7, 4).
python_function('tests/test_ifuri_app.py', 'test_node_voice_capabilities_without_voice_packs', 0, 4, 2).
python_function('tests/test_ifuri_app.py', 'test_node_voice_capabilities_with_stt_pack', 0, 3, 2).
python_function('tests/test_ifuri_app.py', 'test_screen_uri', 0, 3, 2).
python_function('tests/test_ifuri_app.py', 'test_resolve_node_id_order', 1, 5, 4).
python_function('tests/test_ifuri_app.py', 'test_unwrap_result_nested', 0, 2, 1).
python_function('tests/test_ifuri_app.py', 'test_capture_remote_screen_mock', 0, 3, 2).
python_function('tests/test_ifuri_app.py', 'test_connection_hint_on_refused', 0, 3, 1).
python_function('tests/test_novnc_demo.py', 'test_dashboard_url_defaults', 0, 7, 2).
python_function('tests/test_novnc_demo.py', 'test_dashboard_url_honours_overrides', 0, 4, 2).
python_function('tests/test_novnc_demo.py', 'test_dashboard_ports_reads_env', 1, 3, 3).
python_function('tests/test_novnc_demo.py', 'test_compose_args', 0, 4, 2).
python_function('tests/test_novnc_demo.py', 'test_read_env_file', 1, 6, 2).
python_function('tests/test_novnc_demo.py', 'test_dashboard_ports_reads_dotenv', 2, 7, 5).
python_function('tests/test_novnc_demo.py', 'test_shell_env_overrides_dotenv', 2, 2, 3).
python_function('tests/test_novnc_demo.py', 'test_demo_dir_env_override', 2, 3, 3).
python_function('tests/test_novnc_demo.py', 'test_demo_dir_resolves_sibling_examples', 1, 4, 3).
python_function('tests/test_novnc_demo.py', 'test_launch_info_shape', 0, 4, 4).
python_function('tests/test_packs_loader.py', 'test_packages_root_exists', 0, 3, 3).
python_function('tests/test_packs_loader.py', 'test_discover_manifests_finds_bridge_voice_chat', 0, 6, 2).
python_function('tests/test_packs_loader.py', 'test_pack_summary_lists_js_page_pack', 0, 6, 2).
python_function('tests/test_packs_loader.py', 'test_load_local_registry_when_uricore_available', 0, 7, 2).
python_function('tests/test_packs_runtime.py', 'test_local_runtime_info', 0, 3, 2).
python_function('tests/test_packs_runtime.py', 'test_voice_plan_local_pack', 0, 6, 3).
python_function('tests/test_paths.py', 'test_app_package_dir_dev', 0, 3, 2).
python_function('tests/test_paths.py', 'test_web_and_assets_under_package', 0, 3, 3).
python_function('tests/test_paths.py', 'test_repo_root_and_packages_dir', 0, 3, 3).
python_function('tests/test_paths.py', 'test_frozen_bundle_branch', 2, 2, 4).
python_function('tests/test_paths.py', 'test_frozen_bundle_fallback_without_web', 2, 2, 3).
python_function('tests/test_remote_node_e2e.py', 'isolated_home', 2, 1, 3).
python_function('tests/test_remote_node_e2e.py', 'remote_node', 0, 3, 8).
python_function('tests/test_remote_node_e2e.py', 'test_probe_discovers_remote_node', 1, 6, 2).
python_function('tests/test_remote_node_e2e.py', 'test_scan_finds_node_via_extra_hosts', 1, 3, 1).
python_function('tests/test_remote_node_e2e.py', 'test_route_discovery_covers_uri_mcp_a2a', 1, 8, 2).
python_function('tests/test_remote_node_e2e.py', 'test_probe_tolerates_novnc_health_schema', 0, 7, 10).
python_function('tests/test_remote_node_e2e.py', 'test_end_to_end_node_then_routes', 1, 4, 7).
python_function('tests/test_runtime_bind.py', 'test_find_free_port_returns_available_port', 0, 2, 1).
python_function('tests/test_runtime_bind.py', 'test_format_port_in_use_error_mentions_host_and_port', 0, 3, 1).
python_function('tests/test_runtime_handlers.py', 'test_make_handler_registers_core_routes', 0, 7, 4).
python_function('tests/test_storage.py', 'home', 2, 1, 2).
python_function('tests/test_storage.py', 'test_app_home_honours_env', 1, 3, 2).
python_function('tests/test_storage.py', 'test_now_iso_format', 0, 2, 3).
python_function('tests/test_storage.py', 'test_load_creates_default_when_missing', 1, 5, 3).
python_function('tests/test_storage.py', 'test_normalize_fills_defaults', 0, 5, 1).
python_function('tests/test_storage.py', 'test_save_load_round_trip', 1, 3, 5).
python_function('tests/test_storage.py', 'test_save_is_atomic_no_tmp_left', 1, 2, 3).
python_function('tests/test_storage.py', 'test_load_recovers_from_corrupt_json', 1, 3, 8).
python_function('tests/test_storage.py', 'test_add_event_appends_and_caps', 0, 6, 3).
python_function('tests/test_urirun_bridge.py', 'test_urirun_info_shape', 0, 4, 1).
python_function('tests/test_urirun_bridge.py', 'test_call_without_installed_urirun', 1, 5, 2).
python_function('tests/test_urirun_bridge.py', 'test_parse_json_object_rejects_arrays', 0, 1, 2).
python_function('tests/test_urirun_bridge.py', 'test_service_map_env_restores_previous', 1, 3, 2).
python_function('tests/test_urirun_integration.py', '_registry', 0, 1, 1).
python_function('tests/test_urirun_integration.py', 'test_dispatch_local_unknown_route_returns_none', 0, 2, 2).
python_function('tests/test_urirun_integration.py', 'test_dispatch_local_dry_run_uses_urirun', 0, 4, 2).
python_function('tests/test_urirun_integration.py', 'test_dispatch_local_execute_with_policy', 0, 3, 3).
python_function('tests/test_urirun_integration.py', 'test_dispatch_local_without_registry_returns_none', 1, 2, 2).
python_function('tests/test_urirun_integration.py', 'test_scan_project_builds_registry', 1, 5, 6).
python_function('tests/test_urirun_integration.py', 'test_run_flow_routes_via_urirun', 2, 4, 8).
python_function('tests/test_urirun_integration.py', 'test_urirun_serve_http', 1, 8, 22).
python_function('tests/test_urirun_integration.py', 'test_cli_urirun_call_in_process_execute', 1, 4, 6).
python_function('tests/test_urirun_integration.py', 'test_cli_run_execute_uses_runtime_state', 2, 5, 7).
python_function('tests/test_urirun_integration.py', 'test_mcp_tools_and_a2a_card', 0, 7, 5).
python_function('tests/test_url_params.py', 'test_voice_url_builds_prompt', 0, 4, 2).
python_function('tests/test_url_params.py', 'test_voice_query_skips_empty', 0, 2, 1).
python_function('tests/test_url_params.py', 'test_merge_voice_url', 0, 4, 1).
python_function('tests/test_voice_capabilities.py', 'server', 1, 1, 7).
python_function('tests/test_voice_capabilities.py', 'test_voice_capabilities_structure', 0, 4, 2).
python_function('tests/test_voice_capabilities.py', 'test_install_skips_when_packs_present', 0, 2, 3).
python_function('tests/test_voice_capabilities.py', 'test_api_voice_capabilities', 1, 3, 5).
python_function('tests/test_voice_pack_hint.py', 'test_voice_pack_hint_when_no_stt', 0, 4, 2).
python_function('tests/test_voice_planner.py', 'test_regex_health', 0, 3, 1).
python_function('tests/test_voice_planner.py', 'test_catalog_loads_examples', 0, 4, 2).
python_function('tests/test_voice_planner.py', 'test_catalog_matches_description_keywords', 0, 5, 2).
python_function('tests/test_voice_planner.py', 'test_auto_planner_fallback', 0, 4, 1).
python_function('tests/test_voice_planner.py', 'test_llm_planner_flow_json', 0, 4, 3).
python_function('tests/test_webrtc_pipeline.py', 'test_node_voice_capabilities_includes_webrtc', 0, 2, 2).
python_function('tests/test_webrtc_pipeline.py', 'test_webrtc_capabilities_when_loaded', 0, 4, 2).
python_function('tests/test_webrtc_pipeline.py', 'test_webrtc_pack_hint_when_missing', 0, 4, 2).
python_function('tests/test_webrtc_pipeline.py', 'test_install_skips_when_webrtc_present', 0, 2, 3).
python_function('tests/test_webrtc_signal.py', 'test_webrtc_room_id_is_symmetric', 0, 2, 1).
python_function('tests/test_webrtc_signal.py', 'test_initiator_is_lexicographically_smaller_url', 0, 3, 1).
python_function('tests/test_webrtc_signal.py', 'test_signal_post_and_poll', 0, 6, 3).

% ── Python Classes ───────────────────────────────────────
python_class('src/ifuri_app/chat_store.py', 'LocalChatStore').
python_method('LocalChatStore', '__init__', 1, 2, 3).
python_method('LocalChatStore', 'append', 3, 2, 7).
python_method('LocalChatStore', 'list_messages', 1, 7, 10).
python_method('LocalChatStore', 'list_channels', 0, 9, 12).
python_class('src/ifuri_app/discovery.py', 'DiscoveryResponder').
python_method('DiscoveryResponder', '__init__', 2, 1, 2).
python_method('DiscoveryResponder', 'start', 0, 3, 3).
python_method('DiscoveryResponder', 'stop', 0, 4, 3).
python_method('DiscoveryResponder', '_loop', 0, 9, 15).
python_class('src/ifuri_app/flow_compile.py', 'FlowCompileError').
python_class('src/ifuri_app/gui.py', 'IfuriDesktop').
python_method('IfuriDesktop', '__init__', 0, 1, 11).
python_method('IfuriDesktop', '_set_app_icon', 0, 3, 5).
python_method('IfuriDesktop', '_build_style', 0, 2, 4).
python_method('IfuriDesktop', '_build_ui', 0, 1, 12).
python_method('IfuriDesktop', '_build_flows_tab', 0, 2, 17).
python_method('IfuriDesktop', '_build_services_tab', 0, 2, 19).
python_method('IfuriDesktop', '_build_network_tab', 0, 4, 20).
python_method('IfuriDesktop', '_build_connectors_tab', 0, 2, 14).
python_method('IfuriDesktop', '_connector_endpoints', 0, 12, 7).
python_method('IfuriDesktop', 'refresh_connectors', 0, 2, 8).
python_method('IfuriDesktop', '_connectors_done', 1, 7, 8).
python_method('IfuriDesktop', '_toggle_connectors', 0, 4, 3).
python_method('IfuriDesktop', '_build_connect_tab', 0, 3, 20).
python_method('IfuriDesktop', 'refresh_catalog', 0, 1, 8).
python_method('IfuriDesktop', '_catalog_done', 1, 4, 6).
python_method('IfuriDesktop', '_selected_package', 0, 3, 3).
python_method('IfuriDesktop', '_on_package_select', 1, 3, 5).
python_method('IfuriDesktop', '_render_payload_form', 1, 10, 10).
python_method('IfuriDesktop', 'install_selected_connector', 0, 4, 14).
python_method('IfuriDesktop', '_install_done', 3, 4, 3).
python_method('IfuriDesktop', 'refresh_registry_status', 0, 4, 2).
python_method('IfuriDesktop', '_connect_log', 1, 1, 3).
python_method('IfuriDesktop', '_build_events_tab', 0, 2, 9).
python_method('IfuriDesktop', '_groups', 0, 1, 1).
python_method('IfuriDesktop', '_flows', 0, 2, 2).
python_method('IfuriDesktop', '_load_groups', 0, 5, 6).
python_method('IfuriDesktop', '_load_flows', 0, 5, 7).
python_method('IfuriDesktop', '_load_current_flow_text', 0, 2, 4).
python_method('IfuriDesktop', '_on_group_select', 0, 2, 3).
python_method('IfuriDesktop', '_on_flow_select', 0, 2, 3).
python_method('IfuriDesktop', 'new_group', 0, 2, 7).
python_method('IfuriDesktop', 'new_flow', 0, 3, 10).
python_method('IfuriDesktop', 'save_current_flow', 0, 2, 6).
python_method('IfuriDesktop', 'dry_run_current_flow', 0, 1, 11).
python_method('IfuriDesktop', '_refresh_services', 0, 3, 5).
python_method('IfuriDesktop', 'add_service', 0, 3, 9).
python_method('IfuriDesktop', 'start_runtime', 0, 5, 13).
python_method('IfuriDesktop', 'open_voice_ui', 0, 5, 7).
python_method('IfuriDesktop', 'stop_runtime', 0, 3, 3).
python_method('IfuriDesktop', 'discover_peers', 0, 5, 10).
python_method('IfuriDesktop', '_refresh_network_views', 1, 15, 7).
python_method('IfuriDesktop', '_novnc_precheck', 0, 3, 3).
python_method('IfuriDesktop', '_run_compose', 2, 1, 10).
python_method('IfuriDesktop', '_compose_done', 4, 3, 3).
python_method('IfuriDesktop', 'start_novnc_demo', 0, 2, 2).
python_method('IfuriDesktop', 'stop_novnc_demo', 0, 2, 2).
python_method('IfuriDesktop', 'open_novnc_dashboard', 0, 1, 4).
python_method('IfuriDesktop', '_on_device_select', 1, 4, 4).
python_method('IfuriDesktop', '_apply_node_endpoint', 1, 4, 6).
python_method('IfuriDesktop', '_maybe_first_run', 0, 2, 2).
python_method('IfuriDesktop', '_refresh_peers', 0, 5, 6).
python_method('IfuriDesktop', 'refresh_log', 0, 2, 5).
python_method('IfuriDesktop', 'append_log', 1, 1, 3).
python_method('IfuriDesktop', 'save_all', 0, 1, 1).
python_method('IfuriDesktop', '_urirun_serve_cmd', 1, 2, 2).
python_method('IfuriDesktop', 'start_urirun_serve', 0, 4, 9).
python_method('IfuriDesktop', 'stop_urirun_serve', 0, 4, 6).
python_method('IfuriDesktop', 'show_urirun_routes', 0, 1, 12).
python_method('IfuriDesktop', '_on_close', 0, 1, 4).
python_class('src/ifuri_app/gui.py', 'FirstRunWizard').
python_method('FirstRunWizard', '__init__', 1, 1, 16).
python_method('FirstRunWizard', '_scan', 0, 1, 8).
python_method('FirstRunWizard', '_scan_done', 2, 10, 6).
python_method('FirstRunWizard', '_on_pick', 1, 3, 3).
python_method('FirstRunWizard', '_save', 0, 1, 3).
python_method('FirstRunWizard', '_skip', 0, 1, 1).
python_method('FirstRunWizard', '_finish', 0, 2, 3).
python_class('src/ifuri_app/gui_chat.py', 'ChatTabMixin').
python_method('ChatTabMixin', '_build_chat_tab', 0, 1, 18).
python_method('ChatTabMixin', '_router_endpoint', 0, 6, 4).
python_method('ChatTabMixin', '_runtime_base_url', 0, 3, 5).
python_method('ChatTabMixin', '_chat_prompt_text', 0, 1, 2).
python_method('ChatTabMixin', '_sync_chat_prompt_url', 0, 4, 5).
python_method('ChatTabMixin', '_open_chat_in_browser', 0, 2, 3).
python_method('ChatTabMixin', '_refresh_chat_channels', 0, 1, 7).
python_method('ChatTabMixin', '_apply_chat_channels', 1, 16, 9).
python_method('ChatTabMixin', '_on_chat_channel_select', 1, 5, 7).
python_method('ChatTabMixin', '_load_chat_history_from_urisys', 1, 1, 11).
python_method('ChatTabMixin', '_apply_chat_history', 2, 3, 2).
python_method('ChatTabMixin', '_render_chat_thread', 0, 4, 5).
python_method('ChatTabMixin', '_append_chat', 2, 3, 4).
python_method('ChatTabMixin', '_send_chat_message', 0, 3, 13).
python_method('ChatTabMixin', '_finish_chat_reply', 2, 5, 5).
python_class('src/ifuri_app/runtime.py', 'RuntimeServer').
python_method('RuntimeServer', '__init__', 2, 1, 4).
python_method('RuntimeServer', 'url', 0, 2, 0).
python_method('RuntimeServer', 'start', 0, 3, 3).
python_method('RuntimeServer', 'stop', 0, 2, 3).
python_class('src/ifuri_app/runtime_bind.py', 'PortInUseError').
python_class('src/ifuri_app/runtime_bind.py', 'ThreadingHTTPServer').
python_class('src/ifuri_app/runtime_state.py', 'RuntimeState').
python_method('RuntimeState', '__init__', 2, 1, 0).
python_method('RuntimeState', 'load', 0, 2, 4).
python_method('RuntimeState', 'health', 0, 2, 11).
python_method('RuntimeState', 'call_uri', 3, 11, 12).
python_method('RuntimeState', 'run_flow', 2, 17, 17).
python_class('src/ifuri_app/urisys_client.py', 'UrisysNodeClient').
python_method('UrisysNodeClient', '__init__', 1, 2, 2).
python_method('UrisysNodeClient', 'health', 0, 1, 1).
python_method('UrisysNodeClient', 'call_uri', 2, 2, 1).
python_method('UrisysNodeClient', 'app_chat_messages', 1, 1, 2).
python_method('UrisysNodeClient', 'app_chat_channels', 0, 1, 2).
python_method('UrisysNodeClient', 'app_chat_append', 3, 2, 1).
python_method('UrisysNodeClient', '_get', 1, 3, 5).
python_method('UrisysNodeClient', '_post', 2, 5, 9).
python_class('tests/test_connect_store.py', '_CatalogHandler').
python_method('_CatalogHandler', 'log_message', 0, 1, 0).
python_method('_CatalogHandler', 'do_GET', 0, 1, 8).
python_class('tests/test_remote_node_e2e.py', '_NodeHandler').
python_method('_NodeHandler', 'log_message', 0, 1, 0).
python_method('_NodeHandler', '_send', 1, 1, 8).
python_method('_NodeHandler', 'do_GET', 0, 3, 3).
python_class('tests/test_remote_node_e2e.py', '_NoVncHandler').
python_method('_NoVncHandler', 'log_message', 0, 1, 0).
python_method('_NoVncHandler', 'do_GET', 0, 3, 8).
python_class('tests/test_voice_capabilities.py', 'FakeClient').
python_method('FakeClient', 'health', 0, 1, 0).
python_class('tests/test_webrtc_pipeline.py', 'FakeClient').
python_method('FakeClient', 'health', 0, 1, 0).
python_class('tests/test_webrtc_pipeline.py', 'MissingWebRtcClient').
python_method('MissingWebRtcClient', 'health', 0, 1, 0).

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────
makefile_target('help', '').
makefile_target('install', '').
makefile_target('install-dev', '').
makefile_target('vendor-uricore-js', '').
makefile_target('test', '').
makefile_target('test-api', '').
makefile_target('test-e2e', '').
makefile_target('install-e2e', '').
makefile_target('test-gui', '').
makefile_target('test-gui-docker', '').
makefile_target('smoke-novnc', '').
makefile_target('run-gui-novnc', '').
makefile_target('run', '').
makefile_target('run-gui', '').
makefile_target('run-voice', '').
makefile_target('run-voice-bg', '').
makefile_target('run-tauri-dev', '').
makefile_target('stop', '').
makefile_target('health', '').
makefile_target('api-smoke', '').
makefile_target('chat-status', '').
makefile_target('chat-migrate', '').
makefile_target('chat-migrate-dry', '').
makefile_target('voice-capabilities', '').
makefile_target('voice-install-packs', '').
makefile_target('webrtc-capabilities', '').
makefile_target('webrtc-install-pack', '').
makefile_target('webrtc-smoke', '').
makefile_target('urirun-info', '').
makefile_target('upgrade-node', '').
makefile_target('wheel', '').
makefile_target('build', '').
makefile_target('clean', '').
makefile_target('koru-cycle', '').
makefile_target('koru-plan', '').
makefile_target('koru-execute-twin', '').
makefile_target('koru-logs', '').
makefile_target('koru-status', '').

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', '*(not set)*', 'Get your API key from: https://openrouter.ai/keys').
env_variable('LLM_MODEL', 'llm://openrouter/deepseek/deepseek-v4-pro', '').
env_variable('PFIX_AUTO_APPLY', 'true', 'true = apply fixes without asking').
env_variable('PFIX_AUTO_INSTALL_DEPS', 'true', 'true = auto pip/uv install').
env_variable('PFIX_AUTO_RESTART', 'false', 'true = os.execv restart after fix').
env_variable('PFIX_MAX_RETRIES', '3', '').
env_variable('PFIX_DRY_RUN', 'false', '').
env_variable('PFIX_ENABLED', 'true', '').
env_variable('PFIX_GIT_COMMIT', 'false', 'true = auto-commit fixes').
env_variable('PFIX_GIT_PREFIX', 'pfix:', 'commit message prefix').
env_variable('PFIX_CREATE_BACKUPS', 'false', 'false = disable .pfix_backups/ directory').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-cli-tests.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('cli', 'argparse').
sumd_interface('cli', '').
sumd_interface('cli', '').
sumd_interface('desktop', '').
sumd_workflow('install', 'manual').
sumd_workflow_step('install', 1, '$(PYTHON) -m pip install -e .').
sumd_workflow('install-dev', 'manual').
sumd_workflow_step('install-dev', 1, 'if command -v uv >/dev/null 2>&1').
sumd_workflow_step('install-dev', 2, 'uv sync --group dev --group tellmesh').
sumd_workflow_step('install-dev', 3, 'else \').
sumd_workflow_step('install-dev', 4, '$(PYTHON) -m pip install -e ".[flows,dev,packs]"').
sumd_workflow_step('install-dev', 5, '$(PYTHON) -m pip install -e ../../tellmesh/uri2flow ../../tellmesh/uricore 2>/dev/null || true').
sumd_workflow_step('install-dev', 6, 'fi').
sumd_workflow('vendor-uricore-js', 'manual').
sumd_workflow_step('vendor-uricore-js', 1, 'bash scripts/vendor-uricore-js.sh').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, 'PYTHONPATH=src $(PYTHON) -m pytest -q --ignore=tests/e2e').
sumd_workflow('test-api', 'manual').
sumd_workflow_step('test-api', 1, 'PYTHONPATH=src $(PYTHON) -m pytest tests/test_api_runtime.py -q').
sumd_workflow('test-e2e', 'manual').
sumd_workflow_step('test-e2e', 1, 'PYTHONPATH=src $(PYTHON) -m pytest tests/e2e -q').
sumd_workflow('install-e2e', 'manual').
sumd_workflow_step('install-e2e', 1, '$(PYTHON) -m pip install pytest-playwright playwright').
sumd_workflow_step('install-e2e', 2, '$(PYTHON) -m playwright install chromium').
sumd_workflow('test-gui', 'manual').
sumd_workflow_step('test-gui', 1, 'PYTHONPATH=src $(PYTHON) -m pytest tests/test_gui_smoke.py -q').
sumd_workflow('test-gui-docker', 'manual').
sumd_workflow_step('test-gui-docker', 1, 'bash scripts/test-gui-docker.sh').
sumd_workflow('smoke-novnc', 'manual').
sumd_workflow_step('smoke-novnc', 1, '$(MAKE) -C ../examples/11-novnc_lan_flow up').
sumd_workflow_step('smoke-novnc', 2, 'PYTHONPATH=src xvfb-run -a $(PYTHON) scripts/gui_smoke.py --urisys-endpoint $(NODE) --out dist/gui-smoke --timeout 30').
sumd_workflow('run-gui-novnc', 'manual').
sumd_workflow_step('run-gui-novnc', 1, 'docker compose -f docker/docker-compose.novnc.yml up --build').
sumd_workflow_step('run-gui-novnc', 2, 'echo "open http://localhost:6080/vnc.html?autoconnect=1&resize=remote"').
sumd_workflow('run', 'manual').
sumd_workflow_step('run', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app $(ARGS)').
sumd_workflow('run-gui', 'manual').
sumd_workflow_step('run-gui', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app app').
sumd_workflow('run-voice', 'manual').
sumd_workflow_step('run-voice', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app voice \').
sumd_workflow_step('run-voice', 2, '--urisys-endpoint $(URISYS) --port $(PORT) --auto-port').
sumd_workflow('run-voice-bg', 'manual').
sumd_workflow_step('run-voice-bg', 1, '! test -f /tmp/ifuri-voice.pid || { echo "already running (pid $$(cat /tmp/ifuri-voice.pid))"').
sumd_workflow('run-tauri-dev', 'manual').
sumd_workflow_step('run-tauri-dev', 1, 'PORT=$(PORT) URISYS=$(URISYS) PYTHON=$(PYTHON) bash desktop/dev-server.sh').
sumd_workflow_step('run-tauri-dev', 2, 'cd desktop && cargo tauri dev').
sumd_workflow('stop', 'manual').
sumd_workflow_step('stop', 1, 'if test -f /tmp/ifuri-voice.pid').
sumd_workflow_step('stop', 2, 'kill $$(cat /tmp/ifuri-voice.pid) 2>/dev/null || true').
sumd_workflow_step('stop', 3, 'rm -f /tmp/ifuri-voice.pid').
sumd_workflow_step('stop', 4, 'echo "stopped"').
sumd_workflow_step('stop', 5, 'else \').
sumd_workflow_step('stop', 6, 'echo "no pid file (/tmp/ifuri-voice.pid)"').
sumd_workflow_step('stop', 7, 'fi').
sumd_workflow('health', 'manual').
sumd_workflow_step('health', 1, 'curl -fsS "http://127.0.0.1:$(PORT)/api/health" | $(PYTHON) -m json.tool | head -20').
sumd_workflow('api-smoke', 'manual').
sumd_workflow_step('api-smoke', 1, 'echo "== /voice =="').
sumd_workflow_step('api-smoke', 2, 'curl -fsS "http://127.0.0.1:$(PORT)/voice" | head -c 120').
sumd_workflow_step('api-smoke', 3, 'echo "== /api/packs =="').
sumd_workflow_step('api-smoke', 4, 'curl -fsS "http://127.0.0.1:$(PORT)/api/packs" | $(PYTHON) -m json.tool | head -12').
sumd_workflow_step('api-smoke', 5, 'echo "== /api/chat/channels =="').
sumd_workflow_step('api-smoke', 6, 'curl -fsS "http://127.0.0.1:$(PORT)/api/chat/channels?timeout=0.5" | $(PYTHON) -m json.tool | head -15').
sumd_workflow_step('api-smoke', 7, 'echo "== /api/chat/history =="').
sumd_workflow_step('api-smoke', 8, 'curl -fsS "http://127.0.0.1:$(PORT)/api/chat/history?channel_id=smoke" | $(PYTHON) -m json.tool | head -10').
sumd_workflow('chat-status', 'manual').
sumd_workflow_step('chat-status', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app chat-status --endpoint $(URISYS)').
sumd_workflow('chat-migrate', 'manual').
sumd_workflow_step('chat-migrate', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app chat-migrate --endpoint $(URISYS)').
sumd_workflow('chat-migrate-dry', 'manual').
sumd_workflow_step('chat-migrate-dry', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app chat-migrate --endpoint $(URISYS) --dry-run').
sumd_workflow('voice-capabilities', 'manual').
sumd_workflow_step('voice-capabilities', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app voice-capabilities --endpoint $(URISYS)').
sumd_workflow('voice-install-packs', 'manual').
sumd_workflow_step('voice-install-packs', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app voice-install-packs --endpoint $(URISYS)').
sumd_workflow('webrtc-capabilities', 'manual').
sumd_workflow_step('webrtc-capabilities', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-capabilities --endpoint $(URISYS)').
sumd_workflow('webrtc-install-pack', 'manual').
sumd_workflow_step('webrtc-install-pack', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-install-pack --endpoint $(URISYS)').
sumd_workflow('webrtc-smoke', 'manual').
sumd_workflow_step('webrtc-smoke', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-smoke --endpoint $(URISYS)').
sumd_workflow('urirun-info', 'manual').
sumd_workflow_step('urirun-info', 1, 'PYTHONPATH=src $(PYTHON) -m ifuri_app urirun-info').
sumd_workflow('upgrade-node', 'manual').
sumd_workflow('wheel', 'manual').
sumd_workflow_step('wheel', 1, '$(PYTHON) -m pip wheel -w dist .').
sumd_workflow('build', 'manual').
sumd_workflow_step('build', 1, '$(PYTHON) scripts/build-platform.py').
sumd_workflow('clean', 'manual').
sumd_workflow_step('clean', 1, 'rm -rf dist/*.whl dist/*.tar.gz dist/*.zip .pytest_cache **/__pycache__').
sumd_workflow('koru-cycle', 'manual').
sumd_workflow_step('koru-cycle', 1, 'echo "▶ Koru cycle (apply=true) — użyje execute-via-twin-human dla kvm/lenovo (realne kvm://laptop/... do queue.log + done z actor)"').
sumd_workflow_step('koru-cycle', 2, '$(PYTHON) -m urirun_connector_loop cycle --project . --apply || $(PYTHON) -c \'\').
sumd_workflow('koru-plan', 'manual').
sumd_workflow_step('koru-plan', 1, 'echo "▶ Dry-run plan (bez apply)"').
sumd_workflow_step('koru-plan', 2, '$(PYTHON) -m urirun_connector_loop cycle --project .').
sumd_workflow('koru-execute-twin', 'manual').
sumd_workflow_step('koru-execute-twin', 1, 'echo "▶ Bezpośrednie wykonanie przez twin-human (dla testu IFURI-226 lub podobnego)"').
sumd_workflow_step('koru-execute-twin', 2, '$(PYTHON) -c \'\').
sumd_workflow('koru-logs', 'manual').
sumd_workflow_step('koru-logs', 1, 'echo "▶ Ostatnie linie queue.log (to co widać w panelu Na żywo)"').
sumd_workflow_step('koru-logs', 2, 'tail -30 ../.planfile/.koru/queue.log 2>/dev/null || tail -30 .planfile/.koru/queue.log 2>/dev/null || echo "brak queue.log"').
sumd_workflow('koru-status', 'manual').
sumd_workflow_step('koru-status', 1, 'echo "▶ Stan koru + queue"').
sumd_workflow_step('koru-status', 2, '$(PYTHON) -c \'\').
```

## Call Graph

*351 nodes · 500 edges · 41 modules · CC̄=4.1*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `make_handler` *(in src.ifuri_app.runtime_handlers)* | 1 | 1 | 436 | **437** |
| `build_parser` *(in src.ifuri_app.cli)* | 1 | 1 | 174 | **175** |
| `run_gui_smoke` *(in scripts.gui_smoke)* | 2 | 1 | 93 | **94** |
| `serve_http` *(in src.ifuri_app.urirun_bridge)* | 7 | 1 | 46 | **47** |
| `run_flow` *(in src.ifuri_app.runtime_state.RuntimeState)* | 17 ⚠ | 0 | 41 | **41** |
| `scan_network` *(in src.ifuri_app.network_scan)* | 17 ⚠ | 5 | 35 | **40** |
| `print_json` *(in src.ifuri_app.cli)* | 1 | 36 | 2 | **38** |
| `save_workspace` *(in src.ifuri_app.storage)* | 2 | 22 | 14 | **36** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/if-uri/app
# generated in 0.18s
# nodes: 351 | edges: 500 | modules: 41
# CC̄=4.1

HUBS[20]:
  src.ifuri_app.runtime_handlers.make_handler
    CC=1  in:1  out:436  total:437
  src.ifuri_app.cli.build_parser
    CC=1  in:1  out:174  total:175
  scripts.gui_smoke.run_gui_smoke
    CC=2  in:1  out:93  total:94
  src.ifuri_app.urirun_bridge.serve_http
    CC=7  in:1  out:46  total:47
  src.ifuri_app.runtime_state.RuntimeState.run_flow
    CC=17  in:0  out:41  total:41
  src.ifuri_app.network_scan.scan_network
    CC=17  in:5  out:35  total:40
  src.ifuri_app.cli.print_json
    CC=1  in:36  out:2  total:38
  src.ifuri_app.storage.save_workspace
    CC=2  in:22  out:14  total:36
  src.ifuri_app.chat_channels.send_chat_message
    CC=18  in:2  out:33  total:35
  src.ifuri_app.storage.load_workspace
    CC=3  in:17  out:18  total:35
  src.ifuri_app.connect_store._normalize_package_item
    CC=25  in:1  out:33  total:34
  src.ifuri_app.voice_pipeline.run_voice_command
    CC=23  in:3  out:30  total:33
  src.ifuri_app.chat_channels.send_chat_message_routed
    CC=19  in:3  out:28  total:31
  src.ifuri_app.remote_screen.probe_remote_control
    CC=7  in:4  out:27  total:31
  src.ifuri_app.discovery.discover
    CC=9  in:2  out:29  total:31
  src.ifuri_app.chat_channels.migrate_local_chat_to_urisys
    CC=16  in:2  out:26  total:28
  src.ifuri_app.remote_screen.capture_remote_screen
    CC=11  in:5  out:23  total:28
  src.ifuri_app.flow_compile.expand_flow_compiled
    CC=15  in:1  out:26  total:27
  src.ifuri_app.voice_planner.load_flow_catalog
    CC=13  in:5  out:21  total:26
  src.ifuri_app.runtime_state.RuntimeState.call_uri
    CC=11  in:0  out:25  total:25

MODULES:
  packages.ifuri-bridge.handlers.urisys_call  [3 funcs]
    _endpoint  CC=10  out:13
    node_health  CC=2  out:6
    urisys_call  CC=8  out:17
  packages.ifuri-page.handlers  [5 funcs]
    get_url_state  CC=10  out:2
    next  CC=3  out:1
    set_url_state  CC=9  out:2
    toggle_view  CC=9  out:4
    urlState  CC=3  out:0
  packages.ifuri-voice.handlers.plan  [1 funcs]
    plan  CC=11  out:14
  scripts.bootstrap-lenovo-packs  [2 funcs]
    call  CC=2  out:6
    main  CC=5  out:13
  scripts.build-platform  [5 funcs]
    main  CC=2  out:13
    package_artifact  CC=4  out:10
    platform_tag  CC=4  out:4
    read_version  CC=4  out:10
    run_pyinstaller  CC=8  out:23
  scripts.gui_smoke  [3 funcs]
    main  CC=2  out:9
    parse_args  CC=1  out:6
    run_gui_smoke  CC=2  out:93
  src.ifuri_app.chat_channels  [20 funcs]
    _channel_id  CC=1  out:1
    _format_json_reply  CC=1  out:1
    _format_voice_reply  CC=16  out:23
    _ifuri_peer_channels  CC=11  out:17
    _local_chat_store  CC=1  out:1
    _payload_for_scheme  CC=4  out:0
    _router_unreachable  CC=4  out:5
    _service_channels  CC=11  out:14
    _urisys_chat_unavailable  CC=6  out:7
    _urisys_node_channels  CC=7  out:10
  src.ifuri_app.chat_store  [2 funcs]
    __init__  CC=2  out:3
    chat_store_path  CC=2  out:6
  src.ifuri_app.cli  [34 funcs]
    build_parser  CC=1  out:174
    cmd_app  CC=1  out:1
    cmd_chat_channels  CC=2  out:3
    cmd_chat_migrate  CC=2  out:3
    cmd_chat_send  CC=19  out:18
    cmd_chat_status  CC=1  out:2
    cmd_discover  CC=1  out:2
    cmd_expand  CC=1  out:4
    cmd_flow_run  CC=2  out:3
    cmd_flow_validate  CC=1  out:4
  src.ifuri_app.connect_store  [9 funcs]
    _normalize_install  CC=6  out:7
    _normalize_package_item  CC=25  out:33
    _version_of  CC=4  out:5
    catalog_url  CC=2  out:1
    fetch_catalog  CC=6  out:11
    install_command  CC=5  out:4
    local_registry_status  CC=5  out:12
    normalize_packages  CC=8  out:7
    payload_form_fields  CC=8  out:17
  src.ifuri_app.connectors  [5 funcs]
    _detail  CC=5  out:5
    _row  CC=4  out:6
    fetch_node_routes  CC=6  out:11
    normalize_routes  CC=15  out:21
    route_scheme  CC=6  out:5
  src.ifuri_app.discovery  [3 funcs]
    _loop  CC=9  out:16
    discover  CC=9  out:29
    local_descriptor  CC=5  out:12
  src.ifuri_app.flow_compile  [6 funcs]
    _parse_flow_input  CC=12  out:11
    expand_flow_compiled  CC=15  out:26
    flow_steps_from_document  CC=11  out:11
    uri2flow_available  CC=2  out:0
    validate_flow  CC=8  out:13
    validate_flow_compiled  CC=3  out:6
  src.ifuri_app.flow_engine  [10 funcs]
    _legacy_expand_flow  CC=4  out:5
    as_pretty_json  CC=1  out:1
    classify_route  CC=6  out:6
    clean_uri  CC=1  out:2
    dry_run_flow  CC=5  out:8
    dry_run_uri  CC=2  out:3
    expand_flow  CC=2  out:3
    extract_steps  CC=3  out:9
    flow_id_from_text  CC=4  out:5
    uri_scheme  CC=2  out:2
  src.ifuri_app.flow_runner  [4 funcs]
    examples_root  CC=4  out:9
    load_flow_steps  CC=3  out:3
    resolve_flow_path  CC=8  out:13
    run_flow_file  CC=9  out:14
  src.ifuri_app.gui  [24 funcs]
    _finish  CC=2  out:3
    _scan  CC=1  out:10
    __init__  CC=1  out:11
    _apply_node_endpoint  CC=4  out:6
    _connector_endpoints  CC=12  out:13
    _novnc_precheck  CC=3  out:4
    _on_package_select  CC=3  out:6
    _render_payload_form  CC=10  out:20
    _run_compose  CC=1  out:11
    _set_app_icon  CC=3  out:5
  src.ifuri_app.gui_chat  [5 funcs]
    _load_chat_history_from_urisys  CC=1  out:17
    _on_chat_channel_select  CC=5  out:12
    _refresh_chat_channels  CC=1  out:9
    _router_endpoint  CC=6  out:8
    _sync_chat_prompt_url  CC=4  out:6
  src.ifuri_app.network_scan  [6 funcs]
    _collect_local_services  CC=8  out:13
    _local_ipv4  CC=2  out:3
    probe_urisys_node  CC=6  out:12
    scan_network  CC=17  out:35
    scan_urisys_nodes  CC=15  out:19
    try_mdns_urisys  CC=2  out:1
  src.ifuri_app.novnc_demo  [7 funcs]
    compose_args  CC=4  out:1
    dashboard_ports  CC=5  out:4
    dashboard_url  CC=4  out:4
    demo_dir  CC=4  out:7
    docker_available  CC=1  out:1
    launch_info  CC=3  out:5
    read_env_file  CC=7  out:10
  src.ifuri_app.packs.loader  [5 funcs]
    _ensure_pack_path  CC=2  out:3
    discover_manifests  CC=3  out:4
    load_local_registry  CC=5  out:8
    pack_summary  CC=6  out:10
    packages_root  CC=1  out:1
  src.ifuri_app.packs.runtime  [3 funcs]
    dispatch_local_uri  CC=5  out:5
    get_local_uri_runtime  CC=2  out:5
    local_runtime_info  CC=3  out:4
  src.ifuri_app.paths  [5 funcs]
    app_package_dir  CC=4  out:7
    assets_dir  CC=1  out:1
    packages_dir  CC=1  out:1
    repo_root  CC=1  out:1
    web_dir  CC=1  out:1
  src.ifuri_app.remote_screen  [5 funcs]
    capture_remote_screen  CC=11  out:23
    probe_remote_control  CC=7  out:27
    resolve_node_id  CC=10  out:8
    screen_uri  CC=2  out:0
    unwrap_result  CC=5  out:4
  src.ifuri_app.runtime  [1 funcs]
    __init__  CC=1  out:4
  src.ifuri_app.runtime_bind  [5 funcs]
    _port_available  CC=2  out:3
    _port_listeners  CC=4  out:4
    bind_runtime_server  CC=3  out:4
    find_free_port  CC=3  out:4
    format_port_in_use_error  CC=3  out:4
  src.ifuri_app.runtime_handlers  [2 funcs]
    json_bytes  CC=1  out:2
    make_handler  CC=1  out:436
  src.ifuri_app.runtime_state  [5 funcs]
    call_uri  CC=11  out:25
    health  CC=2  out:17
    load  CC=2  out:4
    run_flow  CC=17  out:41
    load_urirun_policy  CC=5  out:6
  src.ifuri_app.sample_data  [1 funcs]
    default_workspace  CC=3  out:4
  src.ifuri_app.storage  [8 funcs]
    add_event  CC=1  out:3
    app_home  CC=2  out:5
    ensure_home  CC=1  out:2
    load_workspace  CC=3  out:18
    normalize_workspace  CC=1  out:16
    now_iso  CC=1  out:2
    save_workspace  CC=2  out:14
    workspace_path  CC=1  out:1
  src.ifuri_app.urirun_bridge  [15 funcs]
    _is_route_not_found  CC=7  out:10
    a2a_card  CC=6  out:6
    call_urirun  CC=9  out:7
    default_urirun_registry  CC=5  out:5
    dispatch_local  CC=11  out:8
    list_routes  CC=6  out:6
    load_registry  CC=2  out:4
    mcp_tools  CC=6  out:6
    parse_json_object  CC=5  out:4
    registry_summary  CC=9  out:18
  src.ifuri_app.urisys_client  [5 funcs]
    __init__  CC=2  out:2
    default_node_endpoint  CC=6  out:7
    node_llm_available  CC=5  out:7
    node_voice_capabilities  CC=8  out:12
    node_webrtc_available  CC=5  out:7
  src.ifuri_app.url_params  [2 funcs]
    voice_query  CC=3  out:3
    voice_url  CC=2  out:2
  src.ifuri_app.voice_pipeline  [5 funcs]
    _extract_stt_text  CC=9  out:10
    install_voice_packs  CC=9  out:20
    run_voice_command  CC=23  out:30
    voice_capabilities  CC=2  out:4
    voice_pack_install_hint  CC=3  out:3
  src.ifuri_app.voice_planner  [10 funcs]
    _catalog_tokens  CC=8  out:12
    _flow_plan  CC=2  out:0
    _parse_llm_plan_json  CC=11  out:17
    load_flow_catalog  CC=13  out:21
    node_has_llm  CC=4  out:6
    plan_voice_command  CC=11  out:14
    plan_with_catalog  CC=11  out:15
    plan_with_llm  CC=13  out:19
    plan_with_regex  CC=3  out:2
    voice_planner_mode  CC=2  out:3
  src.ifuri_app.web.i18n  [2 funcs]
    t  CC=4  out:1
    val  CC=1  out:0
  src.ifuri_app.web.theme  [5 funcs]
    applyLang  CC=2  out:0
    applyTheme  CC=2  out:2
    initFromUrl  CC=2  out:3
    setLang  CC=2  out:2
    setTheme  CC=2  out:2
  src.ifuri_app.web.url_state  [9 funcs]
    base  CC=4  out:2
    cur  CC=4  out:2
    get  CC=2  out:1
    onPopState  CC=1  out:3
    patch  CC=1  out:2
    read  CC=2  out:2
    set  CC=1  out:1
    withParams  CC=9  out:6
    write  CC=8  out:9
  src.ifuri_app.web.voice  [73 funcs]
    I  CC=1  out:0
    SR  CC=4  out:2
    T  CC=1  out:0
    U  CC=1  out:0
    _toggleViewDirect  CC=3  out:4
    api  CC=4  out:3
    appendMessage  CC=7  out:5
    applyPromptFromUrl  CC=4  out:2
    applyUiLanguage  CC=8  out:4
    applyViewFromUrl  CC=7  out:5
  src.ifuri_app.web.webrtc_peer  [22 funcs]
    _applySignal  CC=10  out:5
    _dispatch  CC=8  out:7
    _poll  CC=7  out:5
    _setStatus  CC=2  out:1
    _wireChannel  CC=2  out:3
    answer  CC=1  out:1
    clearTimeout  CC=1  out:1
    isReady  CC=2  out:1
    offer  CC=1  out:1
    payload  CC=8  out:5
  src.ifuri_app.webrtc_pipeline  [4 funcs]
    install_webrtc_pack  CC=8  out:17
    webrtc_capabilities  CC=2  out:3
    webrtc_pack_install_hint  CC=2  out:1
    webrtc_smoke  CC=6  out:14
  src.ifuri_app.webrtc_signal  [5 funcs]
    _purge_room  CC=3  out:4
    local_peer_url  CC=4  out:2
    poll_signals  CC=10  out:9
    post_signal  CC=9  out:12
    webrtc_room_id  CC=1  out:3

EDGES:
  packages.ifuri-voice.handlers.plan.plan → src.ifuri_app.voice_planner.plan_voice_command
  packages.ifuri-page.handlers.get_url_state → packages.ifuri-page.handlers.urlState
  packages.ifuri-page.handlers.set_url_state → packages.ifuri-page.handlers.urlState
  packages.ifuri-page.handlers.toggle_view → packages.ifuri-page.handlers.urlState
  packages.ifuri-bridge.handlers.urisys_call.urisys_call → packages.ifuri-bridge.handlers.urisys_call._endpoint
  packages.ifuri-bridge.handlers.urisys_call.node_health → packages.ifuri-bridge.handlers.urisys_call._endpoint
  src.ifuri_app.webrtc_signal.local_peer_url → src.ifuri_app.network_scan._local_ipv4
  src.ifuri_app.webrtc_signal.post_signal → src.ifuri_app.webrtc_signal._purge_room
  src.ifuri_app.webrtc_signal.poll_signals → src.ifuri_app.webrtc_signal._purge_room
  src.ifuri_app.gui.IfuriDesktop.__init__ → src.ifuri_app.storage.load_workspace
  src.ifuri_app.gui.IfuriDesktop._set_app_icon → src.ifuri_app.paths.assets_dir
  src.ifuri_app.gui.IfuriDesktop._connector_endpoints → src.ifuri_app.web.url_state.set
  src.ifuri_app.gui.IfuriDesktop.refresh_connectors → src.ifuri_app.connectors.fetch_node_routes
  src.ifuri_app.gui.IfuriDesktop.refresh_catalog → src.ifuri_app.connect_store.fetch_catalog
  src.ifuri_app.gui.IfuriDesktop._on_package_select → src.ifuri_app.connect_store.install_command
  src.ifuri_app.gui.IfuriDesktop._render_payload_form → packages.ifuri-page.handlers.next
  src.ifuri_app.gui.IfuriDesktop._render_payload_form → src.ifuri_app.connect_store.payload_form_fields
  src.ifuri_app.gui.IfuriDesktop.install_selected_connector → src.ifuri_app.connect_store.install_command
  src.ifuri_app.gui.IfuriDesktop.refresh_registry_status → src.ifuri_app.connect_store.local_registry_status
  src.ifuri_app.gui.IfuriDesktop.save_current_flow → src.ifuri_app.storage.add_event
  src.ifuri_app.gui.IfuriDesktop.dry_run_current_flow → src.ifuri_app.flow_engine.dry_run_flow
  src.ifuri_app.gui.IfuriDesktop.dry_run_current_flow → src.ifuri_app.storage.add_event
  src.ifuri_app.gui.IfuriDesktop.dry_run_current_flow → src.ifuri_app.storage.save_workspace
  src.ifuri_app.gui.IfuriDesktop.dry_run_current_flow → src.ifuri_app.flow_engine.as_pretty_json
  src.ifuri_app.gui.IfuriDesktop.add_service → src.ifuri_app.storage.add_event
  src.ifuri_app.gui.IfuriDesktop.start_runtime → src.ifuri_app.storage.save_workspace
  src.ifuri_app.gui.IfuriDesktop.open_voice_ui → src.ifuri_app.url_params.voice_url
  src.ifuri_app.gui.IfuriDesktop.discover_peers → src.ifuri_app.network_scan.scan_network
  src.ifuri_app.gui.IfuriDesktop.discover_peers → src.ifuri_app.storage.load_workspace
  src.ifuri_app.gui.IfuriDesktop.discover_peers → src.ifuri_app.flow_engine.as_pretty_json
  src.ifuri_app.gui.IfuriDesktop._novnc_precheck → src.ifuri_app.novnc_demo.demo_dir
  src.ifuri_app.gui.IfuriDesktop._novnc_precheck → src.ifuri_app.novnc_demo.docker_available
  src.ifuri_app.gui.IfuriDesktop._run_compose → src.ifuri_app.novnc_demo.compose_args
  src.ifuri_app.gui.IfuriDesktop.open_novnc_dashboard → src.ifuri_app.novnc_demo.dashboard_url
  src.ifuri_app.gui.IfuriDesktop._apply_node_endpoint → src.ifuri_app.storage.save_workspace
  src.ifuri_app.gui.IfuriDesktop.refresh_log → src.ifuri_app.storage.load_workspace
  src.ifuri_app.gui.IfuriDesktop.save_all → src.ifuri_app.storage.save_workspace
  src.ifuri_app.gui.FirstRunWizard._scan → src.ifuri_app.network_scan.scan_network
  src.ifuri_app.gui.FirstRunWizard._finish → src.ifuri_app.storage.save_workspace
  src.ifuri_app.flow_engine.expand_flow → src.ifuri_app.flow_compile.uri2flow_available
  src.ifuri_app.flow_engine.expand_flow → src.ifuri_app.flow_engine._legacy_expand_flow
  src.ifuri_app.flow_engine.expand_flow → src.ifuri_app.flow_compile.expand_flow_compiled
  src.ifuri_app.flow_engine._legacy_expand_flow → src.ifuri_app.flow_engine.extract_steps
  src.ifuri_app.flow_engine._legacy_expand_flow → src.ifuri_app.flow_engine.flow_id_from_text
  src.ifuri_app.flow_engine.extract_steps → src.ifuri_app.flow_engine.clean_uri
  src.ifuri_app.flow_engine.extract_steps → src.ifuri_app.flow_engine.uri_scheme
  src.ifuri_app.flow_engine.classify_route → src.ifuri_app.flow_engine.uri_scheme
  src.ifuri_app.flow_engine.dry_run_uri → src.ifuri_app.flow_engine.classify_route
  src.ifuri_app.flow_engine.dry_run_flow → src.ifuri_app.flow_engine.expand_flow
  src.ifuri_app.flow_engine.dry_run_flow → src.ifuri_app.flow_engine.dry_run_uri
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**
- assert `status == 200`
- assert `status == 200`
- assert `package == "urirun"`

## Intent

ifURI desktop app — voice UI, urisys-node client, and URI flow runner for urisys-examples.
