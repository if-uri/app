# ifURI App


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.2.10-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.80-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-3.6h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.8012 (5 commits)
- 👤 **Human dev:** ~$361 (3.6h @ $100/h, 30min dedup)

Generated on 2026-06-17 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

Desktop and browser client for **IFURI** — voice commands, multi-endpoint chat, URI flow execution, LAN pairing and optional **urirun** registry execution.

Published at [github.com/if-uri/app](https://github.com/if-uri/app) · [ifuri.com](https://ifuri.com)

## What it does

**ifURI** (`ifuri-app`) lets users:

- chat with each **urisys-node :8790**, MCP, A2A, LLM, ifURI peer and **WebRTC peer** in **`/voice`**,
- keep **URL state** (`lang`, `theme`, `view`, `channel`, `prompt`) in shareable links,
- store chat history on **urisys-node** (`/app/chat/*`) or locally as fallback,
- run **URI flows** from [urisys-examples](https://github.com/tellmesh/urisys-examples),
- call local or service-backed **urirun** registries through `ifuri-app urirun-call` and `/api/urirun/call`,
- use the **Tkinter desktop** app (flows + LAN + czaty).

## Makefile (recommended)

```bash
cd ~/github/if-uri/app
make help              # lista komend
make install-dev       # editable + pytest
make test              # pytest (unit + API)
make run-voice         # http://127.0.0.1:8766/voice
make run-gui           # desktop Tkinter
make api-smoke         # curl health + chat endpoints
make chat-status URISYS=http://192.168.188.201:8790
make chat-migrate-dry URISYS=http://192.168.188.201:8790   # po upgrade node
make webrtc-install-pack URISYS=http://192.168.188.201:8790
make webrtc-smoke URISYS=http://192.168.188.201:8790
make run ARGS="urirun-info"
```

Zmienne: `PORT=8766`, `URISYS=http://192.168.188.201:8790`, `PYTHON=python3`

Tło:

```bash
make run-voice-bg URISYS=http://192.168.188.201:8790
make health PORT=8766
make stop
```

## Install

Pakiet PyPI: **`ifuri`** (aktualnie **0.2.10**).

Monorepo tellmesh (uri2flow, uricore lokalnie):

```bash
make install-dev   # uv sync --group dev --group tellmesh
# bez uv: pip install -e ".[flows,dev,packs]" && pip install -e ../../tellmesh/{uri2flow,uricore}
```

```bash
cd ~/github/if-uri/app
make install-dev
# lub: python -m pip install -e ".[flows]"
ifuri-app --version
```

Optional urirun runtime:

```bash
python -m pip install -e ".[urirun]"
ifuri-app urirun-info
ifuri-app urirun-call tool://local/report/render \
  --registry generated/registry.json \
  --payload '{"format":"html"}'
```

## Quick start

```bash
# Na maszynie z urisys-node (np. lenovo)
urisys-node serve --host 0.0.0.0 --port 8790

# Operator — browser
export URISYS_NODE_ENDPOINT=http://192.168.188.201:8790
make run-voice URISYS=http://192.168.188.201:8790
# → http://127.0.0.1:8766/voice?lang=pl&theme=dark

# Operator — native shell (Rust + Tauri, dev)
make run-tauri-dev URISYS=http://192.168.188.201:8790
```

## CLI

```bash
ifuri-app app                         # Tkinter desktop
ifuri-app init --scan-lan             # create workspace, discover urisys-node on /24
ifuri-app voice --prompt "health"     # voice UI + URL z prompt=
ifuri-app chat-channels
ifuri-app chat-send "status" --endpoint http://192.168.188.201:8790
ifuri-app chat-status --endpoint http://192.168.188.201:8790
ifuri-app chat-migrate --endpoint http://192.168.188.201:8790
ifuri-app packs
ifuri-app urirun-info
ifuri-app urirun-call tool://local/report/render --registry generated/registry.json --payload '{"format":"html"}'
ifuri-app urirun-scan . --out generated/bindings.json
ifuri-app urirun-serve --registry generated/registry.json   # HTTP /health /routes POST /run
ifuri-app urirun-mcp tools --registry generated/registry.json   # tools|card|serve (MCP / A2A)
ifuri-app flow-validate lenovo-remote/01-health-probe.uri.flow.yaml
ifuri-app voice-plan "sprawdź health"
ifuri-app webrtc-capabilities --endpoint http://192.168.188.201:8790
ifuri-app webrtc-install-pack --endpoint http://192.168.188.201:8790
ifuri-app webrtc-smoke --endpoint http://192.168.188.201:8790
ifuri-app discover
```

## Runtime API

Pełna dokumentacja: **[docs/API.md](docs/API.md)** · diagram: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** · WebRTC: **[docs/WEBRTC.md](docs/WEBRTC.md)**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/voice` | Browser chat UI |
| GET | `/api/health` | ifURI + urisys health |
| GET | `/api/chat/channels` | LAN endpoints as chats |
| GET | `/api/chat/history?channel_id=` | Thread history |
| POST | `/api/chat/send` | Send message (`text` or `prompt`) |
| POST | `/api/voice/run` | Voice pipeline |
| GET | `/api/webrtc/signal` | WebRTC signaling inbox (poll) |
| POST | `/api/webrtc/signal` | WebRTC SDP/ICE relay |
| GET | `/api/urirun` | Optional urirun runtime status |
| POST | `/api/urirun/call` | Call URI through urirun registry |
| POST | `/api/urisys/call` | Proxy to node |

## Data

```text
~/.ifuri/workspace.json      # flows, services, urisys endpoint
~/.ifuri/app-chat.jsonl      # chat fallback (gdy node bez /app/chat)
```

Override: `IFURI_HOME`, `IFURI_CHAT_STORE`

## Backlog

[TODO.md](TODO.md) · [CHANGELOG.md](CHANGELOG.md)

## License

Licensed under Apache-2.0.
