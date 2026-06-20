# Execution plan — ifURI/urirun TODO

Derived from `TODO/*.md` + recon (2026-06). Status corrected against the real repos.
Repos local: `if-uri/app`, `if-uri/get`, `if-uri/connect.ifuri.com`, `if-uri/ifuri-com`.
`tellmesh/urirun` lives locally as `/home/tom/github/tellmesh/urihandler` and pushes to
`git@github.com:tellmesh/urirun.git`.

Legend: ✅ done · 🟢 safe to do now (code/config) · 🟡 needs decision/clone · 🔴 owner-only (creds/publish/security)

## Recommended order (no risk, no decisions): 30 → 10/50-local → 20

---

## 20 · get-node (`if-uri/get`) — 🟢
Current: `node.sh` and `node.ps1` default to `URIRUN_REF=v0.3.14`; `/health`,
`--dry-run`, `--no-start`, `--upgrade`, `/app` redirect and route printing are in place.
- [x] Pin urirun version with `URIRUN_REF` override; default to released tag `v0.3.14`.
- [x] `--upgrade`: reuse venv, `pip install -U`, recompile, restart running node.
- [x] `--service`: systemd --user (Linux), launchd plist (macOS), Windows Scheduled Task.
- [x] `node.ps1` (PowerShell) exists; keep parity tested when Windows runner is available.
- [x] `/app` redirect → latest desktop release.
- Verify: `bash node.sh --help`, `--dry-run`, post-install `curl 127.0.0.1:8765/health`.
- Verified in Docker full E2E: `pc1` and `pc2` installed from `https://get.ifuri.com/node.sh`
  and exposed 7 URI routes each.
- Verified locally: `make service-smoke` created a temporary systemd --user unit,
  checked `/health`, and removed the unit.

## 30 · connect (`if-uri/connect.ifuri.com`) — 🟢
- [x] CI/local manifest validation: every `data/connectors/*/manifest.json` validates against `schema/*.json`.
- [x] Manifest ↔ urirun bridge: `/install?connectors=…` installs external packages,
  generates bundled bindings, and compiles `connectors.registry.json`.
- [x] MCP/A2A projection: catalog exposes `/mcp.json`, `/a2a.json`, and `/.well-known/agent.json`.
- [ ] Harden `submit.php` / `validate-connector` (rate-limit, spam guard).
- Verify: `/connectors.json`,`/registry.json`,`/search.json` valid JSON; `/install?connectors=planfile` runnable.
- Verified live: deployed to `https://connect.ifuri.com`, public smoke green, clean install generated connector registries on `urirun v0.3.14`.
- Verified in Docker full E2E: available connector install produced 37 registry routes,
  23 executed connector route results, 37 MCP tools and 37 A2A skills.

## 10 + 50 · app + CI (`if-uri/app`) — 🟢 PR-only (no deploy/secrets)
- [x] Node/daemon unit: `systemd/ifuri-runtime-user.service` (+ `com.ifuri.runtime.plist`, NSSM note in `systemd/README.md`) — beside existing voice unit.
- [x] `make build` parity → calls `scripts/build-platform.py` (Makefile `build:` target).
- [x] build-release.yml matrix: macos-13 (x86_64) added; universal2 / optional linux arm64 pending.
- [ ] Post-build/deploy smoke: `curl -fsSI`.
- Verify: `pytest --ignore=tests/e2e` (82+), `ifuri-app --help`.
- Risk: low (matrix runs on tag only).

## 40 · urirun (`tellmesh/urirun`) — 🟢
- Local source is `/home/tom/github/tellmesh/urihandler` with remote `tellmesh/urirun`.
- Consumers now pin `v0.3.14`.
- Remaining: optional PyPI/npm publishing, JS npm package, C release asset, and signed release policy.

## 🔴 Owner-only (not done autonomously)
- Code signing / notarization (Apple Dev ID, Windows cert; `APPLE_*`/`WIN_CERT_*` secrets).
- Publish to PyPI / npm / GHCR (tokens; public release).
- GitHub Actions deploy over SSH (`PLESK_SSH_KEY` secret; security settings).
- Create GitHub Releases / tags (publishing).

## Open decisions (unblock the rest)
1. Desktop shell: PyInstaller now + Tauri later? (Tauri partially wired: `make run-tauri-dev`.)
2. urirun distribution: GitHub-only vs +PyPI+npm.
3. Code-signing budget (Apple $99/yr + Windows cert)? Y/N.
4. Site deploy: manual `make deploy` vs GitHub Actions over SSH.
