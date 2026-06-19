# Where ifURI / urirun can be re-used

The contract is constant — `scheme://target/resource/operation` + JSON-Schema bindings
+ policy gate — and transports are pluggable. That makes it reusable in many places.

## Library / embed (any language)
- **Python / JS / PHP / C** adapters → expose functions, scripts, containers, firmware as URI routes.
- Drop urirun into a project, `urirun scan` → registry, call by stable URI from code or CLI.

## AI / agents
- **MCP server**: `urirun.v2_mcp` projects the registry to `tools/list` + `tools/call` → use from Claude/LLM clients, editors, agent frameworks.
- **A2A agent card**: publish skills so other agents discover & call routes.
- **connect.ifuri.com** catalog → MCP/A2A discovery of third-party connectors.

## Runtimes / transports
- **CLI** in any shell or **CI/CD pipeline step** (run a URI as a build action).
- **HTTP service** (`urirun-serve`, `v2_service`) and **gRPC** (`v2_grpc`) for remote calls.
- **Queue / serverless**: `handler(event) → urirun.run` (MQTT/NATS/Kafka, lambdas).
- **Docker / Compose / k8s**: services addressed by URI; node-per-host via get.ifuri.com.

## Surfaces / products
- **ifURI desktop app**: local control plane for a LAN (devices, browser, kvm, voice, flows).
- **Browser automation**: `browser://` (noVNC) flows.
- **Home automation / IoT / firmware**: C adapter + device mesh (`device://target/...`).
- **Editor extension (VS Code/JetBrains)**: run URIs / browse the registry from the editor.
- **Hosting panels (Plesk/cPanel)**: connectors for DNS, deploy, domains (see connect hub).

## Distribution channels to enable reuse
- [ ] urirun on **PyPI + npm** (pinned installs) — [40-urirun](40-urirun.md).
- [ ] **GHCR Docker images** for nodes/workers.
- [ ] **Connector marketplace** at connect.ifuri.com (submit/validate/sign).
- [ ] Examples gallery (examples.ifuri.com) as copy-paste starting points.
- [ ] One-liner node bootstrap (get.ifuri.com) for any machine on a LAN.

## Highest-leverage next bets
1. **MCP server packaging** — DONE: `ifuri-app urirun-mcp tools|card|serve` (+ `urirun.v2_mcp`).
2. **Connector marketplace** seeded with 5–10 real connectors.
3. **Pinned, signed releases** so third parties trust `pip install` / `curl|bash`.
