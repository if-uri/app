# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
