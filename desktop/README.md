# ifURI Voice — Tauri desktop shell (scaffold)

Native window wrapping the `/voice` chat UI served by **ifuri-app** Python runtime.

## Prerequisites

- Rust (`cargo`, `rustc`)
- [Tauri CLI](https://v2.tauri.app/) 2.x (`cargo install tauri-cli`)
- Python ifURI app (`make install-dev` from repo root)

## Development

Terminal 1 (or let Tauri start it automatically):

```bash
cd ~/github/if-uri/app
make run-voice URISYS=http://192.168.188.201:8790 PORT=8766
```

Terminal 2:

```bash
cd ~/github/if-uri/app
make run-tauri-dev URISYS=http://192.168.188.201:8790
```

`make run-tauri-dev` runs `desktop/dev-server.sh` (starts voice server if needed) then `cargo tauri dev`.

The WebView loads `http://127.0.0.1:8766/voice` — full API, WebRTC, and chat features work as in the browser.

## Layout

```text
desktop/
  dev-server.sh      # idempotent voice server for dev
  src-tauri/         # Rust + tauri.conf.json
```

## Production builds (TODO)

Store-ready bundles need a **Python sidecar** (`ifuri-app voice`) or embedded static export plus API — not implemented in this scaffold. See [TODO.md](../TODO.md).

## See also

- [docs/WEBRTC.md](../docs/WEBRTC.md) — WebRTC peer contract
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
