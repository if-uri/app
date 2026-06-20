# urirun — packaging & releases (repo: if-uri/urirun, formerly urihandler)

## State
- Python package `urirun` in `adapters/python/` (v1/v2 runtime, CLI `urirun`/`urirun-v1`/`urirun-v2`).
- JS adapter in `adapters/js/`, C adapter in `adapters/c/`.
- CI: `.github/workflows/ci.yml` → `make test` (py3.12).
- Docs say: PyPI optional; install from GitHub or GitHub Release wheels.
- Consumers now pin `v0.3.14` by default (app extra, get/node.sh, connector deps, connect catalog).
- `release.yml` builds wheel + sdist + `sha256sums.txt` on `v*` tags.
- `urirun.v2.connector_bindings()` is available for connector packages that generate
  bindings from decorators.

## Tasks
- [x] **Pinned consumers** to released tag `v0.3.14` (app extra, get/node.sh, connector deps, connect catalog and docs).
- [x] **Release workflow** (`release.yml`): on tag `v*` → build wheel + sdist (`adapters/python`),
  attach to GitHub Release (+ `sha256sums.txt`). This is what `get`/app should pin to.
- [x] **Version source of truth**: bump `adapters/python/pyproject.toml` (currently 0.3.x) on release;
  keep CHANGELOG.
- [ ] **Optional PyPI**: `twine upload` job behind a `PYPI_TOKEN` secret (decision in [00](00-roadmap.md)).
- [ ] **npm package** for `adapters/js` (`urirun` JS) → publish on tag (decision).
- [ ] **C adapter**: ship `urirun.c/.h` as a release asset for firmware reuse.
- [~] **`urirun[grpc]`** runtime dependency verified in Docker E2E through `grpcio`; static `transport://grpc/...` binding still TODO.
- [ ] Keep v1 (param-binding) and v2 (schema-first) both supported; document migration.
- [x] Local package tests are green for the app integration path; CI still needs to run on the remote workflow after push.
- [x] Tag the first post-helper release and update consumers away from `@main`.

## Verify
- Tag `v0.3.14` → GitHub install is the current pinned source.
- `pip install <release wheel>` works; `urirun --help`, `urirun scan`, `urirun run`.
- Fresh GitHub installs of `urirun-connector-http-check`, `urirun-connector-time-tools`
  and `urirun-connector-browser-control` pull `urirun v0.3.14` and generate
  bindings through `connector_bindings()`.
