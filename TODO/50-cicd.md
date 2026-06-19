# CI/CD — multiplatform desktop + integrations

**Answer to "do we generate CI/CD?": yes — and most of it already exists for the app; extend it and add the missing pieces below.**

## Already in place
- **app/.github/workflows/ci.yml** — pytest matrix py3.10–3.13 + wheel.
- **app/.github/workflows/build-release.yml** — wheel + PyInstaller binaries
  (ubuntu-latest, windows-latest, macos-latest=arm64) → `softprops/action-gh-release` with generated notes.
- **urirun/.github/workflows/ci.yml** — `make test`.

## Gaps → tasks
### Desktop app (build-release.yml)
- [x] **Checksums**: emit `sha256` per artifact (ifuri.com Download already renders `item.sha256`) → wire `releases.php`/release to include them.
- [ ] **Coverage of arch**: add macos-x86_64 (or build a **universal2**), optional linux arm64.
- [ ] **Code signing / notarization**: Apple Developer ID + `notarytool`; Windows Authenticode (OV/EV). Secrets: `APPLE_*`, `WIN_CERT_*`.
- [ ] **Tauri job** (if Tauri shell chosen, [10](10-app-desktop.md)): `tauri-apps/tauri-action` matrix → signed installers (.dmg/.msi/.AppImage) + updater manifest.
- [ ] **Release on tag** `v*` only; draft → publish; attach CHANGELOG.

### urirun (new release.yml) — see [40](40-urirun.md)
- [x] Tag → wheel+sdist+sha256 → GitHub Release (release.yml). Optional PyPI/npm pending.

### Connectors (connect.ifuri.com)
- [ ] Validate connector manifests against `schema/*.json` on PR.
- [ ] Build/publish `registry.json` + `search.json` artifacts.

### Site deploys (ifuri-com, examples, docs, logo, get, connect)
- [ ] Optional **GitHub Actions deploy on push to main** running each repo's
  `scripts/deploy-plesk.sh` over SSH (`PLESK_SSH_KEY` secret, host `ifuri@ifuri.com`).
  Keeps `make deploy` for local; adds hands-off publish.
- [ ] Post-deploy smoke: `curl -fsSI https://<sub>.ifuri.com/`.

### Integrations / images
- [ ] Docker images for urirun nodes + workers (publish to GHCR) on tag.
- [ ] (Optional) VS Code extension build, MCP server image — see [60-reuse](60-reuse.md).

## Recommendation
P0: checksums + **urirun release.yml** (so get/app pin a real version) + site auto-deploy.
P1: signing/notarization + Tauri job. P2: Docker/extension images.
