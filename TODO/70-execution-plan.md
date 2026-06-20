# Execution plan

This is the practical order for executing the roadmap without breaking the
current working path.

## Phase 1 — make the runtime reproducible
- [x] Tag `tellmesh/urirun` after `connector_bindings()` and verify the release
  contains wheel, sdist and `sha256sums.txt`.
- [x] Install from that release wheel in a clean venv and run:
  `urirun --help`, `urirun validate`, `urirun compile`, `urirun run`.
- [x] Update `if-uri/get/node.sh`, app optional dependency and connector packages
  to pin a tag/release instead of `@main`, keeping an override env var.

## Phase 2 — automate the proven E2E path
- [x] Add a manual/nightly workflow for `examples/12-full_e2e_connect_lab`.
- [x] Keep the scenario focused on the user path: get.ifuri.com node install,
  connect.ifuri.com connector install, host/pc1/pc2 flow, MCP tools, A2A skills.
- [x] Move `browser-control` from planned to available after publishing a real
  connector package and Docker smoke environment.
- [ ] Keep `mqtt`, `get-node`, `kvm`, `llm` and `mcp-filesystem` marked as planned
  until each has a real connector package and Docker smoke environment.

## Phase 3 — connector package template
- [x] Turn `urirun-connector-http-check` into the reference template:
  decorator, `connector_bindings()`, manifest, Docker smoke, README, CI.
- [x] Create the next connector from that template: `browser-control`, with
  mock-safe execution, Docker smoke and hub manifest.
- [ ] Create the next connector with a real external dependency and mock-safe
  execution, preferably `mcp-filesystem`.
- [x] Add catalog validation in `connect.ifuri.com` smoke tests before accepting new
  connector manifests.

## Phase 4 — app UX
- [ ] First-run wizard: discover node, choose registry, save endpoint.
- [ ] GUI control for local `urirun-serve`: start, stop, show routes.
- [ ] Decide PyInstaller-only vs Tauri shell after the runtime/install path is
  pinned and CI-covered.

## Explicit non-goals for now
- Do not execute generated `TODO.md` wholesale.
- Do not fix `build/lib/*` lint items; exclude/clean build artifacts instead.
- Do not add signing/notarization until release artifacts and checksums are stable.
