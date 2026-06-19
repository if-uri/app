# urirun — packaging & releases (repo: tellmesh/urirun, formerly urihandler)

## State
- Python package `urirun` in `adapters/python/` (v1/v2 runtime, CLI `urirun`/`urirun-v1`/`urirun-v2`).
- JS adapter in `adapters/js/`, C adapter in `adapters/c/`.
- CI: `.github/workflows/ci.yml` → `make test` (py3.12). **No release/publish workflow.**
- Docs say: PyPI optional; install from GitHub; GitHub Release wheels referenced (e.g. v0.3.4) but not auto-built.
- Consumers pin `@main` today (app extra, get/node.sh) — not reproducible.
- `release.yml` now exists and builds wheel + sdist + `sha256sums.txt` on `v*` tags.
- `urirun.v2.connector_bindings()` is available for connector packages that generate
  bindings from decorators.

## Tasks
- [x] **Pinned consumers** to released tag `v0.3.5` (app extra, get/node.sh, connector deps, connect catalog); docs stay `@main` = latest.
- [x] **Release workflow** (`release.yml`): on tag `v*` → build wheel + sdist (`adapters/python`),
  attach to GitHub Release (+ `sha256sums.txt`). This is what `get`/app should pin to.
- [ ] **Version source of truth**: bump `adapters/python/pyproject.toml` (currently 0.3.x) on release;
  keep CHANGELOG.
- [ ] **Optional PyPI**: `twine upload` job behind a `PYPI_TOKEN` secret (decision in [00](00-roadmap.md)).
- [ ] **npm package** for `adapters/js` (`urirun` JS) → publish on tag (decision).
- [ ] **C adapter**: ship `urirun.c/.h` as a release asset for firmware reuse.
- [ ] **`urirun[grpc]`** extra verified in CI (optional deps).
- [ ] Keep v1 (param-binding) and v2 (schema-first) both supported; document migration.
- [ ] Make `make test` green in CI after the v1/v2 rename (local is green).
- [ ] Tag the first post-helper release and update consumers away from `@main`.

## Verify
- Tag → Release contains `urirun-X.Y.Z-py3-none-any.whl` + `*.tar.gz` + `sha256sums.txt`.
- `pip install <release wheel>` works; `urirun --help`, `urirun scan`, `urirun run`.
- Fresh GitHub install of `urirun-connector-http-check` pulls `urirun` and generates
  bindings through `connector_bindings()`.
