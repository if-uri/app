# ifURI App


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.2.1-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.10-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-2.0h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.0956 (1 commits)
- 👤 **Human dev:** ~$200 (2.0h @ $100/h, 30min dedup)

Generated on 2026-06-17 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

Desktop and browser-shell client for **[urisys](https://github.com/tellmesh/urisys)** — voice commands, flow execution, and LAN pairing.

Published at [github.com/if-uri/app](https://github.com/if-uri/app).

## What it does

**ifURI** (`ifuri-app`) lets users:

- speak or type commands in a **browser UI** (`/voice`),
- convert speech → text → **URI flows** from [urisys-examples](https://github.com/tellmesh/urisys-examples),
- execute steps via **urisys-node** on local or remote hosts (`POST /uri/call`),
- use **`stt://`** and **`tts://`** on the node for full voice loop,
- run two instances on **two devices** and forward transcripts peer-to-peer.

The Tkinter desktop app (flow editor) and LAN discovery remain; v0.2 adds the urisys voice path.

## Install

Wheel **nie** nazywa się `ifuri_app-0.1.0` — pakiet PyPI to **`ifuri`**, aktualna wersja **0.2.0**.

```bash
cd ~/github/if-uri/app
python -m pip wheel -w dist .
python -m pip install dist/ifuri-0.2.0-py3-none-any.whl
ifuri-app --version    # → ifuri-app 0.2.0
```

Z kodu (dev):

```bash
python -m pip install -e ".[flows]"
```

Jeśli `ifuri-app: command not found` — ten sam interpreter co `pip`:

```bash
python -m ifuri_app voice
python -m pip show ifuri   # ścieżka do bin/
```

## Quick start

```bash
# On the machine with urisys-node (e.g. lenovo slave)
urisys node serve --host 0.0.0.0 --port 8790

# On operator machine
pip install -e ".[flows]"
export URISYS_EXAMPLES_ROOT=~/github/tellmesh/urisys-examples
export URISYS_NODE_ENDPOINT=http://192.168.188.201:8790

ifuri-app voice --host 0.0.0.0 --port 8765
# → http://localhost:8765/voice
```

## CLI

```bash
ifuri-app app                         # Tkinter desktop (flow editor)
ifuri-app voice                       # HTTP runtime + voice UI
ifuri-app serve --host 0.0.0.0        # runtime API only
ifuri-app node-health                 # urisys-node /health
ifuri-app node-call "kv://local/runtime/query/health"
ifuri-app voice-plan "sprawdź health"
ifuri-app voice-run "otwórz linkedin"
ifuri-app flow-run lenovo-remote/01-health-probe.uri.flow.yaml --dry-run
ifuri-app discover                    # LAN ifURI peers
```

## Voice → flow

| You say (PL/EN) | Flow |
|-----------------|------|
| health, status node | `lenovo-remote/01-health-probe.uri.flow.yaml` |
| linkedin, post, kvm | `lenovo-remote/08-kvm-linkedin.uri.flow.yaml` |
| playwright | `lenovo-remote/07-playwright-linkedin.uri.flow.yaml` |
| other | `voice://command/from-text` on node |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full diagram.

## Runtime API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/voice` | Browser voice UI |
| GET | `/api/health` | ifURI + urisys health |
| POST | `/api/voice/plan` | Text → flow plan |
| POST | `/api/voice/run` | Full voice pipeline |
| POST | `/api/urisys/call` | Proxy to node `/uri/call` |
| POST | `/api/flow/run-file` | Run urisys-examples YAML |

## Install wheel (users)

```bash
python -m pip install ifuri-0.2.0-py3-none-any.whl
ifuri-app voice
```

## Native app (per platform)

Build locally:

```bash
python scripts/build-platform.py    # → dist/ifuri-VERSION-{linux|macos|windows}-ARCH.tar.gz|zip
python -m pip wheel -w dist .       # → dist/ifuri-VERSION-py3-none-any.whl
```

Local CD → GitHub Release:

```bash
./scripts/cd-github.sh              # test + wheel + native app → gh release vVERSION
```

CI builds **linux / windows / macos** on tag `v*` (`.github/workflows/build-release.yml`).

## Data

```text
~/.ifuri/workspace.json
```

Override: `IFURI_HOME=/path/to/dir`

## License

Licensed under Apache-2.0.
