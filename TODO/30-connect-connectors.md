# connect.ifuri.com + connectors (repo: if-uri/connect.ifuri.com)

## State
- PHP connector hub. Endpoints: `/` picker, `/connectors/{id}(.json)`, `/connectors.json`,
  `/registry.json`, `/search.json`, `/submit`, `POST /validate-connector`,
  `/install?connectors=…` (shell installer). Schemas in `schema/*.json`, logic in `lib/hub.php`.
- Deploy via `scripts/deploy-plesk.sh` (rsync, no `--delete` → preserves `data/`).

## What a "connector" is
A manifest describing URI routes a third party exposes (DNS, planfile, MCP server, browser,
kvm, llm, …) → bridges into a **urirun binding/registry** the app/flows can call.

## Tasks
- [ ] **Seed real connectors**: planfile, namecheap-dns, mcp-filesystem, browser (noVNC),
  llm (local/qwen), kvm, get-node — as validated manifests in the catalog.
- [ ] **Manifest ↔ urirun bridge**: define connector.schema → `urirun.bindings.v2` mapping
  so `/install?connectors=…` produces a registry the app runs (`ifuri-app urirun-call`).
- [ ] **Validation in CI**: validate every connector manifest against `schema/*.json` (see [50-cicd](50-cicd.md)).
- [ ] **Submit flow**: harden `POST /validate-connector`; rate-limit; spam guard for `/submit`.
- [ ] **Signing/trust**: optional signed manifests + a "verified" badge.
- [ ] **Discovery**: project the catalog to **MCP tools/list** and an **A2A agent card**
  (`registry.json` already machine-readable) so agents can find connectors.
- [ ] **SEO**: confirm `sitemap.php`/`robots.php` output; link from ifuri.com.
- [ ] Cache `data/` catalog; document the `data/` directory (kept on deploy).

## Verify
- connect.ifuri.com/ 200; `/connectors.json`, `/registry.json`, `/search.json` valid JSON;
  `/install?connectors=planfile` returns a runnable script.
