# WebRTC — contract (ifURI ↔ uriwebrtc ↔ peer)

Cross-repo contract for duplex voice between two **ifURI** `/voice` instances on LAN.
Node pack: [tellmesh/uriwebrtc](https://github.com/tellmesh/uriwebrtc) · hot-loaded by [urisys-node](https://github.com/tellmesh/urisys-node) `>= 0.1.17`.

## Layers

| Layer | Owner | Role |
|-------|-------|------|
| **Pack** | `uriwebrtc` | `webrtc://` routes — session tracking, HTTP signaling inbox (node-side mock) |
| **Signaling relay** | ifURI runtime | `GET/POST /api/webrtc/signal` — SDP/ICE between browsers (in-memory) |
| **Browser** | `web/webrtc_peer.js` | `RTCPeerConnection`, mic + remote audio, data channel protocol |
| **UI** | `web/voice.js` | Channel type `webrtc-peer`, connect button, voice send/receive |

```text
  ifURI A :8766                              ifURI B :8767
 ┌─────────────────────┐                    ┌─────────────────────┐
 │ /voice UI           │                    │ /voice UI           │
 │ webrtc_peer.js      │◄── HTTP signal ───►│ webrtc_peer.js      │
 │ POST B/api/webrtc/  │    (offer/answer/  │ poll /api/webrtc/   │
 │      signal         │     ice)           │      signal         │
 │ RTCPeerConnection   │◄══ WebRTC P2P ═══►│ RTCPeerConnection   │
 │  ├─ audio (mic)     │    (LAN/STUN)      │  ├─ audio (mic)     │
 │  └─ DataChannel uri │                    │  └─ DataChannel uri │
 └─────────┬───────────┘                    └─────────┬───────────┘
           │ POST /api/voice/run                        │
           ▼                                            ▼
 ┌─────────────────────┐                    ┌─────────────────────┐
 │ urisys-node :8790   │                    │ urisys-node :8790   │
 │ stt/tts/llm (local) │                    │ stt/tts/llm (local) │
 └─────────────────────┘                    └─────────────────────┘
```

## Room identity

Symmetric room id (both peers compute the same value):

```text
webrtc-peer:{min(local_api_url, peer_api_url)}|{max(...)}
```

Example:

```text
webrtc-peer:http://192.168.188.212:8766|http://192.168.188.212:8767
```

**Initiator** (creates offer): peer whose `local_api_url` is lexicographically `<=` remote URL.

`local_api_url` is returned by `GET /api/chat/channels` as `local_api_url` and `GET /api/webrtc/capabilities`.

## ifURI HTTP API (signaling relay)

Not a WebSocket — simple HTTP inbox per room (browser polls local ifURI only; cross-peer posts go to remote base URL).

### POST `/api/webrtc/signal`

Body:

```json
{
  "room": "webrtc-peer:http://a:8766|http://b:8767",
  "from": "http://192.168.188.212:8766",
  "type": "offer",
  "data": { "type": "offer", "sdp": "..." }
}
```

| Field | Required | Values |
|-------|----------|--------|
| `room` | yes | Room id (see above) |
| `from` | yes | Sender ifURI base URL |
| `type` | yes | `offer` \| `answer` \| `ice` |
| `data` | yes | RTCSessionDescription or RTCIceCandidate JSON |

Response: `{ "ok": true, "id": 1, "room": "..." }`

### GET `/api/webrtc/signal?room=&since=`

Poll local inbox. Returns signals with `id > since`.

```json
{
  "ok": true,
  "room": "...",
  "since": 0,
  "next": 3,
  "signals": [
    { "id": 1, "from": "http://...", "type": "offer", "data": { ... }, "at": 1781718000 }
  ]
}
```

### GET `/api/webrtc/capabilities?endpoint=`

```json
{
  "ok": true,
  "endpoint": "http://192.168.188.201:8790",
  "webrtc": true,
  "local_api_url": "http://192.168.188.212:8766",
  "webrtc_pack_hint": { "needed": false }
}
```

## Chat channel: `webrtc-peer`

Discovered via LAN scan (`ifuri_peers`). For each peer (except self), ifURI adds:

```json
{
  "id": "webrtc-peer:http://192.168.188.212:8767",
  "type": "webrtc-peer",
  "kind": "webrtc",
  "title": "desk (WebRTC)",
  "peer_url": "http://192.168.188.212:8767",
  "signaling_room": "webrtc-peer:http://192.168.188.212:8766|http://192.168.188.212:8767",
  "meta": {
    "local_url": "http://192.168.188.212:8766",
    "remote_url": "http://192.168.188.212:8767"
  }
}
```

User flow:

1. Refresh channel list (LAN scan).
2. Select **WebRTC peer** channel.
3. Click **Connect WebRTC** (both sides must connect).
4. Send text or use mic — messages use data channel when connected.

## Data channel protocol (`DataChannel` name: `uri`)

JSON messages on the peer connection (not HTTP).

### Voice command (request)

```json
{
  "kind": "voice",
  "id": "v1781718000-abc123",
  "text": "sprawdź health",
  "dry_run": false
}
```

Receiver runs `POST /api/voice/run` locally (its own `URISYS_NODE_ENDPOINT` / workspace urisys).

### Voice reply

```json
{
  "kind": "voice-reply",
  "id": "v1781718000-abc123",
  "ok": true,
  "text": "Flow completed: lenovo-remote/01-health-probe.uri.flow.yaml",
  "body": { "ok": true, "summary": "...", "plan": { ... } }
}
```

### URI envelope (optional / future)

```json
{
  "kind": "uri",
  "uri": "kvm://local/monitor/primary/query/screenshot",
  "payload": {},
  "context": { "approved": true, "dry_run": true }
}
```

Also supported on node via `webrtc://…/data/command/send` (server-side mock, no P2P).

## Duplex audio

- **Local mic**: `getUserMedia({ audio: true })` → `RTCPeerConnection.addTrack`
- **Remote audio**: `ontrack` → hidden `<audio id="webrtcRemoteAudio" autoplay playsinline>`
- **TTS**: executed on the peer that *receives* the voice command (`speak: true` in `/api/voice/run`), heard locally on that machine (not streamed back over WebRTC in v1)

## `webrtc://` pack (urisys-node)

Install on node:

```bash
make webrtc-install-pack URISYS=http://192.168.188.201:8790
# flow: urisys-examples/lenovo-remote/02c-install-webrtc-pack.uri.flow.yaml
# wheel: uriwebrtc-0.1.0-py3-none-any.whl (or GitHub Releases via pack_resolver)
```

### Routes

| URI | Kind | Operation |
|-----|------|-----------|
| `webrtc://local/session/{session}/command/start` | command | `webrtc.session.start` |
| `webrtc://local/session/{session}/data/command/send` | command | `webrtc.data.send` |
| `webrtc://local/session/{session}/signal/command/post` | command | `webrtc.signal.post` |
| `webrtc://local/session/{session}/signal/query/inbox` | query | `webrtc.signal.inbox` |

### `signal/command/post` payload

```json
{
  "room": "rdp-chat",
  "from": "http://ifuri-peer:8766",
  "type": "offer",
  "data": { "type": "offer", "sdp": "v=0..." }
}
```

### `signal/query/inbox` payload

```json
{ "room": "rdp-chat", "since": 0 }
```

Response: `{ "ok": true, "signals": [...], "since": 0, "next": N }`

Node-side signaling inbox is **in-process mock** (for flows/smoke). Browser P2P uses **ifURI `/api/webrtc/signal`** instead.

## CLI & Makefile

```bash
ifuri-app webrtc-capabilities --endpoint http://192.168.188.201:8790
ifuri-app webrtc-install-pack --endpoint http://192.168.188.201:8790
ifuri-app webrtc-smoke --endpoint http://192.168.188.201:8790

make webrtc-capabilities URISYS=http://192.168.188.201:8790
make webrtc-install-pack URISYS=http://192.168.188.201:8790
make webrtc-smoke URISYS=http://192.168.188.201:8790
```

## Smoke test (two ifURI instances)

```bash
# Terminal 1
URISYS_NODE_ENDPOINT=http://192.168.188.201:8790 ifuri-app voice --port 8766

# Terminal 2 (same LAN)
URISYS_NODE_ENDPOINT=http://192.168.188.201:8790 ifuri-app voice --port 8767

# Both browsers: refresh → WebRTC peer channel → Connect WebRTC → send "health"
```

## Version matrix

| Component | Min version | Notes |
|-----------|-------------|-------|
| ifURI app | 0.2.10 | WebRTC phases 1–3 |
| urisys-node | 0.1.17 | `webrtc` in `pack_resolver` |
| uriwebrtc | 0.1.0 | Standalone wheel |
| uristt | 0.1.0 | Voice packs (separate wheel) |

## See also

- [API.md](API.md) — HTTP routes
- [ARCHITECTURE.md](ARCHITECTURE.md) — system diagram
- [tellmesh/uriwebrtc](https://github.com/tellmesh/uriwebrtc) — pack manifest & handlers
