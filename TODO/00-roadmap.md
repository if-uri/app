# ifURI / urirun — roadmap

Cross-repo plan for the ifURI ecosystem. One file per area; check items as done.

## Where we are (done)
- **Sites live on Plesk** with repeatable deploy (`scripts/deploy-plesk.sh` + `make deploy`):
  ifuri.com, examples.ifuri.com, docs.ifuri.com, logo.ifuri.com, get.ifuri.com, connect.ifuri.com.
- **Brand**: unified palette (indigo/emerald/slate) + theme-aware logo; copy buttons on code; PWA, SEO (sitemap/robots), 404, a11y, contact+privacy.
- **urirun**: renamed `tellmesh/urirun`; v1/v2 runtime; integrated into the app
  (`ifuri-app urirun-info|scan|call|serve`, urirun-first dispatch).
- **urirun connector authoring**: `urirun.v2.connector_bindings()` exists, so connector
  packages can expose JSON-serializable bindings from `@urirun.command` decorators.
- **Full E2E lab**: `if-uri/examples/12-full_e2e_connect_lab` verifies get.ifuri.com,
  two urirun nodes, connector install, registry runtime, flow execution, MCP tools
  and A2A skills.
- **App CI**: `ci.yml` (pytest 3.10–3.13 + wheel) and `build-release.yml`
  (PyInstaller binaries for linux/windows/macos-arm64 → GitHub Release).

## What's next (by priority)
- **P0** — finish release pipeline so downloads on ifuri.com are always fresh & trustworthy:
  [50-cicd](50-cicd.md) (sha256 + signing + urirun release wheels), [40-urirun](40-urirun.md).
- **P1** — desktop packaging decision + Tauri shell, node installer parity:
  [10-app-desktop](10-app-desktop.md), [20-get-node](20-get-node.md).
- **P1** — seed the connector hub with real integrations: [30-connect-connectors](30-connect-connectors.md).
- **P2** — broaden reuse / integrations to other platforms: [60-reuse](60-reuse.md).

## Execution order
1. **Make installs reproducible**: tag/release `tellmesh/urirun`, then update
   `get.ifuri.com/node.sh`, app extras and connector dependencies to pin a tag or
   release wheel instead of `@main`.
2. **Automate the proven E2E path**: move the passing full Docker lab into CI as a
   manual/nightly workflow, because it validates the actual user path across repos.
3. **Harden connector distribution**: validate hub manifests in CI, keep the catalog
   generated, and migrate new connector packages to `@urirun.command` +
   `connector_bindings()`.
4. **Then package UX**: first-run wizard, service install, and Tauri shell only after
   the runtime/install path is reproducible.

## Do not execute blindly
- Do not run generated `TODO.md` fixes against `build/lib/*`; those are build
  artifacts and should be cleaned/excluded instead.
- Do not auto-run `prefact -a --execute-todos` across the repo. It mixes low-value
  style noise with real behavior changes.

## Files
- [10-app-desktop.md](10-app-desktop.md) — ifURI desktop app (packaging, Tauri, updates)
- [20-get-node.md](20-get-node.md) — get.ifuri.com node installer
- [30-connect-connectors.md](30-connect-connectors.md) — connect hub + connectors
- [40-urirun.md](40-urirun.md) — urirun packaging & releases
- [50-cicd.md](50-cicd.md) — CI/CD for multiplatform builds + integrations
- [60-reuse.md](60-reuse.md) — where ifURI/urirun can be re-used

## Open decisions (need owner sign-off)
1. Desktop shell: **PyInstaller (now)** vs **Tauri (next)** vs both. → [10](10-app-desktop.md)
2. urirun distribution: GitHub Release wheels only, or also **PyPI + npm**. → [40](40-urirun.md)
3. Code signing budget: Apple Developer ID ($99/yr) + Windows cert (EV/OV). → [50](50-cicd.md)
4. Site deploy: keep manual `make deploy`, or **GitHub Actions over SSH** (secret key). → [50](50-cicd.md)
