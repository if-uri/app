# get.ifuri.com — node installer (repo: if-uri/get)

## State
- `node.sh`: `curl -fsSL https://get.ifuri.com/node.sh | bash` → installs a urirun node
  (venv in `~/.urirun-node`, pip from `tellmesh/urirun`, runs on `0.0.0.0:8765`).
- Static landing `index.html`; deploy via `scripts/deploy-plesk.sh`.

## Tasks
- [x] **Pin versions**: default to released urirun tag `v0.3.12` (see [40-urirun](40-urirun.md)) instead of `@main`, with `URIRUN_REF` override — reproducible installs.
- [x] **Integrity**: `node.sh.sha256` published + `sha256sum -c` verify instructions (README); `--no-start`/`--dry-run` to preview before running.
- [ ] **Windows / macOS**: `get.ifuri.com/node.ps1` (PowerShell) and a `brew`/`pipx` path; document each.
- [ ] **Service install**: `--service` flag → systemd (Linux) / launchd (macOS) / NSSM (Windows) so the node survives reboot.
- [ ] **Idempotent upgrade**: `node.sh --upgrade` reuses venv, bumps urirun, restarts.
- [x] **App shortcut**: `get.ifuri.com/app` → 302 to latest desktop release (.htaccess + app/).
- [ ] **Health after install**: hit `/health` and print the node's URI routes + LAN address.
- [ ] No telemetry; print exactly what it installs and where.

## Verify
- `bash node.sh --help`; install on a clean box → `curl 127.0.0.1:8765/health` ok.
- get.ifuri.com/ and /node.sh serve 200 (already live).
