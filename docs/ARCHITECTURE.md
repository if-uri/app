# ifURI architecture

ifURI is a **desktop + browser-shell client** for the [urisys](https://github.com/tellmesh/urisys) ecosystem. It does not replace `urisys-node`; it talks to it over HTTP and runs flows from [urisys-examples](https://github.com/tellmesh/urisys-examples).

Repo: [github.com/if-uri/app](https://github.com/if-uri/app)

## Roles on two devices

```text
 Device A (operator)                    Device B (slave / lenovo)
 ┌─────────────────────────┐           ┌─────────────────────────┐
 │ ifuri-app voice :8765   │           │ ifuri-app voice :8765   │
 │  Web Speech → text      │  LAN      │  Web Speech → text      │
 │  plan → flow            │◄─────────►│  plan → flow            │
 └───────────┬─────────────┘           └───────────┬─────────────┘
             │ POST /uri/call                      │
             ▼                                     ▼
 ┌─────────────────────────┐           ┌─────────────────────────┐
 │ urisys-node :8790       │           │ urisys-node :8790       │
 │ screen/kvm/him/shell/…  │           │ screen/kvm/him/shell/…  │
 │ stt:// tts:// voice://  │           │ stt:// tts:// voice://  │
 └─────────────────────────┘           └─────────────────────────┘
```

Each device can be **client** (ifURI) or **host** (urisys-node), or both on one machine.

## Voice pipeline

1. **Browser** — Web Speech API (or manual text) → transcript.
2. **ifURI** — `POST /api/voice/plan` maps phrases to `urisys-examples` flows (e.g. “linkedin” → `lenovo-remote/08-kvm-linkedin.uri.flow.yaml`).
3. **Optional STT** — `stt://…/query/transcript` on node normalizes text ([uri2voice](https://github.com/tellmesh/uri2voice), [urisys-automation-lab](https://github.com/tellmesh/urisys-automation-lab)).
4. **Execute** — each step of the flow → `POST /uri/call` on urisys-node (same as `lenovo_remote_session.py`).
5. **Optional TTS** — `tts://…/command/speak` reads the summary back.

Fallback when no phrase matches: `voice://command/from-text` on the node (NL → compact flow).

## Packages

| Component | Repo | Role |
|-----------|------|------|
| ifURI app | `if-uri/app` | UI, planning, flow runner client |
| urisys-node | `tellmesh/urisys-node` | URI server on host |
| urisys-examples | `tellmesh/urisys-examples` | `*.uri.flow.yaml` suites |
| uri2voice | `tellmesh/uri2voice` | `stt://`, `tts://`, `voice://` handlers |

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `IFURI_HOME` | `~/.ifuri` | Workspace JSON |
| `URISYS_NODE_ENDPOINT` | `http://127.0.0.1:8790` | Target node |
| `URISYS_EXAMPLES_ROOT` | `../tellmesh/urisys-examples` | Flow YAML root |
| `IFURI_STT_URI` | `stt://local/session/main/query/transcript` | STT route on node |
| `IFURI_TTS_URI` | `tts://local/session/main/command/speak` | TTS route on node |

## Distribution

Build wheel for download:

```bash
python -m pip wheel -w dist .
```

Users install and run:

```bash
pip install ifuri-0.2.0-py3-none-any.whl
ifuri-app voice --host 0.0.0.0 --urisys-endpoint http://192.168.188.201:8790
# open http://localhost:8765/voice
```

## Roadmap

- [ ] Pack `stt`/`tts` on node via `install-pack` at first voice session
- [ ] `llm://` planner instead of keyword triggers
- [ ] WebRTC peer channel for duplex voice between two ifURI instances
- [ ] Tauri/Electron shell wrapping `/voice` for store builds
- [ ] systemd user unit for `ifuri-app voice` + `urisys-node serve`
