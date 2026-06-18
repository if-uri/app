# Changelog

## [Unreleased]

### Added
- Tauri desktop scaffold (`desktop/`, `make run-tauri-dev`) — native WebView for `/voice`

## [0.2.10] - 2026-06-17

### Added
- WebRTC phases 1–3: pack install (`webrtc-install-pack`), HTTP signaling (`/api/webrtc/signal`), `webrtc-peer` channels, duplex voice over data channel
- `webrtc_pipeline.py`, `webrtc_signal.py`, `web/webrtc_peer.js`
- CLI: `webrtc-capabilities`, `webrtc-install-pack`, `webrtc-smoke`
- `node_voice_capabilities.webrtc`

### Changed
- `voice_pipeline` / bootstrap: `uristt-0.1.0`, `uriwebrtc-0.1.0` wheels

### Docs
- [docs/WEBRTC.md](docs/WEBRTC.md) — cross-repo contract
- Update [docs/API.md](docs/API.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [README.md](README.md)

## [0.2.9] - 2026-06-17

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/API.md

### Test
- Update tests/e2e/test_voice_playwright.py
- Update tests/test_api_runtime.py
- Update tests/test_voice_capabilities.py
- Update tests/test_voice_pack_hint.py

### Other
- Update Makefile
- Update VERSION
- Update src/ifuri_app/web/i18n.js
- Update src/ifuri_app/web/index.html
- Update src/ifuri_app/web/voice.css
- Update src/ifuri_app/web/voice.js
- Update uv.lock


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.8] - 2026-06-16

### Added
- `GET /api/voice/capabilities`, `POST /api/voice/install-packs`
- Banner w `/voice` gdy brak stt/tts + przycisk instalacji packów
- CLI: `voice-capabilities`, `voice-install-packs`
- Pełne i18n PL/EN (`web/i18n.js`) + E2E Playwright (`make test-e2e`)
- Deprecation warning dla legacy `expand_flow` bez uri2flow

### Fixed
- CLI `chat-status` / `chat-migrate` — brakujące importy z `chat_channels`
- `make upgrade-node` — fallback zdalny przez `shell://` URI gdy SSH niedostępny
- `voice-install-packs` — fallback `node://…/install-pack` gdy flow 02b nie przejdzie

## [0.2.7] - 2026-06-17

### Docs
- Update README.md

### Other
- Update .goal_test_report.xml
- Update uv.lock

## [0.2.6] - 2026-06-17

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/API.md
- Update docs/ARCHITECTURE.md
- Update packages/README.md

### Test
- Update tests/test_api_runtime.py
- Update tests/test_flow_compile.py
- Update tests/test_ifuri_app.py
- Update tests/test_packs_runtime.py
- Update tests/test_voice_planner.py

### Other
- Update .goal_test_report.xml
- Update Makefile
- Update VERSION
- Update packages/ifuri-page/handlers.js
- Update packages/ifuri-voice/handlers/plan.py
- Update packages/ifuri-voice/manifest.yaml
- Update scripts/vendor-uricore-js.sh
- Update src/ifuri_app/web/index.html
- Update src/ifuri_app/web/page/handlers.js
- Update src/ifuri_app/web/page/manifest.js
- ... and 4 more files

## [0.2.5] - 2026-06-17

### Added
- **Voice planner** (`voice_planner.py`) — łańcuch: regex → catalog → `llm://` → fallback
- Katalog flow z `urisys-examples` (`load_flow_catalog`)
- `GET /api/voice/catalog`, `IFURI_VOICE_PLANNER=auto|regex|catalog|llm`
- CLI: `voice-catalog`, `voice-plan --planner --endpoint`
- `node_voice_capabilities.llm` — wykrywanie packa urillm na node

### Changed
- `voice_pipeline` deleguje planowanie do `voice_planner`
- `/api/voice/plan` używa node + opcjonalnego plannera

## [0.2.4] - 2026-06-17

