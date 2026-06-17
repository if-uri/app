# ifURI runtime API

Base URL: `http://127.0.0.1:8766` (configurable via `make run-voice PORT=…`).

Repo: [github.com/if-uri/app](https://github.com/if-uri/app)

## Health & static

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health`, `/api/health` | ifURI + urisys-node health |
| GET | `/`, `/voice` | Browser chat UI |
| GET | `/web/*` | Static assets (`voice.js`, `url_state.js`, …) |

## Chat

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/chat/channels?timeout=1.5&endpoint=` | LAN scan → channel list + history index |
| GET | `/api/chat/history?channel_id=&endpoint=&limit=200` | Thread messages (urisys or local fallback) |
| GET | `/api/chat/status?endpoint=` | Probe urisys `/app/chat/*` availability |
| POST | `/api/chat/migrate` | Body: `{ endpoint?, dry_run?, force? }` — upload local JSONL |
| POST | `/api/chat/send` | Body: `{ channel, text \| prompt, dry_run, router_endpoint }` |

## Voice & urisys

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/voice/catalog?refresh=0` | Flow catalog for voice planner |
| POST | `/api/voice/plan` | `{ text, endpoint?, planner? }` → flow/uri plan |
| POST | `/api/voice/run` | Full voice pipeline |
| POST | `/api/urisys/call` | Proxy to node `POST /uri/call` |
| POST | `/api/urisys/health` | Node health |
| GET | `/api/urisys/screen.png?endpoint=&node_id=&monitor=` | Remote screenshot |
| GET | `/api/urisys/control-test?endpoint=&node_id=` | HIM probe |

## Network & workspace

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/network/scan?timeout=1.5` | Full LAN scan |
| GET | `/api/services`, `/api/flows`, `/api/peers` | Workspace data |
| GET | `/api/packs` | Local URI packs (`packages/`) + `uri2flow` flag |
| POST | `/api/flow/expand` | Body: `{ flow_text }` — compile via uri2flow |
| POST | `/api/flow/validate` | Body: `{ flow_text }` — uri2flow validation |
| POST | `/api/flow/run-file` | Run urisys-examples YAML |

## URL state (`/voice`)

Persistent query parameters (shareable links):

| Param | Example | Meaning |
|-------|---------|---------|
| `lang` | `pl`, `en` | UI language |
| `theme` | `dark`, `light`, `ifuri` | Color theme |
| `view` | `chat`, `screen` | Active panel |
| `channel` | `urisys-node:http://…:8790` | Active chat channel id |
| `prompt` | `health` | Composer text / deep link |
| `action` | `send` | With `prompt` → auto-send on load |
| `dry_run` | `0`, `1` | Dry-run toggle |
| `screen_auto` | `0`, `1` | Auto screenshot refresh |

Example:

```text
http://127.0.0.1:8766/voice?lang=pl&theme=ifuri&channel=urisys-node:http://192.168.188.201:8790&prompt=health&action=send
```

## Data files

| Path | Purpose |
|------|---------|
| `~/.ifuri/workspace.json` | Flows, services, urisys endpoint |
| `~/.ifuri/app-chat.jsonl` | Local chat history (fallback) |

Override: `IFURI_HOME`, `IFURI_CHAT_STORE`

## Smoke test

```bash
make run-voice-bg URISYS=http://192.168.188.201:8790
make api-smoke PORT=8766
make stop
```

See also [ARCHITECTURE.md](ARCHITECTURE.md), [README.md](../README.md).
