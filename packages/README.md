# ifURI URI packs

App-specific **URI handlers** in the [uricore](https://github.com/tellmesh/uricore) pack convention.
Used by ifURI for local dry-run, browser control, and bridging to `urisys-node`.

## Stack

```text
Compact flow YAML  ──►  uri2flow (compile)  ──►  workflow_graph
Single URI call    ──►  uricore (Py) / uricore-js (JS)  ──►  handler
Execute on host    ──►  urisys-node POST /uri/call
ifURI /voice       ──►  UI + chat + proxy (this repo)
```

| Layer | Repo | Role in ifURI |
|-------|------|----------------|
| **uricore** | tellmesh/uricore | Python control plane — local handlers in `packages/*/handlers/` |
| **uricore-js** | tellmesh/uricore-js | Browser `page://` handlers — `ifuri-page/` |
| **uri2flow** | tellmesh/uri2flow | Replace `flow_engine.py` expand/validate (planned) |
| **urisys-node** | tellmesh/urisys-node | Real execution on lenovo / host |

## Pack layout

Each subdirectory is one capability pack:

```text
packages/
  ifuri-bridge/     app://…/command/urisys_call   → proxy to urisys-node
  ifuri-voice/      voice://…/query/plan          → phrase → flow ref (local)
  ifuri-chat/       app://…/query/messages        → local chat fallback
  ifuri-page/       page://… (JS)                 → DOM / URL state in /voice
```

Python pack:

```text
ifuri-bridge/
  manifest.yaml
  handlers/
    urisys_call.py
```

Handler refs in manifest use `python://handlers.<module>:<fn>` — the loader adds the pack
directory to `sys.path` before registering with uricore.

JavaScript pack (`ifuri-page/`): loaded by `@uricore/js` in `web/voice.js` (integration TBD).

## Loader

```python
from ifuri_app.packs.loader import load_local_registry

registry = load_local_registry()  # requires uricore + pyyaml
```

Install optional deps:

```bash
pip install -e ".[packs]"
```

## Authoring a new pack

1. Create `packages/my-pack/manifest.yaml` (`id`, `scheme`, `uri_patterns`, `handlers.python`).
2. Add `handlers/*.py` with `(payload, context) -> dict` functions.
3. Register routes in tests: `tests/test_packs_loader.py`.
4. For production side effects, prefer urisys-node packs — keep ifURI packs for UI/bridge only.