### Added
- **uri2flow** — `/api/flow/expand`, `/api/flow/validate`, `flow-validate` CLI
- **packages/** — ifuri-bridge, ifuri-voice, ifuri-chat, ifuri-page (uricore + uricore-js)
- `GET /api/packs` — lista packów + status runtime uricore
- `@uricore/js` vendored w `/web` — `page_runtime.js`, `make vendor-uricore-js`
- Lokalny dispatch URI przez uricore (`/api/uri/call` z `dry_run=false` dla packów)
- Wykonanie flow (`/api/flow/run` `dry_run=false`) — lokalne packi → urisys-node
- CLI: `ifuri-app packs`

### Changed
- `flow_runner` / `flow_engine` — uri2flow zamiast duplikatu parsera YAML
- `RuntimeState.call_uri` / `run_flow` — uricore-local z fallbackiem
- `install-dev` — `[flows,packs,dev]`; Makefile: `vendor-uricore-js`

## [0.2.2] - 2026-06-17

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/API.md
- Update docs/ARCHITECTURE.md
- Update packages/README.md

### Test
- Update tests/test_api_runtime.py
- Update tests/test_chat_history.py
- Update tests/test_chat_migrate.py
- Update tests/test_chat_store.py
- Update tests/test_packs_loader.py
- Update tests/test_url_params.py

### Other
- Update .goal_test_report.xml
- Update Makefile
- Update packages/ifuri-bridge/handlers/__init__.py
- Update packages/ifuri-bridge/handlers/urisys_call.py
- Update packages/ifuri-bridge/manifest.yaml
- Update packages/ifuri-chat/handlers/__init__.py
- Update packages/ifuri-chat/handlers/messages.py
- Update packages/ifuri-chat/manifest.yaml
- Update packages/ifuri-page/handlers.js
- Update packages/ifuri-page/manifest.js
- ... and 9 more files

## [0.2.3] - 2026-06-17

### Added
- Przełącznik **Czat / Ekran** w `/voice` (URL `view=chat|screen`)
- `GET /api/chat/status`, `POST /api/chat/migrate` — sprawdzenie i migracja historii do urisys
- CLI: `ifuri-app chat-status`, `ifuri-app chat-migrate`
- systemd: `systemd/ifuri-voice-user.service` + `ifuri-voice.env.example`
- Skrypt `scripts/upgrade-lenovo-node.sh` (urisys-node >= 0.1.15 z `/app/chat/*`)

### Changed
- Makefile: `chat-status`, `chat-migrate`, `upgrade-node`
- docs/API.md, TODO.md

## [0.2.2] - 2026-06-17

### Added
- **Makefile** — `make run-voice`, `run-gui`, `test`, `test-api`, `api-smoke`, `health`, `stop` ([README.md](README.md))
- **TODO.md** — backlog and completed checklist
- **docs/API.md** — runtime HTTP API reference
- Local chat history fallback (`~/.ifuri/app-chat.jsonl`) when urisys-node lacks `/app/chat/*`
- URL query params: `lang`, `theme`, `view`, `channel`, `prompt`, `action`, `dry_run`, `screen_auto`
- `GET /api/chat/history`, chat persistence via urisys or local store
- API smoke tests (`tests/test_api_runtime.py`) including concurrent `/api/health`
- GUI: zakładka Czaty — historia z urisys, URL z `prompt=`, przycisk **Web ↗** i **Otwórz /voice**
- CLI: `voice --prompt`, `chat-send --prompt`

### Fixed
- Race on `workspace.json` save under parallel HTTP requests (thread lock + unique temp files)
- `RuntimeState.load()` no longer writes workspace on every request (only when port changes)
- LAN scan `TimeoutError` no longer crashes HTTP handler (`network_scan.py`)
- HTTP handler returns JSON 500 instead of dropping connection on unhandled errors

### Changed
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — chat API, URL state, Makefile, data paths
- [README.md](README.md) — Makefile quick reference, updated API table, version 0.2.2

## [0.2.1] - 2026-06-17

### Docs
- Update README.md
- Update docs/ARCHITECTURE.md

### Test
- Update tests/test_chat_channels.py
- Update tests/test_gui_smoke.py
- Update tests/test_ifuri_app.py

### Other
- Docker GUI smoke tests, chat channels, network scan

## [0.1.1] - 2026-06-17

### Docs
- Update README.md

### Test
- Update tests/test_ifuri_app.py

### Other
- Initial packaging, examples, discovery
