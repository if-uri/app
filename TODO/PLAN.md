# Execution plan — ifURI/urirun TODO

Derived from `TODO/*.md` + recon (2026-06). Status corrected against the real repos.
Repos local: `if-uri/app`, `if-uri/get`, `if-uri/connect.ifuri.com`, `if-uri/ifuri-com`.
`tellmesh/urirun` is NOT cloned locally.

Legend: ✅ done · 🟢 safe to do now (code/config) · 🟡 needs decision/clone · 🔴 owner-only (creds/publish/security)

## Recommended order (no risk, no decisions): 30 → 10/50-local → 20

---

## 20 · get-node (`if-uri/get`) — 🟢 (deploy changes get.ifuri.com)
Current: `node.sh` pins `@main`; has `/health`; no `--upgrade`/`--service`/`node.ps1`.
- [ ] Pin urirun version: `URIRUN_REF` override; default to a released tag (blocked by 40 → temporary `main`).
- [ ] `--upgrade`: reuse venv, `pip install -U`, restart runner.
- [ ] `--service`: systemd --user (Linux) / launchd plist (macOS).
- [ ] `node.ps1` (PowerShell) + section in `index.html`.
- [ ] `/app` redirect → latest desktop release.
- Verify: `bash node.sh --help`, `--dry-run`, post-install `curl 127.0.0.1:8765/health`.
- Risk: low (script); deploy via `deploy-plesk.sh` → verify with curl.

## 30 · connect (`if-uri/connect.ifuri.com`) — 🟢 (seed already done: 8 manifests + schemas + ci-deploy.yml)
- [ ] CI manifest validation: `.github/workflows/validate-connectors.yml` — validate every `data/connectors/*/manifest.json` vs `schema/*.json`.
- [ ] Manifest ↔ urirun bridge: `connector.schema` → `urirun.bindings.v2` mapping, used by `install.php?connectors=…`. Files: `lib/hub.php`, `install.php`.
- [ ] MCP/A2A projection: `registry.json` → `tools/list` + A2A card. Files: `lib/hub.php`, `api/`.
- [ ] Harden `submit.php` / `validate-connector` (rate-limit, spam guard).
- Verify: `/connectors.json`,`/registry.json`,`/search.json` valid JSON; `/install?connectors=planfile` runnable.
- Risk: low (additive endpoints + CI).

## 10 + 50 · app + CI (`if-uri/app`) — 🟢 PR-only (no deploy/secrets)
- [ ] Node/daemon unit: `systemd/ifuri-node.service` (+ launchd plist, NSSM note) — beside existing voice unit.
- [ ] `make build`/`run` parity → call `scripts/build-platform.py`.
- [ ] build-release.yml matrix: add macos-13 (x86_64) or universal2, optional linux arm64.
- [ ] Post-build/deploy smoke: `curl -fsSI`.
- Verify: `pytest --ignore=tests/e2e` (82+), `ifuri-app --help`.
- Risk: low (matrix runs on tag only).

## 40 · urirun (`tellmesh/urirun`) — 🟡 blocked
- Not cloned locally. `release.yml` marked done. Remaining: bump `pyproject`, CHANGELOG, `make test` green after v1/v2 rename.
- Blocker: clone repo + decision #2 (PyPI/npm).

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
