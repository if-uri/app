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
  `grpc-transport`. Planned/skipped: `mqtt`, `browser-control`.

## What a "connector" is
A manifest describing URI routes a third party exposes (DNS, planfile, MCP server, browser,
kvm, llm, …) → bridges into a **urirun binding/registry** the app/flows can call.

## Tasks
- [ ] **Seed real connectors**: planfile, namecheap-dns, mcp-filesystem, browser (noVNC),
  llm (local/qwen), kvm, get-node — as validated manifests in the catalog.
- [ ] **Manifest ↔ urirun bridge**: define connector.schema → `urirun.bindings.v2` mapping
  so `/install?connectors=…` produces a registry the app runs (`ifuri-app urirun-call`).
- [x] **Connector package template**: `connect.ifuri.com/scripts/connector-template` + `new-connector.sh` scaffold the `http-check` pattern (`@urirun.command`, `urirun.connector_bindings()`, schema-valid manifest, CLI, README); CI self-checks it.
- [x] **Validation in CI**: `scripts/validate_connectors.py` validates manifests + catalog against `schema/*.json` (see [50-cicd](50-cicd.md)).
- [ ] **Submit flow**: harden `POST /validate-connector`; rate-limit; spam guard for `/submit`.
- [ ] **Signing/trust**: optional signed manifests + a "verified" badge.
- [ ] **Discovery**: project the catalog to **MCP tools/list** and an **A2A agent card**
  (`registry.json` already machine-readable) so agents can find connectors.
- [ ] **SEO**: confirm `sitemap.php`/`robots.php` output; link from ifuri.com.
- [ ] Cache `data/` catalog; document the `data/` directory (kept on deploy).

## Verify
- connect.ifuri.com/ 200; `/connectors.json`, `/registry.json`, `/search.json` valid JSON;
  `/install?connectors=planfile` returns a runnable script.
- `urirun-connector-http-check`: `make docker-test` ok.
- `examples/12-full_e2e_connect_lab`: `make test` ok.
