# get.ifuri.com — node installer (repo: if-uri/get)

## State
- `node.sh`: `curl -fsSL https://get.ifuri.com/node.sh | bash` → installs a urirun node
  (venv in `~/.urirun-node`, pip from `tellmesh/urirun`, runs on `0.0.0.0:8765`).
- Static landing `index.html`; deploy via `scripts/deploy-plesk.sh`.

## Tasks
- [ ] **Pin versions**: default to a released urirun wheel/tag (see [40-urirun](40-urirun.md)) instead of `@main`, with `URIRUN_REF` override — reproducible installs.
- [ ] **Integrity**: publish + check a SHA-256 of `node.sh` (and print "verify with: …"); avoid blind `curl|bash` foot-gun (offer `--dry-run` / download-then-run).
- [ ] **Windows / macOS**: `get.ifuri.com/node.ps1` (PowerShell) and a `brew`/`pipx` path; document each.
- [ ] **Service install**: `--service` flag → systemd (Linux) / launchd (macOS) / NSSM (Windows) so the node survives reboot.
- [ ] **Idempotent upgrade**: `node.sh --upgrade` reuses venv, bumps urirun, restarts.
- [ ] **App shortcut**: `get.ifuri.com/app` → redirect to latest desktop release (GitHub Releases).
- [ ] **Health after install**: hit `/health` and print the node's URI routes + LAN address.
- [ ] No telemetry; print exactly what it installs and where.

## Verify
- `bash node.sh --help`; install on a clean box → `curl 127.0.0.1:8765/health` ok.
- get.ifuri.com/ and /node.sh serve 200 (already live).
