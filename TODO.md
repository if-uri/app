# TODO — ifURI App

## Priorytet

- [ ] Wdrożyć urisys-node **>= 0.1.15** na lenovo (SSH obecnie zamknięty — użyj `make upgrade-node` gdy dostępny)
- [ ] Po upgrade node: `make chat-migrate URISYS=http://192.168.188.201:8790`
- [x] Voice planner: regex + catalog + llm:// (zamiast samych keyword triggers)
- [x] Packi `stt`/`tts` na lenovo (voice-capabilities: stt+tts OK; brak tylko `llm`)
- [ ] `llm` pack na lenovo (planner używa regex + catalog offline)
- [ ] WebRTC / duplex voice między dwoma instancjami ifURI

## UI / UX

- [x] Przełącznik widoku chat ↔ screen w `/voice` (przycisk + URL `view=`)
- [x] `@uricore/js` page:// w `/voice` (toggle view via `page_runtime.js`)
- [x] Pełne i18n w `/voice` (PL/EN — `web/i18n.js`)
- [x] E2E Playwright dla `/voice` + URL state (`make test-e2e`)
- [ ] Tauri/Electron shell na `/voice` (store builds)

## Ops

- [x] systemd user unit: `systemd/ifuri-voice-user.service`
- [x] Auto-install packów `stt`/`tts` — banner UI + `POST /api/voice/install-packs`
- [x] Legacy `extract_steps` — deprecation warning bez uri2flow

## Architektura (uricore / uri2flow)

- [x] `packages/` — URI handlery (bridge, voice, chat, page)
- [x] uri2flow — expand/validate flow
- [x] uricore-local runtime — `/api/uri/call`, `/api/packs`
- [ ] Pełne wycofanie legacy `extract_steps` (wymaga uri2flow jako hard dep w dev)

## Zrobione (patrz [CHANGELOG.md](CHANGELOG.md))

- [x] URL state: `lang`, `theme`, `view`, `channel`, `prompt`, `action`
- [x] Historia czatu + fallback lokalny + migracja do urisys (`chat-migrate`)
- [x] Naprawa race condition `workspace.json` (wątki HTTP)
- [x] Naprawa crash API przy `TimeoutError` w skanowaniu LAN
- [x] Makefile, testy API, GUI czaty + link `/voice`
