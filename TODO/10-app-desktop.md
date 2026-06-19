# App — ifURI desktop (repo: if-uri/app)

## State
- Python app `ifuri_app` + CLI `ifuri-app` / `ifuri` (`cli.py`).
- Local HTTP runtime (`runtime.py`) + uricore packs (`packages/ifuri-{bridge,chat,page,voice}`).
- urirun is the primary local runtime (urirun-first dispatch; `urirun-info|scan|call|serve`).
- Packaging today: **PyInstaller** binaries via `scripts/build-platform.py` (linux/windows/macos-arm64) → GitHub Release.
- **Tauri scaffold present but unused**: `desktop/src-tauri` (Cargo, `tauri.conf.json`, icons) — not wired into release CI.

## Decision: shell strategy
- **Now:** keep PyInstaller binaries (works, already in CI) as the "app" download.
- **Next:** make **Tauri** the GUI shell that wraps the local HTTP runtime (small binary, native webview, real signing/auto-update). The Python runtime stays the engine.

## Tasks
- [ ] Decide PyInstaller-only vs Tauri-shell (see [00 open decisions](00-roadmap.md)).
- [ ] Tauri: load the app's web UI (`src/ifuri_app/web/`) against the local runtime; bundle/spawn the Python runtime (sidecar) or require `pip install ifuri`.
- [ ] App icons/splash from brand kit (`if-uri/logo` → `png/icon/*`, `ico/favicon.ico`).
- [ ] First-run wizard: `init --scan-lan`, pick/registry urirun, set node endpoint.
- [ ] Node/daemon mode: ship `systemd/` unit + a Windows service / launchd plist.
- [ ] Optional extras packaging: voice (stt/tts), webrtc — keep optional to keep base small.
- [ ] Auto-update channel (Tauri updater or check GitHub Releases API used by ifuri.com).
- [ ] Surface `urirun-serve` from the GUI (start/stop local URI HTTP service).
- [ ] `make build` / `make run` parity with CI `scripts/build-platform.py`.

## Verify
- `ifuri-app --help`; `pytest --ignore=tests/e2e` green (currently 82+).
- Release artifacts land on ifuri.com Download (reads GitHub Releases via `api/releases.php`).
