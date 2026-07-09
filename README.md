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

### Autonomy (koru + twin-human)

Aplikacja integruje się z **koru** autonomous loop + **urirun-twin-human**:

- Zadania planfile z labelami `kvm`, `lenovo`, `signal-gui` (np. IFURI-226: wysyłka Signal na desktopie lenovo) są automatycznie delegowane do twin-human.
- Realne komendy URI (`kvm://laptop/...`) są wykonywane i logowane.
- Uruchomienie: `urirun start` lub `make koru-cycle`.
- Logi widoczne w dashboardzie "Na żywo — koru (realne komendy URI)".
- Wsparcie dla Digital Twin (osoby + grants + unblock_ledger).

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

### Koru autonomy + twin-human (kvm / lenovo desktop)

```bash
make koru-cycle          # uruchom cykl z apply (używa twin-human dla ticketów kvm/lenovo)
make koru-plan           # dry-run plan pętli
make koru-execute-twin   # bezpośrednie wywołanie twin-human dla IFURI-226 itp.
make koru-logs           # tail .planfile/.koru/queue.log (to co widać w panelu "Na żywo")
make koru-status         # stan koru + otwarte tickety
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

Developer install. `make install-dev` użyje `uv`, jeśli jest dostępny; w trybie
bez `uv` instaluje aplikację editable i opcjonalnie lokalne checkouty
`uri2flow` / `uricore`, jeśli istnieją jako sąsiednie repozytoria developerskie.

```bash
make install-dev
# bez uv, minimalnie:
python -m pip install -e ".[flows,dev,packs]"
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
ifuri-app serve                       # start local runtime HTTP API (no voice UI)
ifuri-app voice --prompt "health"     # voice UI + URL z prompt=
ifuri-app node-health --endpoint http://192.168.188.201:8790
ifuri-app node-call uri://... --endpoint http://192.168.188.201:8790
ifuri-app node-control-test --endpoint http://192.168.188.201:8790
ifuri-app node-screen --endpoint http://192.168.188.201:8790 --out screen.png
ifuri-app flow-run 08-kvm-linkedin.uri.flow.yaml --endpoint http://192.168.188.201:8790
ifuri-app chat-channels
ifuri-app chat-send "status" --endpoint http://192.168.188.201:8790
ifuri-app chat-status --endpoint http://192.168.188.201:8790
ifuri-app chat-migrate --endpoint http://192.168.188.201:8790
ifuri-app packs
ifuri-app run tool://local/report/render --payload '{"format":"html"}' --dry-run
ifuri-app run tool://local/report/render --payload '{"format":"html"}' --execute
ifuri-app expand lenovo-remote/01-health-probe.uri.flow.yaml
ifuri-app urirun-info
ifuri-app urirun-call tool://local/report/render --registry generated/registry.json --payload '{"format":"html"}'
ifuri-app urirun-scan . --out generated/bindings.json
ifuri-app urirun-serve --registry generated/registry.json   # HTTP /health /routes POST /run
ifuri-app urirun-mcp tools --registry generated/registry.json   # tools|card|serve (MCP / A2A)
ifuri-app flow-validate lenovo-remote/01-health-probe.uri.flow.yaml
ifuri-app voice-plan "sprawdź health"
ifuri-app voice-catalog
ifuri-app voice-run "sprawdź health" --dry-run
ifuri-app voice-capabilities --endpoint http://192.168.188.201:8790
ifuri-app voice-install-packs --endpoint http://192.168.188.201:8790
ifuri-app webrtc-capabilities --endpoint http://192.168.188.201:8790
ifuri-app webrtc-install-pack --endpoint http://192.168.188.201:8790
ifuri-app webrtc-smoke --endpoint http://192.168.188.201:8790
ifuri-app discover
```

## Autonomy & Koru (new)

```bash
urirun start                 # start koru autonomous loop (twin-human for kvm/lenovo)
urirun start --apply
```

- Zadania z `labels: kvm,lenovo,signal-gui` (np. wysyłka Signal na desktopie Lenovo) są obsługiwane przez **urirun-twin-human**.
- Rzeczywiste komendy URI (`kvm://laptop/...`) są wykonywane i logowane.
- Panel "Na żywo — koru (realne komendy URI)" pokazuje co naprawdę leci na węzeł.
- Make targets: `koru-cycle`, `koru-plan`, `koru-logs`, `koru-status`.

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

## Related ifURI projects

- Runtime: [if-uri/urirun](https://github.com/if-uri/urirun) (w tym `urirun start`, twin-human, host work/koru)
- Koru autonomy + loop: urirun-connector-loop + urirun-connector-work
- Twin for desktop/KVM: [urirun-twin-human](https://github.com/if-uri/if-uri/tree/main/urirun-twin-human)
- Public docs: [if-uri/docs](https://github.com/if-uri/docs)
- Examples and Docker/noVNC flows: [if-uri/examples](https://github.com/if-uri/examples)
- Connector hub: [connect.ifuri.com](https://connect.ifuri.com)
- Installer: [get.ifuri.com](https://get.ifuri.com)
- Current cross-repository summary:
  [work-summary-2026-06-20](https://github.com/if-uri/docs/blob/main/work-summary-2026-06-20.md)

## License

Licensed under Apache-2.0.
