# TODO — ifURI App

## Priorytet

- [ ] Wdrożyć urisys-node **>= 0.1.15** na lenovo (SSH obecnie zamknięty — użyj `make upgrade-node` gdy dostępny)
- [ ] Po upgrade node: `make chat-migrate URISYS=http://192.168.188.201:8790`
- [ ] `llm://` planner zamiast keyword triggers w voice pipeline
- [ ] WebRTC / duplex voice między dwoma instancjami ifURI

## UI / UX

- [x] Przełącznik widoku chat ↔ screen w `/voice` (przycisk + URL `view=`)
- [ ] Pełne i18n w `/voice` (EN poza placeholderami)
- [ ] Tauri/Electron shell na `/voice` (store builds)

## Ops

- [x] systemd user unit: `systemd/ifuri-voice-user.service`
- [ ] Auto-install packów `stt`/`tts` przy pierwszej sesji voice
- [ ] E2E test Playwright dla `/voice` + URL state

## Zrobione (patrz [CHANGELOG.md](CHANGELOG.md))

- [x] URL state: `lang`, `theme`, `view`, `channel`, `prompt`, `action`
- [x] Historia czatu + fallback lokalny + migracja do urisys (`chat-migrate`)
- [x] Naprawa race condition `workspace.json` (wątki HTTP)
- [x] Naprawa crash API przy `TimeoutError` w skanowaniu LAN
- [x] Makefile, testy API, GUI czaty + link `/voice`
