# TODO — ifURI App

## Priorytet

- [x] Wdrożyć urisys-node **>= 0.1.15** na lenovo (`make upgrade-node` — zdalnie shell:// URI, bez SSH)
- [x] Po upgrade node: `make chat-migrate` — `/app/chat/*` OK (0 lokalnych wiadomości do uploadu)
- [x] Packi `stt`/`tts` + `llm` na lenovo
- [x] WebRTC / duplex voice między dwoma instancjami ifURI
  - [x] Faza 1: pack `webrtc` w `pack_resolver` (urisys-node >= 0.1.17)
  - [x] Flow `02c-install-webrtc-pack` + CLI `webrtc-install-pack` / `webrtc-smoke`
  - [x] Faza 2: signaling SDP/ICE między dwoma ifURI
    - [x] `/api/webrtc/signal` + kanały `webrtc-peer` w `/voice`
    - [x] `uriwebrtc` signal/post + signal/inbox na urisys-node
  - [x] Faza 3: duplex voice w `voice.js`
    - [x] Mikrofon + remote `<audio>` przez RTCPeerConnection
    - [x] `voice` / `voice-reply` envelopes na data channel
    - [x] `/api/voice/run` na peerze odbierającym polecenie

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
