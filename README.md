# ifURI App


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.1-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.15-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-1.0h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.1500 (1 commits)
- 👤 **Human dev:** ~$100 (1.0h @ $100/h, 30min dedup)

Generated on 2026-06-17 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---



Cross-platform Python desktop app and local URI runtime for **ifURI**.

It lets you:

- edit many `uri2flow` / `.uri.flow.yaml` documents inside grouped tasks,
- browse and register services such as `mcp://`, `agent://`, `llm://`, `browser://`, `shell://`, `python://`, `http://`, `workflow://`,
- run safe dry-runs of flows,
- expose your local services through a small HTTP runtime,
- discover other `ifuri://` apps on the local network and route workflow steps to them.

The app uses only Python standard library modules. The desktop UI is built with Tkinter.

## Install from wheel

```bash
python -m pip install ifuri_app-0.1.0-py3-none-any.whl
ifuri-app
```

## Install from source

```bash
python -m pip install -e .
ifuri-app app
```

## CLI

```bash
ifuri-app app                         # open desktop app
ifuri-app init                        # create ~/.ifuri/workspace.json
ifuri-app serve --host 0.0.0.0        # expose local ifURI runtime
ifuri-app discover                    # discover local ifURI nodes
ifuri-app run examples/local_network.uri.flow.yaml --dry-run
```

## Runtime API

When the runtime is started, it exposes:

- `GET /health`
- `GET /api/services`
- `GET /api/flows`
- `GET /api/peers`
- `POST /api/uri/call`
- `POST /api/flow/run`

Example:

```bash
curl -X POST http://localhost:8765/api/uri/call \
  -H 'Content-Type: application/json' \
  -d '{"uri":"mcp://filesystem/list","dry_run":true}'
```

## Data location

By default, workspace data is stored in:

```text
~/.ifuri/workspace.json
```

Override it with:

```bash
IFURI_HOME=/path/to/workspace ifuri-app app
```


## License

Licensed under Apache-2.0.
