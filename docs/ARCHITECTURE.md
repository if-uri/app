# ifURI architecture

ifURI is a **desktop + browser-shell client** for the [urisys](https://github.com/tellmesh/urisys) ecosystem. It does not replace `urisys-node`; it talks to it over HTTP and runs flows from [urisys-examples](https://github.com/tellmesh/urisys-examples).

Repo: [github.com/if-uri/app](https://github.com/if-uri/app) · Site: [ifuri.com](https://ifuri.com)

## Roles on two devices

```text
 Device A (operator)                    Device B (slave / lenovo)
 ┌─────────────────────────┐           ┌─────────────────────────┐
 │ ifuri-app voice :8766   │           │ urisys-node :8790       │
 │  /voice chat UI         │  LAN      │  screen/kvm/him/shell   │
 │  URL state + history    │◄─────────►│  stt:// tts:// voice:// │
 └───────────┬─────────────┘           └───────────┬─────────────┘
             │ POST /uri/call                      │
             ▼                                     ▼
 ┌─────────────────────────┐           ┌─────────────────────────┐
 │ urisys-node (optional)  │           │ app:// chat history *   │
 └─────────────────────────┘           └─────────────────────────┘
  * /app/chat/* on node — fallback ~/.ifuri/app-chat.jsonl locally
```

Each device can be **client** (ifURI) or **host** (urisys-node), or both on one machine.

## Voice & chat pipeline

1. **Browser** — Web Speech API (or manual text) → transcript; URL `prompt=` synced live.
2. **ifURI** — `POST /api/voice/plan` maps phrases to `urisys-examples` flows.
3. **Chat** — each endpoint (node, MCP, A2A, ifURI peer, **WebRTC peer**) is a channel; history from urisys `GET /app/chat/messages` or local JSONL.
4. **Execute** — flow steps → `POST /uri/call` on urisys-node.
5. **Optional TTS** — `tts://…/command/speak` on node.

See [API.md](API.md) for HTTP routes and [WEBRTC.md](WEBRTC.md) for peer duplex voice.

## WebRTC duplex voice (two ifURI instances)

```text
 ifURI A :8766                         ifURI B :8767
┌──────────────────┐                  ┌──────────────────┐
│ /voice           │  HTTP signaling  │ /voice           │
│ webrtc_peer.js   │◄────────────────►│ webrtc_peer.js   │
│ RTCPeerConnection│  WebRTC (audio)  │ RTCPeerConnection│
│ DataChannel uri  │◄════════════════►│ DataChannel uri  │
└────────┬─────────┘                  └────────┬─────────┘
         │ /api/voice/run                       │
         ▼                                      ▼
   urisys-node :8790                      urisys-node :8790
```

- **Pack** on node: [tellmesh/uriwebrtc](https://github.com/tellmesh/uriwebrtc) (`webrtc://` routes, smoke/flows).
- **Signaling** between browsers: ifURI `GET/POST /api/webrtc/signal` (in-memory relay).
- **Voice over P2P**: data channel `voice` / `voice-reply` envelopes — receiver runs local STT/TTS/planner.

Install: `make webrtc-install-pack URISYS=…` · Full contract: [WEBRTC.md](WEBRTC.md).

## Packages (uricore / uri2flow / uricore-js)

| Component | Repo | Role |
|-----------|------|------|
| **uricore** | tellmesh/uricore | Python URI control plane — local handlers in `packages/*/handlers/` |
| **uricore-js** | tellmesh/uricore-js | Browser `page://` — `packages/ifuri-page/` |
| **uri2flow** | tellmesh/uri2flow | Compile compact YAML → workflow graph (used by `/api/flow/expand`) |
| ifURI app | [if-uri/app](https://github.com/if-uri/app) | UI, planning, chat, flow client |
| urisys-node | [tellmesh/urisys-node](https://github.com/tellmesh/urisys-node) | URI server on host |
| uriwebrtc | [tellmesh/uriwebrtc](https://github.com/tellmesh/uriwebrtc) | `webrtc://` pack (signaling mock + envelopes) |
| uristt | [tellmesh/uristt](https://github.com/tellmesh/uristt) | `stt://` / `tts://` on node |
| urisys-examples | [tellmesh/urisys-examples](https://github.com/tellmesh/urisys-examples) | `*.uri.flow.yaml` suites |
| ifuri.com | [if-uri/ifuri-com](https://github.com/if-uri/ifuri-com) | Product site + downloads |

App-specific URI handlers live under [`packages/`](../packages/README.md). Loader: `ifuri_app.packs.loader`.

## External packages (ecosystem)

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `IFURI_HOME` | `~/.ifuri` | Workspace JSON |
| `IFURI_CHAT_STORE` | `~/.ifuri/app-chat.jsonl` | Local chat fallback |
| `URISYS_NODE_ENDPOINT` | `http://127.0.0.1:8790` | Target node |
| `URISYS_EXAMPLES_ROOT` | `../tellmesh/urisys-examples` | Flow YAML root |

## systemd (operator machine)

```bash
mkdir -p ~/.config/ifuri
cp systemd/ifuri-voice.env.example ~/.config/ifuri/voice.env
# edit URISYS_NODE_ENDPOINT
cp systemd/ifuri-voice-user.service ~/.config/systemd/user/ifuri-voice.service
systemctl --user daemon-reload && systemctl --user enable --now ifuri-voice.service
```

urisys-node: see [tellmesh/urisys-node/systemd](https://github.com/tellmesh/urisys-node/tree/main/systemd).

## Chat migration

When lenovo runs urisys-node >= 0.1.15:

```bash
make chat-status URISYS=http://192.168.188.201:8790
make chat-migrate-dry URISYS=http://192.168.188.201:8790
make chat-migrate URISYS=http://192.168.188.201:8790
```

## Development

```bash
make install-dev
make test
make run-voice URISYS=http://192.168.188.201:8790
make run-gui
```

## Roadmap

See [TODO.md](../TODO.md).

- [ ] Deploy `app://` chat routes on production urisys-node builds
- [ ] `llm://` planner instead of keyword triggers
- [x] WebRTC peer channel for duplex voice — see [WEBRTC.md](WEBRTC.md)
- [ ] Tauri/Electron shell wrapping `/voice`
