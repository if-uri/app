# connect.ifuri.com + connectors (repo: if-uri/connect.ifuri.com)

## State
- PHP connector hub. Endpoints: `/` picker, `/connectors/{id}(.json)`, `/connectors.json`,
  `/registry.json`, `/search.json`, `/submit`, `POST /validate-connector`,
  `/install?connectors=…` (shell installer). Schemas in `schema/*.json`, logic in `lib/hub.php`.
- Deploy via `scripts/deploy-plesk.sh` (rsync, no `--delete` → preserves `data/`).
- `urirun-connector-http-check` is the reference external connector:
  `@urirun.command` + `urirun.connector_bindings()` + Docker smoke test.
- Full E2E currently verifies available connectors:
  `planfile`, `sqlite-context`, `domain-monitor`, `http-check`, `namecheap-dns`,
  `time-tools`, `browser-control`, `grpc-transport`. Planned/skipped: `mqtt`,
  `get-node`, `kvm`, `llm`, `mcp-filesystem`.

## What a "connector" is
A manifest describing URI routes a third party exposes (DNS, planfile, MCP server, browser,
kvm, llm, …) → bridges into a **urirun binding/registry** the app/flows can call.

## Tasks
- [x] **Seed real connectors**: planfile, namecheap-dns, http-check, time-tools, browser-control, domain-monitor, sqlite-context, grpc-transport (available) + mqtt, mcp-filesystem, llm, kvm, get-node (planned) — 13 validated catalog manifests.
- [x] **Manifest ↔ urirun bridge**: `/install?connectors=…` now imports the installed connector packages, builds `urirun.bindings.v2` via `urirun.connector_bindings()` and compiles a runnable registry (`ifuri-app urirun-call`).
- [x] **Connector package template**: `connect.ifuri.com/scripts/connector-template` + `new-connector.sh` scaffold the `http-check` pattern (`@urirun.command`, `urirun.connector_bindings()`, schema-valid manifest, CLI, README); CI self-checks it.
- [x] **Validation in CI**: `scripts/validate_connectors.py` validates manifests + catalog against `schema/*.json` (see [50-cicd](50-cicd.md)).
- [x] **Submit flow**: `POST /validate-connector` hardened — per-IP rate limit (30/60s), 64 KB body cap, JSON depth cap (32).
- [~] **Signing/trust**: "verified/community" badge live in UI; signed manifests still TODO.
- [x] **Discovery**: catalog projected to MCP tools (`/mcp.json`) + A2A card (`/a2a.json`, `/.well-known/agent.json`) so agents can find connectors.
- [x] **SEO**: sitemap includes /mcp.json + /a2a.json (+ connectors); robots/llms list machine endpoints.
- [ ] Cache `data/` catalog; document the `data/` directory (kept on deploy).

## Verify
- connect.ifuri.com/ 200; `/connectors.json`, `/registry.json`, `/search.json` valid JSON;
  `/install?connectors=planfile` returns a runnable script.
- `urirun-connector-http-check`: `make test && make smoke && make docker-test` ok.
- `urirun-connector-time-tools`: `make test && make smoke && make docker-test` ok.
- `urirun-connector-browser-control`: `python3 -m pytest`, `make smoke`, `make docker-test` ok.
- `examples/12-full_e2e_connect_lab`: `make test` ok with 2 nodes, 14 mesh routes,
  37 installer registry routes, 23 connector route results, 37 MCP tools and
  37 A2A skills.
