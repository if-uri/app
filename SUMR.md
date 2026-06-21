# ifURI App

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Dependencies](#dependencies)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `ifuri`
- **version**: `0.2.10`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(2), app.doql.less, goal.yaml, .env.example, docker-compose.gui.yml, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: ifuri;
  version: 0.2.10;
}

dependencies {
  flows: pyyaml>=6.0;
  packs: "uricore>=0.1.8, pyyaml>=6.0";
  urirun: "urirun @ git+https://github.com/if-uri/urirun.git@v0.3.14#subdirectory=adapters/python";
  build: "pyinstaller>=6.0, pyyaml>=6.0";
  dev: "pytest>=8.0, pyyaml>=6.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="ifuri-app"] {
  entry: ifuri_app.cli:main;
}
interface[type="cli"] page[name="ifuri"] {
  entry: ifuri_app.cli:main;
}

interface[type="desktop"] {
  type: tauri;
  framework: tauri;
}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pip install -e .;
}

workflow[name="install-dev"] {
  trigger: manual;
  step-1: run cmd=if command -v uv >/dev/null 2>&1; then \;
  step-2: run cmd=uv sync --group dev --group tellmesh; \;
  step-3: run cmd=else \;
  step-4: run cmd=$(PYTHON) -m pip install -e ".[flows,dev,packs]"; \;
  step-5: run cmd=$(PYTHON) -m pip install -e ../../tellmesh/uri2flow ../../tellmesh/uricore 2>/dev/null || true; \;
  step-6: run cmd=fi;
}

workflow[name="vendor-uricore-js"] {
  trigger: manual;
  step-1: run cmd=bash scripts/vendor-uricore-js.sh;
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m pytest -q --ignore=tests/e2e;
}

workflow[name="test-api"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m pytest tests/test_api_runtime.py -q;
}

workflow[name="test-e2e"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m pytest tests/e2e -q;
}

workflow[name="install-e2e"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pip install pytest-playwright playwright;
  step-2: run cmd=$(PYTHON) -m playwright install chromium;
}

workflow[name="test-gui"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m pytest tests/test_gui_smoke.py -q;
}

workflow[name="test-gui-docker"] {
  trigger: manual;
  step-1: run cmd=bash scripts/test-gui-docker.sh;
}

workflow[name="smoke-novnc"] {
  trigger: manual;
  step-1: run cmd=$(MAKE) -C ../examples/11-novnc_lan_flow up;
  step-2: run cmd=PYTHONPATH=src xvfb-run -a $(PYTHON) scripts/gui_smoke.py --urisys-endpoint $(NODE) --out dist/gui-smoke --timeout 30;
}

workflow[name="run-gui-novnc"] {
  trigger: manual;
  step-1: run cmd=docker compose -f docker/docker-compose.novnc.yml up --build;
  step-2: run cmd=echo "open http://localhost:6080/vnc.html?autoconnect=1&resize=remote";
}

workflow[name="run"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app $(ARGS);
}

workflow[name="run-gui"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app app;
}

workflow[name="run-voice"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app voice \;
  step-2: run cmd=--urisys-endpoint $(URISYS) --port $(PORT) --auto-port;
}

workflow[name="run-voice-bg"] {
  trigger: manual;
  step-1: run cmd=! test -f /tmp/ifuri-voice.pid || { echo "already running (pid $$(cat /tmp/ifuri-voice.pid))"; exit 1; };
  step-2: run cmd=PYTHONPATH=src nohup $(PYTHON) -m ifuri_app voice \;
  step-3: run cmd=--urisys-endpoint $(URISYS) --port $(PORT) --no-auto-port \;
  step-4: run cmd=>/tmp/ifuri-voice.log 2>&1 & echo $$! > /tmp/ifuri-voice.pid;
  step-5: run cmd=sleep 0.8;
  step-6: run cmd=grep -m1 'voice UI:' /tmp/ifuri-voice.log || tail -3 /tmp/ifuri-voice.log;
}

workflow[name="run-tauri-dev"] {
  trigger: manual;
  step-1: run cmd=PORT=$(PORT) URISYS=$(URISYS) PYTHON=$(PYTHON) bash desktop/dev-server.sh;
  step-2: run cmd=cd desktop && cargo tauri dev;
}

workflow[name="stop"] {
  trigger: manual;
  step-1: run cmd=if test -f /tmp/ifuri-voice.pid; then \;
  step-2: run cmd=kill $$(cat /tmp/ifuri-voice.pid) 2>/dev/null || true; \;
  step-3: run cmd=rm -f /tmp/ifuri-voice.pid; \;
  step-4: run cmd=echo "stopped"; \;
  step-5: run cmd=else \;
  step-6: run cmd=echo "no pid file (/tmp/ifuri-voice.pid)"; \;
  step-7: run cmd=fi;
}

workflow[name="health"] {
  trigger: manual;
  step-1: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/api/health" | $(PYTHON) -m json.tool | head -20;
}

workflow[name="api-smoke"] {
  trigger: manual;
  step-1: run cmd=echo "== /voice ==";
  step-2: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/voice" | head -c 120; echo;
  step-3: run cmd=echo "== /api/packs ==";
  step-4: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/api/packs" | $(PYTHON) -m json.tool | head -12;
  step-5: run cmd=echo "== /api/chat/channels ==";
  step-6: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/api/chat/channels?timeout=0.5" | $(PYTHON) -m json.tool | head -15;
  step-7: run cmd=echo "== /api/chat/history ==";
  step-8: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/api/chat/history?channel_id=smoke" | $(PYTHON) -m json.tool | head -10;
}

workflow[name="chat-status"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app chat-status --endpoint $(URISYS);
}

workflow[name="chat-migrate"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app chat-migrate --endpoint $(URISYS);
}

workflow[name="chat-migrate-dry"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app chat-migrate --endpoint $(URISYS) --dry-run;
}

workflow[name="voice-capabilities"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app voice-capabilities --endpoint $(URISYS);
}

workflow[name="voice-install-packs"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app voice-install-packs --endpoint $(URISYS);
}

workflow[name="webrtc-capabilities"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-capabilities --endpoint $(URISYS);
}

workflow[name="webrtc-install-pack"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-install-pack --endpoint $(URISYS);
}

workflow[name="webrtc-smoke"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app webrtc-smoke --endpoint $(URISYS);
}

workflow[name="urirun-info"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=src $(PYTHON) -m ifuri_app urirun-info;
}

workflow[name="upgrade-node"] {
  trigger: manual;
  step-1: run cmd=if ssh -o ConnectTimeout=5 -o BatchMode=yes "$${URISYS_SSH_USER:-tom}@$${URISYS_HOST:-192.168.188.201}" 'echo ok' 2>/dev/null; then \;
  step-2: run cmd=bash scripts/upgrade-lenovo-node.sh; \;
  step-3: run cmd=else \;
  step-4: run cmd=echo "SSH unavailable — upgrading via shell:// URI…"; \;
  step-5: run cmd=$(PYTHON) scripts/upgrade-lenovo-remote.py; \;
  step-6: run cmd=fi;
}

workflow[name="wheel"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pip wheel -w dist .;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) scripts/build-platform.py;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=rm -rf dist/*.whl dist/*.tar.gz dist/*.zip .pytest_cache **/__pycache__;
  step-2: run cmd=find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true;
}

tests {
  import: testql-scenarios/**/*.testql.toon.yaml;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_MAX_RETRIES, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_CREATE_BACKUPS, URI_SERVICE_MAP, IFURI_URIRUN_REGISTRY, IFURI_CONNECT_CATALOG, URISYS_EXAMPLES_ROOT, IFURI_EXAMPLES_ROOT, IFURI_VOICE_PLANNER, URISYS_WEBRTC_WHEEL, URISYS_WHEEL_HOST, IFURI_NOVNC_DEMO_DIR, URISYS_NODE_ENDPOINT, IFURI_HOME, URISYS_STT_WHEEL, IFURI_STT_URI, IFURI_TTS_URI;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  template_file: .env.example;
  python_version: >=3.10;
  vars: LLM_MODEL, OPENROUTER_API_KEY, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
  runtime_llm: OPENROUTER_API_KEY;
  runtime_pfix: PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
}
```

## Workflows

## Dependencies

### Runtime

*(see pyproject.toml)*

### Development

```text markpact:deps python scope=dev
pytest>=8.0
pyyaml>=6.0
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Call Graph

*345 nodes · 491 edges · 39 modules · CC̄=4.1*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `make_handler` *(in src.ifuri_app.runtime)* | 1 | 1 | 453 | **454** |
| `build_parser` *(in src.ifuri_app.cli)* | 1 | 1 | 174 | **175** |
| `run_gui_smoke` *(in scripts.gui_smoke)* | 2 | 1 | 93 | **94** |
| `channels_from_scan` *(in src.ifuri_app.chat_channels)* | 34 ⚠ | 1 | 49 | **50** |
| `serve_http` *(in src.ifuri_app.urirun_bridge)* | 7 | 1 | 46 | **47** |
| `normalize_packages` *(in src.ifuri_app.connect_store)* | 31 ⚠ | 1 | 41 | **42** |
| `run_flow` *(in src.ifuri_app.runtime.RuntimeState)* | 17 ⚠ | 0 | 41 | **41** |
| `scan_network` *(in src.ifuri_app.network_scan)* | 17 ⚠ | 5 | 35 | **40** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/if-uri/app
# generated in 0.15s
# nodes: 345 | edges: 491 | modules: 39
# CC̄=4.1

HUBS[20]:
  src.ifuri_app.runtime.make_handler
    CC=1  in:1  out:453  total:454
  src.ifuri_app.cli.build_parser
    CC=1  in:1  out:174  total:175
  scripts.gui_smoke.run_gui_smoke
    CC=2  in:1  out:93  total:94
  src.ifuri_app.chat_channels.channels_from_scan
    CC=34  in:1  out:49  total:50
  src.ifuri_app.urirun_bridge.serve_http
    CC=7  in:1  out:46  total:47
  src.ifuri_app.connect_store.normalize_packages
    CC=31  in:1  out:41  total:42
  src.ifuri_app.runtime.RuntimeState.run_flow
    CC=17  in:0  out:41  total:41
  src.ifuri_app.network_scan.scan_network
    CC=17  in:5  out:35  total:40
  src.ifuri_app.cli.print_json
    CC=1  in:36  out:2  total:38
  src.ifuri_app.storage.save_workspace
    CC=2  in:22  out:14  total:36
  src.ifuri_app.storage.load_workspace
    CC=3  in:17  out:18  total:35
  src.ifuri_app.chat_channels.send_chat_message
    CC=18  in:1  out:33  total:34
  src.ifuri_app.voice_pipeline.run_voice_command
    CC=23  in:3  out:30  total:33
  src.ifuri_app.discovery.discover
    CC=9  in:2  out:29  total:31
  src.ifuri_app.remote_screen.probe_remote_control
    CC=7  in:4  out:26  total:30
  src.ifuri_app.chat_channels.send_chat_message_routed
    CC=17  in:3  out:25  total:28
  src.ifuri_app.chat_channels.migrate_local_chat_to_urisys
    CC=16  in:2  out:26  total:28
  src.ifuri_app.remote_screen.capture_remote_screen
    CC=11  in:5  out:22  total:27
  src.ifuri_app.flow_compile.expand_flow_compiled
    CC=15  in:1  out:26  total:27
  src.ifuri_app.voice_planner.load_flow_catalog
    CC=13  in:5  out:21  total:26

MODULES:
  packages.ifuri-bridge.handlers.urisys_call  [3 funcs]
    _endpoint  CC=10  out:13
    node_health  CC=2  out:6
    urisys_call  CC=8  out:17
  packages.ifuri-page.handlers  [5 funcs]
    get_url_state  CC=10  out:2
    next  CC=3  out:1
    set_url_state  CC=9  out:2
    toggle_view  CC=9  out:4
    urlState  CC=3  out:0
  packages.ifuri-voice.handlers.plan  [1 funcs]
    plan  CC=11  out:14
  scripts.bootstrap-lenovo-packs  [2 funcs]
    call  CC=2  out:6
    main  CC=5  out:13
  scripts.build-platform  [5 funcs]
    main  CC=2  out:13
    package_artifact  CC=4  out:10
    platform_tag  CC=4  out:4
    read_version  CC=4  out:10
    run_pyinstaller  CC=8  out:23
  scripts.gui_smoke  [3 funcs]
    main  CC=2  out:9
    parse_args  CC=1  out:6
    run_gui_smoke  CC=2  out:93
  src.ifuri_app.chat_channels  [15 funcs]
    _format_json_reply  CC=1  out:1
    _format_voice_reply  CC=16  out:23
    _local_chat_store  CC=1  out:1
    _payload_for_scheme  CC=4  out:0
    _urisys_chat_unavailable  CC=6  out:7
    channels_from_scan  CC=34  out:49
    fetch_chat_channel_index  CC=3  out:8
    fetch_chat_history  CC=9  out:18
    list_chat_channels  CC=2  out:7
    migrate_local_chat_to_urisys  CC=16  out:26
  src.ifuri_app.chat_store  [2 funcs]
    __init__  CC=2  out:3
    chat_store_path  CC=2  out:6
  src.ifuri_app.cli  [34 funcs]
    build_parser  CC=1  out:174
    cmd_app  CC=1  out:1
    cmd_chat_channels  CC=2  out:3
    cmd_chat_migrate  CC=2  out:3
    cmd_chat_send  CC=19  out:18
    cmd_chat_status  CC=1  out:2
    cmd_discover  CC=1  out:2
    cmd_expand  CC=1  out:4
    cmd_flow_run  CC=2  out:3
    cmd_flow_validate  CC=1  out:4
  src.ifuri_app.connect_store  [7 funcs]
    _normalize_install  CC=6  out:7
    catalog_url  CC=2  out:1
    fetch_catalog  CC=6  out:11
    install_command  CC=5  out:4
    local_registry_status  CC=5  out:12
    normalize_packages  CC=31  out:41
    payload_form_fields  CC=8  out:17
  src.ifuri_app.connectors  [5 funcs]
    _detail  CC=5  out:5
    _row  CC=4  out:6
    fetch_node_routes  CC=6  out:11
    normalize_routes  CC=15  out:21
    route_scheme  CC=6  out:5
  src.ifuri_app.discovery  [3 funcs]
    _loop  CC=9  out:16
    discover  CC=9  out:29
    local_descriptor  CC=5  out:12
  src.ifuri_app.flow_compile  [5 funcs]
    _parse_flow_input  CC=12  out:11
    expand_flow_compiled  CC=15  out:26
    flow_steps_from_document  CC=11  out:11
    uri2flow_available  CC=2  out:0
    validate_flow_compiled  CC=3  out:6
  src.ifuri_app.flow_engine  [10 funcs]
    _legacy_expand_flow  CC=4  out:5
    as_pretty_json  CC=1  out:1
    classify_route  CC=6  out:6
    clean_uri  CC=1  out:2
    dry_run_flow  CC=5  out:8
    dry_run_uri  CC=2  out:3
    expand_flow  CC=2  out:3
    extract_steps  CC=3  out:9
    flow_id_from_text  CC=4  out:5
    uri_scheme  CC=2  out:2
  src.ifuri_app.flow_runner  [4 funcs]
    examples_root  CC=4  out:9
    load_flow_steps  CC=3  out:3
    resolve_flow_path  CC=4  out:8
    run_flow_file  CC=9  out:14
  src.ifuri_app.gui  [24 funcs]
    _finish  CC=2  out:3
    _scan  CC=1  out:10
    __init__  CC=1  out:11
    _apply_node_endpoint  CC=4  out:6
    _connector_endpoints  CC=12  out:13
    _novnc_precheck  CC=3  out:4
    _on_package_select  CC=3  out:6
    _render_payload_form  CC=10  out:20
    _run_compose  CC=1  out:11
    _set_app_icon  CC=3  out:5
  src.ifuri_app.gui_chat  [5 funcs]
    _load_chat_history_from_urisys  CC=1  out:17
    _on_chat_channel_select  CC=5  out:12
    _refresh_chat_channels  CC=1  out:9
    _router_endpoint  CC=6  out:8
    _sync_chat_prompt_url  CC=4  out:6
  src.ifuri_app.network_scan  [6 funcs]
    _collect_local_services  CC=8  out:13
    _local_ipv4  CC=2  out:3
    probe_urisys_node  CC=6  out:12
    scan_network  CC=17  out:35
    scan_urisys_nodes  CC=15  out:19
    try_mdns_urisys  CC=2  out:1
  src.ifuri_app.novnc_demo  [7 funcs]
    compose_args  CC=4  out:1
    dashboard_ports  CC=5  out:4
    dashboard_url  CC=4  out:4
    demo_dir  CC=4  out:7
    docker_available  CC=1  out:1
    launch_info  CC=3  out:5
    read_env_file  CC=7  out:10
  src.ifuri_app.packs.loader  [5 funcs]
    _ensure_pack_path  CC=2  out:3
    discover_manifests  CC=3  out:4
    load_local_registry  CC=5  out:8
    pack_summary  CC=6  out:10
    packages_root  CC=1  out:1
  src.ifuri_app.packs.runtime  [3 funcs]
    dispatch_local_uri  CC=5  out:5
    get_local_uri_runtime  CC=2  out:5
    local_runtime_info  CC=3  out:4
  src.ifuri_app.paths  [5 funcs]
    app_package_dir  CC=4  out:7
    assets_dir  CC=1  out:1
    packages_dir  CC=1  out:1
    repo_root  CC=1  out:1
    web_dir  CC=1  out:1
  src.ifuri_app.remote_screen  [4 funcs]
    capture_remote_screen  CC=11  out:22
    probe_remote_control  CC=7  out:26
    screen_uri  CC=2  out:0
    unwrap_result  CC=5  out:4
  src.ifuri_app.runtime  [13 funcs]
    __init__  CC=1  out:4
    call_uri  CC=11  out:25
    health  CC=2  out:17
    load  CC=2  out:4
    run_flow  CC=17  out:41
    _load_urirun_policy  CC=5  out:6
    _port_available  CC=2  out:3
    _port_listeners  CC=4  out:4
    bind_runtime_server  CC=3  out:4
    find_free_port  CC=3  out:4
  src.ifuri_app.sample_data  [1 funcs]
    default_workspace  CC=3  out:4
  src.ifuri_app.storage  [8 funcs]
    add_event  CC=1  out:3
    app_home  CC=2  out:5
    ensure_home  CC=1  out:2
    load_workspace  CC=3  out:18
    normalize_workspace  CC=1  out:16
    now_iso  CC=1  out:2
    save_workspace  CC=2  out:14
    workspace_path  CC=1  out:1
  src.ifuri_app.urirun_bridge  [14 funcs]
    a2a_card  CC=6  out:6
    call_urirun  CC=9  out:7
    default_urirun_registry  CC=5  out:5
    dispatch_local  CC=10  out:7
    list_routes  CC=6  out:6
    load_registry  CC=2  out:4
    mcp_tools  CC=6  out:6
    parse_json_object  CC=5  out:4
    registry_summary  CC=9  out:18
    scan_project  CC=10  out:13
  src.ifuri_app.urisys_client  [5 funcs]
    __init__  CC=2  out:2
    default_node_endpoint  CC=6  out:7
    node_llm_available  CC=5  out:7
    node_voice_capabilities  CC=8  out:12
    node_webrtc_available  CC=5  out:7
  src.ifuri_app.url_params  [2 funcs]
    voice_query  CC=3  out:3
    voice_url  CC=2  out:2
  src.ifuri_app.voice_pipeline  [5 funcs]
    _extract_stt_text  CC=9  out:10
    install_voice_packs  CC=9  out:20
    run_voice_command  CC=23  out:30
    voice_capabilities  CC=2  out:4
    voice_pack_install_hint  CC=3  out:3
  src.ifuri_app.voice_planner  [10 funcs]
    _catalog_tokens  CC=8  out:12
    _flow_plan  CC=2  out:0
    _parse_llm_plan_json  CC=11  out:17
    load_flow_catalog  CC=13  out:21
    node_has_llm  CC=4  out:6
    plan_voice_command  CC=11  out:14
    plan_with_catalog  CC=11  out:15
    plan_with_llm  CC=14  out:19
    plan_with_regex  CC=3  out:2
    voice_planner_mode  CC=2  out:3
  src.ifuri_app.web.i18n  [2 funcs]
    t  CC=4  out:1
    val  CC=1  out:0
  src.ifuri_app.web.page.handlers  [4 funcs]
    get_url_state  CC=10  out:2
    set_url_state  CC=9  out:2
    toggle_view  CC=9  out:4
    urlState  CC=3  out:0
  src.ifuri_app.web.theme  [5 funcs]
    applyLang  CC=2  out:0
    applyTheme  CC=2  out:2
    initFromUrl  CC=2  out:3
    setLang  CC=2  out:2
    setTheme  CC=2  out:2
  src.ifuri_app.web.url_state  [9 funcs]
    base  CC=4  out:2
    cur  CC=4  out:2
    get  CC=2  out:1
    onPopState  CC=1  out:3
    patch  CC=1  out:2
    read  CC=2  out:2
    set  CC=1  out:1
    withParams  CC=9  out:6
    write  CC=8  out:9
  src.ifuri_app.web.voice  [74 funcs]
    I  CC=1  out:0
    SR  CC=4  out:2
    T  CC=1  out:0
    U  CC=1  out:0
    _toggleViewDirect  CC=3  out:4
    api  CC=4  out:3
    appendMessage  CC=7  out:5
    applyPromptFromUrl  CC=4  out:2
    applyUiLanguage  CC=8  out:4
    applyViewFromUrl  CC=7  out:5
  src.ifuri_app.web.webrtc_peer  [22 funcs]
    _applySignal  CC=10  out:5
    _dispatch  CC=8  out:7
    _poll  CC=7  out:5
    _setStatus  CC=2  out:1
    _wireChannel  CC=2  out:3
    answer  CC=1  out:1
    clearTimeout  CC=1  out:1
    isReady  CC=2  out:1
    offer  CC=1  out:1
    payload  CC=8  out:5
  src.ifuri_app.webrtc_pipeline  [4 funcs]
    install_webrtc_pack  CC=8  out:17
    webrtc_capabilities  CC=2  out:3
    webrtc_pack_install_hint  CC=2  out:1
    webrtc_smoke  CC=6  out:14
  src.ifuri_app.webrtc_signal  [4 funcs]
    _purge_room  CC=3  out:4
    local_peer_url  CC=4  out:2
    poll_signals  CC=10  out:9
    post_signal  CC=9  out:12

EDGES:
  packages.ifuri-page.handlers.get_url_state → packages.ifuri-page.handlers.urlState
  packages.ifuri-page.handlers.set_url_state → packages.ifuri-page.handlers.urlState
  packages.ifuri-page.handlers.toggle_view → packages.ifuri-page.handlers.urlState
  src.ifuri_app.url_params.voice_url → src.ifuri_app.url_params.voice_query
  src.ifuri_app.connect_store.normalize_packages → src.ifuri_app.connect_store._normalize_install
  src.ifuri_app.connect_store.fetch_catalog → src.ifuri_app.connect_store.catalog_url
  src.ifuri_app.connect_store.fetch_catalog → src.ifuri_app.connect_store.normalize_packages
  src.ifuri_app.connect_store.local_registry_status → src.ifuri_app.urirun_bridge.urirun_info
  src.ifuri_app.connect_store.local_registry_status → src.ifuri_app.urirun_bridge.default_urirun_registry
  src.ifuri_app.connect_store.local_registry_status → src.ifuri_app.urirun_bridge.registry_summary
  src.ifuri_app.connect_store.payload_form_fields → src.ifuri_app.web.url_state.set
  packages.ifuri-bridge.handlers.urisys_call.urisys_call → packages.ifuri-bridge.handlers.urisys_call._endpoint
  packages.ifuri-bridge.handlers.urisys_call.node_health → packages.ifuri-bridge.handlers.urisys_call._endpoint
  src.ifuri_app.paths.web_dir → src.ifuri_app.paths.app_package_dir
  src.ifuri_app.paths.assets_dir → src.ifuri_app.paths.app_package_dir
  src.ifuri_app.paths.repo_root → src.ifuri_app.paths.app_package_dir
  src.ifuri_app.paths.packages_dir → src.ifuri_app.paths.repo_root
  src.ifuri_app.webrtc_signal.local_peer_url → src.ifuri_app.network_scan._local_ipv4
  src.ifuri_app.webrtc_signal.post_signal → src.ifuri_app.webrtc_signal._purge_room
  src.ifuri_app.webrtc_signal.poll_signals → src.ifuri_app.webrtc_signal._purge_room
  src.ifuri_app.flow_compile.expand_flow_compiled → src.ifuri_app.flow_compile._parse_flow_input
  src.ifuri_app.flow_compile.expand_flow_compiled → src.ifuri_app.flow_compile.uri2flow_available
  src.ifuri_app.flow_compile.flow_steps_from_document → src.ifuri_app.flow_compile.uri2flow_available
  src.ifuri_app.flow_compile.flow_steps_from_document → src.ifuri_app.flow_compile._parse_flow_input
  src.ifuri_app.flow_compile.flow_steps_from_document → src.ifuri_app.flow_engine.extract_steps
  src.ifuri_app.flow_compile.validate_flow_compiled → src.ifuri_app.flow_compile._parse_flow_input
  src.ifuri_app.flow_compile.validate_flow_compiled → src.ifuri_app.flow_compile.uri2flow_available
  packages.ifuri-voice.handlers.plan.plan → src.ifuri_app.voice_planner.plan_voice_command
  src.ifuri_app.flow_engine.expand_flow → src.ifuri_app.flow_compile.uri2flow_available
  src.ifuri_app.flow_engine.expand_flow → src.ifuri_app.flow_engine._legacy_expand_flow
  src.ifuri_app.flow_engine.expand_flow → src.ifuri_app.flow_compile.expand_flow_compiled
  src.ifuri_app.flow_engine._legacy_expand_flow → src.ifuri_app.flow_engine.extract_steps
  src.ifuri_app.flow_engine._legacy_expand_flow → src.ifuri_app.flow_engine.flow_id_from_text
  src.ifuri_app.flow_engine.extract_steps → src.ifuri_app.flow_engine.clean_uri
  src.ifuri_app.flow_engine.extract_steps → src.ifuri_app.flow_engine.uri_scheme
  src.ifuri_app.flow_engine.classify_route → src.ifuri_app.flow_engine.uri_scheme
  src.ifuri_app.flow_engine.dry_run_uri → src.ifuri_app.flow_engine.classify_route
  src.ifuri_app.flow_engine.dry_run_flow → src.ifuri_app.flow_engine.expand_flow
  src.ifuri_app.flow_engine.dry_run_flow → src.ifuri_app.flow_engine.dry_run_uri
  src.ifuri_app.webrtc_pipeline.webrtc_capabilities → src.ifuri_app.urisys_client.node_webrtc_available
  src.ifuri_app.webrtc_pipeline.webrtc_capabilities → src.ifuri_app.webrtc_pipeline.webrtc_pack_install_hint
  src.ifuri_app.webrtc_pipeline.install_webrtc_pack → src.ifuri_app.webrtc_pipeline.webrtc_pack_install_hint
  src.ifuri_app.webrtc_pipeline.install_webrtc_pack → src.ifuri_app.flow_runner.run_flow_file
  src.ifuri_app.webrtc_pipeline.install_webrtc_pack → src.ifuri_app.urisys_client.node_webrtc_available
  src.ifuri_app.webrtc_pipeline.webrtc_smoke → src.ifuri_app.urisys_client.node_webrtc_available
  src.ifuri_app.webrtc_pipeline.webrtc_pack_install_hint → src.ifuri_app.urisys_client.node_webrtc_available
  src.ifuri_app.chat_store.chat_store_path → src.ifuri_app.storage.app_home
  src.ifuri_app.chat_store.LocalChatStore.__init__ → src.ifuri_app.storage.ensure_home
  src.ifuri_app.chat_store.LocalChatStore.__init__ → src.ifuri_app.chat_store.chat_store_path
  src.ifuri_app.urisys_client.default_node_endpoint → src.ifuri_app.storage.load_workspace
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**
- assert `status == 200`
- assert `status == 200`
- assert `package == "urirun"`

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/if-uri/app
# generated in 0.15s
# nodes: 345 | edges: 491 | modules: 39
# CC̄=4.1

HUBS[20]:
  src.ifuri_app.runtime.make_handler
    CC=1  in:1  out:453  total:454
  src.ifuri_app.cli.build_parser
    CC=1  in:1  out:174  total:175
  scripts.gui_smoke.run_gui_smoke
    CC=2  in:1  out:93  total:94
  src.ifuri_app.chat_channels.channels_from_scan
    CC=34  in:1  out:49  total:50
  src.ifuri_app.urirun_bridge.serve_http
    CC=7  in:1  out:46  total:47
  src.ifuri_app.connect_store.normalize_packages
    CC=31  in:1  out:41  total:42
  src.ifuri_app.runtime.RuntimeState.run_flow
    CC=17  in:0  out:41  total:41
  src.ifuri_app.network_scan.scan_network
    CC=17  in:5  out:35  total:40
  src.ifuri_app.cli.print_json
    CC=1  in:36  out:2  total:38
  src.ifuri_app.storage.save_workspace
    CC=2  in:22  out:14  total:36
  src.ifuri_app.storage.load_workspace
    CC=3  in:17  out:18  total:35
  src.ifuri_app.chat_channels.send_chat_message
    CC=18  in:1  out:33  total:34
  src.ifuri_app.voice_pipeline.run_voice_command
    CC=23  in:3  out:30  total:33
  src.ifuri_app.discovery.discover
    CC=9  in:2  out:29  total:31
  src.ifuri_app.remote_screen.probe_remote_control
    CC=7  in:4  out:26  total:30
  src.ifuri_app.chat_channels.send_chat_message_routed
    CC=17  in:3  out:25  total:28
  src.ifuri_app.chat_channels.migrate_local_chat_to_urisys
    CC=16  in:2  out:26  total:28
  src.ifuri_app.remote_screen.capture_remote_screen
    CC=11  in:5  out:22  total:27
  src.ifuri_app.flow_compile.expand_flow_compiled
    CC=15  in:1  out:26  total:27
  src.ifuri_app.voice_planner.load_flow_catalog
    CC=13  in:5  out:21  total:26

MODULES:
  packages.ifuri-bridge.handlers.urisys_call  [3 funcs]
    _endpoint  CC=10  out:13
    node_health  CC=2  out:6
    urisys_call  CC=8  out:17
  packages.ifuri-page.handlers  [5 funcs]
    get_url_state  CC=10  out:2
    next  CC=3  out:1
    set_url_state  CC=9  out:2
    toggle_view  CC=9  out:4
    urlState  CC=3  out:0
  packages.ifuri-voice.handlers.plan  [1 funcs]
    plan  CC=11  out:14
  scripts.bootstrap-lenovo-packs  [2 funcs]
    call  CC=2  out:6
    main  CC=5  out:13
  scripts.build-platform  [5 funcs]
    main  CC=2  out:13
    package_artifact  CC=4  out:10
    platform_tag  CC=4  out:4
    read_version  CC=4  out:10
    run_pyinstaller  CC=8  out:23
  scripts.gui_smoke  [3 funcs]
    main  CC=2  out:9
    parse_args  CC=1  out:6
    run_gui_smoke  CC=2  out:93
  src.ifuri_app.chat_channels  [15 funcs]
    _format_json_reply  CC=1  out:1
    _format_voice_reply  CC=16  out:23
    _local_chat_store  CC=1  out:1
    _payload_for_scheme  CC=4  out:0
    _urisys_chat_unavailable  CC=6  out:7
    channels_from_scan  CC=34  out:49
    fetch_chat_channel_index  CC=3  out:8
    fetch_chat_history  CC=9  out:18
    list_chat_channels  CC=2  out:7
    migrate_local_chat_to_urisys  CC=16  out:26
  src.ifuri_app.chat_store  [2 funcs]
    __init__  CC=2  out:3
    chat_store_path  CC=2  out:6
  src.ifuri_app.cli  [34 funcs]
    build_parser  CC=1  out:174
    cmd_app  CC=1  out:1
    cmd_chat_channels  CC=2  out:3
    cmd_chat_migrate  CC=2  out:3
    cmd_chat_send  CC=19  out:18
    cmd_chat_status  CC=1  out:2
    cmd_discover  CC=1  out:2
    cmd_expand  CC=1  out:4
    cmd_flow_run  CC=2  out:3
    cmd_flow_validate  CC=1  out:4
  src.ifuri_app.connect_store  [7 funcs]
    _normalize_install  CC=6  out:7
    catalog_url  CC=2  out:1
    fetch_catalog  CC=6  out:11
    install_command  CC=5  out:4
    local_registry_status  CC=5  out:12
    normalize_packages  CC=31  out:41
    payload_form_fields  CC=8  out:17
  src.ifuri_app.connectors  [5 funcs]
    _detail  CC=5  out:5
    _row  CC=4  out:6
    fetch_node_routes  CC=6  out:11
    normalize_routes  CC=15  out:21
    route_scheme  CC=6  out:5
  src.ifuri_app.discovery  [3 funcs]
    _loop  CC=9  out:16
    discover  CC=9  out:29
    local_descriptor  CC=5  out:12
  src.ifuri_app.flow_compile  [5 funcs]
    _parse_flow_input  CC=12  out:11
    expand_flow_compiled  CC=15  out:26
    flow_steps_from_document  CC=11  out:11
    uri2flow_available  CC=2  out:0
    validate_flow_compiled  CC=3  out:6
  src.ifuri_app.flow_engine  [10 funcs]
    _legacy_expand_flow  CC=4  out:5
    as_pretty_json  CC=1  out:1
    classify_route  CC=6  out:6
    clean_uri  CC=1  out:2
    dry_run_flow  CC=5  out:8
    dry_run_uri  CC=2  out:3
    expand_flow  CC=2  out:3
    extract_steps  CC=3  out:9
    flow_id_from_text  CC=4  out:5
    uri_scheme  CC=2  out:2
  src.ifuri_app.flow_runner  [4 funcs]
    examples_root  CC=4  out:9
    load_flow_steps  CC=3  out:3
    resolve_flow_path  CC=4  out:8
    run_flow_file  CC=9  out:14
  src.ifuri_app.gui  [24 funcs]
    _finish  CC=2  out:3
    _scan  CC=1  out:10
    __init__  CC=1  out:11
    _apply_node_endpoint  CC=4  out:6
    _connector_endpoints  CC=12  out:13
    _novnc_precheck  CC=3  out:4
    _on_package_select  CC=3  out:6
    _render_payload_form  CC=10  out:20
    _run_compose  CC=1  out:11
    _set_app_icon  CC=3  out:5
  src.ifuri_app.gui_chat  [5 funcs]
    _load_chat_history_from_urisys  CC=1  out:17
    _on_chat_channel_select  CC=5  out:12
    _refresh_chat_channels  CC=1  out:9
    _router_endpoint  CC=6  out:8
    _sync_chat_prompt_url  CC=4  out:6
  src.ifuri_app.network_scan  [6 funcs]
    _collect_local_services  CC=8  out:13
    _local_ipv4  CC=2  out:3
    probe_urisys_node  CC=6  out:12
    scan_network  CC=17  out:35
    scan_urisys_nodes  CC=15  out:19
    try_mdns_urisys  CC=2  out:1
  src.ifuri_app.novnc_demo  [7 funcs]
    compose_args  CC=4  out:1
    dashboard_ports  CC=5  out:4
    dashboard_url  CC=4  out:4
    demo_dir  CC=4  out:7
    docker_available  CC=1  out:1
    launch_info  CC=3  out:5
    read_env_file  CC=7  out:10
  src.ifuri_app.packs.loader  [5 funcs]
    _ensure_pack_path  CC=2  out:3
    discover_manifests  CC=3  out:4
    load_local_registry  CC=5  out:8
    pack_summary  CC=6  out:10
    packages_root  CC=1  out:1
  src.ifuri_app.packs.runtime  [3 funcs]
    dispatch_local_uri  CC=5  out:5
    get_local_uri_runtime  CC=2  out:5
    local_runtime_info  CC=3  out:4
  src.ifuri_app.paths  [5 funcs]
    app_package_dir  CC=4  out:7
    assets_dir  CC=1  out:1
    packages_dir  CC=1  out:1
    repo_root  CC=1  out:1
    web_dir  CC=1  out:1
  src.ifuri_app.remote_screen  [4 funcs]
    capture_remote_screen  CC=11  out:22
    probe_remote_control  CC=7  out:26
    screen_uri  CC=2  out:0
    unwrap_result  CC=5  out:4
  src.ifuri_app.runtime  [13 funcs]
    __init__  CC=1  out:4
    call_uri  CC=11  out:25
    health  CC=2  out:17
    load  CC=2  out:4
    run_flow  CC=17  out:41
    _load_urirun_policy  CC=5  out:6
    _port_available  CC=2  out:3
    _port_listeners  CC=4  out:4
    bind_runtime_server  CC=3  out:4
    find_free_port  CC=3  out:4
  src.ifuri_app.sample_data  [1 funcs]
    default_workspace  CC=3  out:4
  src.ifuri_app.storage  [8 funcs]
    add_event  CC=1  out:3
    app_home  CC=2  out:5
    ensure_home  CC=1  out:2
    load_workspace  CC=3  out:18
    normalize_workspace  CC=1  out:16
    now_iso  CC=1  out:2
    save_workspace  CC=2  out:14
    workspace_path  CC=1  out:1
  src.ifuri_app.urirun_bridge  [14 funcs]
    a2a_card  CC=6  out:6
    call_urirun  CC=9  out:7
    default_urirun_registry  CC=5  out:5
    dispatch_local  CC=10  out:7
    list_routes  CC=6  out:6
    load_registry  CC=2  out:4
    mcp_tools  CC=6  out:6
    parse_json_object  CC=5  out:4
    registry_summary  CC=9  out:18
    scan_project  CC=10  out:13
  src.ifuri_app.urisys_client  [5 funcs]
    __init__  CC=2  out:2
    default_node_endpoint  CC=6  out:7
    node_llm_available  CC=5  out:7
    node_voice_capabilities  CC=8  out:12
    node_webrtc_available  CC=5  out:7
  src.ifuri_app.url_params  [2 funcs]
    voice_query  CC=3  out:3
    voice_url  CC=2  out:2
  src.ifuri_app.voice_pipeline  [5 funcs]
    _extract_stt_text  CC=9  out:10
    install_voice_packs  CC=9  out:20
    run_voice_command  CC=23  out:30
    voice_capabilities  CC=2  out:4
    voice_pack_install_hint  CC=3  out:3
  src.ifuri_app.voice_planner  [10 funcs]
    _catalog_tokens  CC=8  out:12
    _flow_plan  CC=2  out:0
    _parse_llm_plan_json  CC=11  out:17
    load_flow_catalog  CC=13  out:21
    node_has_llm  CC=4  out:6
    plan_voice_command  CC=11  out:14
    plan_with_catalog  CC=11  out:15
    plan_with_llm  CC=14  out:19
    plan_with_regex  CC=3  out:2
    voice_planner_mode  CC=2  out:3
  src.ifuri_app.web.i18n  [2 funcs]
    t  CC=4  out:1
    val  CC=1  out:0
  src.ifuri_app.web.page.handlers  [4 funcs]
    get_url_state  CC=10  out:2
    set_url_state  CC=9  out:2
    toggle_view  CC=9  out:4
    urlState  CC=3  out:0
  src.ifuri_app.web.theme  [5 funcs]
    applyLang  CC=2  out:0
    applyTheme  CC=2  out:2
    initFromUrl  CC=2  out:3
    setLang  CC=2  out:2
    setTheme  CC=2  out:2
  src.ifuri_app.web.url_state  [9 funcs]
    base  CC=4  out:2
    cur  CC=4  out:2
    get  CC=2  out:1
    onPopState  CC=1  out:3
    patch  CC=1  out:2
    read  CC=2  out:2
    set  CC=1  out:1
    withParams  CC=9  out:6
    write  CC=8  out:9
  src.ifuri_app.web.voice  [74 funcs]
    I  CC=1  out:0
    SR  CC=4  out:2
    T  CC=1  out:0
    U  CC=1  out:0
    _toggleViewDirect  CC=3  out:4
    api  CC=4  out:3
    appendMessage  CC=7  out:5
    applyPromptFromUrl  CC=4  out:2
    applyUiLanguage  CC=8  out:4
    applyViewFromUrl  CC=7  out:5
  src.ifuri_app.web.webrtc_peer  [22 funcs]
    _applySignal  CC=10  out:5
    _dispatch  CC=8  out:7
    _poll  CC=7  out:5
    _setStatus  CC=2  out:1
    _wireChannel  CC=2  out:3
    answer  CC=1  out:1
    clearTimeout  CC=1  out:1
    isReady  CC=2  out:1
    offer  CC=1  out:1
    payload  CC=8  out:5
  src.ifuri_app.webrtc_pipeline  [4 funcs]
    install_webrtc_pack  CC=8  out:17
    webrtc_capabilities  CC=2  out:3
    webrtc_pack_install_hint  CC=2  out:1
    webrtc_smoke  CC=6  out:14
  src.ifuri_app.webrtc_signal  [4 funcs]
    _purge_room  CC=3  out:4
    local_peer_url  CC=4  out:2
    poll_signals  CC=10  out:9
    post_signal  CC=9  out:12

EDGES:
  packages.ifuri-page.handlers.get_url_state → packages.ifuri-page.handlers.urlState
  packages.ifuri-page.handlers.set_url_state → packages.ifuri-page.handlers.urlState
  packages.ifuri-page.handlers.toggle_view → packages.ifuri-page.handlers.urlState
  src.ifuri_app.url_params.voice_url → src.ifuri_app.url_params.voice_query
  src.ifuri_app.connect_store.normalize_packages → src.ifuri_app.connect_store._normalize_install
  src.ifuri_app.connect_store.fetch_catalog → src.ifuri_app.connect_store.catalog_url
  src.ifuri_app.connect_store.fetch_catalog → src.ifuri_app.connect_store.normalize_packages
  src.ifuri_app.connect_store.local_registry_status → src.ifuri_app.urirun_bridge.urirun_info
  src.ifuri_app.connect_store.local_registry_status → src.ifuri_app.urirun_bridge.default_urirun_registry
  src.ifuri_app.connect_store.local_registry_status → src.ifuri_app.urirun_bridge.registry_summary
  src.ifuri_app.connect_store.payload_form_fields → src.ifuri_app.web.url_state.set
  packages.ifuri-bridge.handlers.urisys_call.urisys_call → packages.ifuri-bridge.handlers.urisys_call._endpoint
  packages.ifuri-bridge.handlers.urisys_call.node_health → packages.ifuri-bridge.handlers.urisys_call._endpoint
  src.ifuri_app.paths.web_dir → src.ifuri_app.paths.app_package_dir
  src.ifuri_app.paths.assets_dir → src.ifuri_app.paths.app_package_dir
  src.ifuri_app.paths.repo_root → src.ifuri_app.paths.app_package_dir
  src.ifuri_app.paths.packages_dir → src.ifuri_app.paths.repo_root
  src.ifuri_app.webrtc_signal.local_peer_url → src.ifuri_app.network_scan._local_ipv4
  src.ifuri_app.webrtc_signal.post_signal → src.ifuri_app.webrtc_signal._purge_room
  src.ifuri_app.webrtc_signal.poll_signals → src.ifuri_app.webrtc_signal._purge_room
  src.ifuri_app.flow_compile.expand_flow_compiled → src.ifuri_app.flow_compile._parse_flow_input
  src.ifuri_app.flow_compile.expand_flow_compiled → src.ifuri_app.flow_compile.uri2flow_available
  src.ifuri_app.flow_compile.flow_steps_from_document → src.ifuri_app.flow_compile.uri2flow_available
  src.ifuri_app.flow_compile.flow_steps_from_document → src.ifuri_app.flow_compile._parse_flow_input
  src.ifuri_app.flow_compile.flow_steps_from_document → src.ifuri_app.flow_engine.extract_steps
  src.ifuri_app.flow_compile.validate_flow_compiled → src.ifuri_app.flow_compile._parse_flow_input
  src.ifuri_app.flow_compile.validate_flow_compiled → src.ifuri_app.flow_compile.uri2flow_available
  packages.ifuri-voice.handlers.plan.plan → src.ifuri_app.voice_planner.plan_voice_command
  src.ifuri_app.flow_engine.expand_flow → src.ifuri_app.flow_compile.uri2flow_available
  src.ifuri_app.flow_engine.expand_flow → src.ifuri_app.flow_engine._legacy_expand_flow
  src.ifuri_app.flow_engine.expand_flow → src.ifuri_app.flow_compile.expand_flow_compiled
  src.ifuri_app.flow_engine._legacy_expand_flow → src.ifuri_app.flow_engine.extract_steps
  src.ifuri_app.flow_engine._legacy_expand_flow → src.ifuri_app.flow_engine.flow_id_from_text
  src.ifuri_app.flow_engine.extract_steps → src.ifuri_app.flow_engine.clean_uri
  src.ifuri_app.flow_engine.extract_steps → src.ifuri_app.flow_engine.uri_scheme
  src.ifuri_app.flow_engine.classify_route → src.ifuri_app.flow_engine.uri_scheme
  src.ifuri_app.flow_engine.dry_run_uri → src.ifuri_app.flow_engine.classify_route
  src.ifuri_app.flow_engine.dry_run_flow → src.ifuri_app.flow_engine.expand_flow
  src.ifuri_app.flow_engine.dry_run_flow → src.ifuri_app.flow_engine.dry_run_uri
  src.ifuri_app.webrtc_pipeline.webrtc_capabilities → src.ifuri_app.urisys_client.node_webrtc_available
  src.ifuri_app.webrtc_pipeline.webrtc_capabilities → src.ifuri_app.webrtc_pipeline.webrtc_pack_install_hint
  src.ifuri_app.webrtc_pipeline.install_webrtc_pack → src.ifuri_app.webrtc_pipeline.webrtc_pack_install_hint
  src.ifuri_app.webrtc_pipeline.install_webrtc_pack → src.ifuri_app.flow_runner.run_flow_file
  src.ifuri_app.webrtc_pipeline.install_webrtc_pack → src.ifuri_app.urisys_client.node_webrtc_available
  src.ifuri_app.webrtc_pipeline.webrtc_smoke → src.ifuri_app.urisys_client.node_webrtc_available
  src.ifuri_app.webrtc_pipeline.webrtc_pack_install_hint → src.ifuri_app.urisys_client.node_webrtc_available
  src.ifuri_app.chat_store.chat_store_path → src.ifuri_app.storage.app_home
  src.ifuri_app.chat_store.LocalChatStore.__init__ → src.ifuri_app.storage.ensure_home
  src.ifuri_app.chat_store.LocalChatStore.__init__ → src.ifuri_app.chat_store.chat_store_path
  src.ifuri_app.urisys_client.default_node_endpoint → src.ifuri_app.storage.load_workspace
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 86f 13762L | python:41,shell:11,yaml:10,javascript:10,json:5,rust:3,toml:2,yml:2,gui-novnc:1 | 2026-06-21
# generated in 0.02s
# CC̅=4.1 | critical:18/512 | dups:0 | cycles:0

HEALTH[19]:
  🔴 GOD   src/ifuri_app/runtime.py = 811L, 4 classes, 16m, max CC=17
  🟡 CC    normalize_packages CC=31 (limit:15)
  🟡 CC    expand_flow_compiled CC=15 (limit:15)
  🟡 CC    scan_urisys_nodes CC=15 (limit:15)
  🟡 CC    scan_network CC=17 (limit:15)
  🟡 CC    normalize_routes CC=15 (limit:15)
  🟡 CC    cmd_chat_send CC=19 (limit:15)
  🟡 CC    _apply_chat_channels CC=16 (limit:15)
  🟡 CC    run_voice_command CC=23 (limit:15)
  🟡 CC    channels_from_scan CC=34 (limit:15)
  🟡 CC    migrate_local_chat_to_urisys CC=16 (limit:15)
  🟡 CC    send_chat_message CC=18 (limit:15)
  🟡 CC    send_chat_message_routed CC=17 (limit:15)
  🟡 CC    _format_voice_reply CC=16 (limit:15)
  🟡 CC    renderChannelList CC=21 (limit:15)
  🟡 CC    handleWebRtcEnvelope CC=17 (limit:15)
  🟡 CC    connectWebRtc CC=15 (limit:15)
  🟡 CC    run_flow CC=17 (limit:15)
  🟡 CC    _refresh_network_views CC=15 (limit:15)

REFACTOR[2]:
  1. split src/ifuri_app/runtime.py  (god module)
  2. split 18 high-CC methods  (CC>15)

PIPELINES[236]:
  [1] Src [get_url_state]: get_url_state → urlState
      PURITY: 100% pure
  [2] Src [state]: state
      PURITY: 100% pure
  [3] Src [set_url_state]: set_url_state → urlState
      PURITY: 100% pure
  [4] Src [toggle_view]: toggle_view → urlState
      PURITY: 100% pure
  [5] Src [current]: current
      PURITY: 100% pure
  [6] Src [merge_voice_url]: merge_voice_url
      PURITY: 100% pure
  [7] Src [urisys_call]: urisys_call → _endpoint
      PURITY: 100% pure
  [8] Src [node_health]: node_health → _endpoint
      PURITY: 100% pure
  [9] Src [web_dir]: web_dir → app_package_dir
      PURITY: 100% pure
  [10] Src [packages_dir]: packages_dir → repo_root → app_package_dir
      PURITY: 100% pure
  [11] Src [is_webrtc_initiator]: is_webrtc_initiator
      PURITY: 100% pure
  [12] Src [room_stats]: room_stats
      PURITY: 100% pure
  [13] Src [plan]: plan → plan_voice_command → load_flow_catalog → examples_root
      PURITY: 100% pure
  [14] Src [list_messages]: list_messages
      PURITY: 100% pure
  [15] Src [list_channels]: list_channels
      PURITY: 100% pure
  [16] Src [__init__]: __init__ → ensure_home → app_home
      PURITY: 100% pure
  [17] Src [append]: append
      PURITY: 100% pure
  [18] Src [list_messages]: list_messages
      PURITY: 100% pure
  [19] Src [list_channels]: list_channels
      PURITY: 100% pure
  [20] Src [__init__]: __init__ → default_node_endpoint → load_workspace → ensure_home → ...(1 more)
      PURITY: 100% pure
  [21] Src [health]: health
      PURITY: 100% pure
  [22] Src [call_uri]: call_uri
      PURITY: 100% pure
  [23] Src [app_chat_messages]: app_chat_messages
      PURITY: 100% pure
  [24] Src [app_chat_channels]: app_chat_channels
      PURITY: 100% pure
  [25] Src [app_chat_append]: app_chat_append
      PURITY: 100% pure
  [26] Src [_get]: _get
      PURITY: 100% pure
  [27] Src [_post]: _post
      PURITY: 100% pure
  [28] Src [registry]: registry
      PURITY: 100% pure
  [29] Src [runtime]: runtime
      PURITY: 100% pure
  [30] Src [t]: t → val
      PURITY: 100% pure
  [31] Src [initFromUrl]: initFromUrl → applyTheme
      PURITY: 100% pure
  [32] Src [setTheme]: setTheme → applyTheme
      PURITY: 100% pure
  [33] Src [setLang]: setLang → applyLang
      PURITY: 100% pure
  [34] Src [cmd_init]: cmd_init → load_workspace → ensure_home → app_home
      PURITY: 100% pure
  [35] Src [cmd_serve]: cmd_serve → load_workspace → ensure_home → app_home
      PURITY: 100% pure
  [36] Src [cmd_discover]: cmd_discover → discover → load_workspace → ensure_home → ...(1 more)
      PURITY: 100% pure
  [37] Src [cmd_voice]: cmd_voice → load_workspace → ensure_home → app_home
      PURITY: 100% pure
  [38] Src [cmd_node_health]: cmd_node_health → print_json
      PURITY: 100% pure
  [39] Src [cmd_node_call]: cmd_node_call → print_json
      PURITY: 100% pure
  [40] Src [cmd_node_control_test]: cmd_node_control_test → probe_remote_control → set → patch → ...(2 more)
      PURITY: 100% pure
  [41] Src [cmd_node_screen]: cmd_node_screen → capture_remote_screen → screen_uri
      PURITY: 100% pure
  [42] Src [cmd_flow_run]: cmd_flow_run → print_json
      PURITY: 100% pure
  [43] Src [cmd_voice_plan]: cmd_voice_plan → print_json
      PURITY: 100% pure
  [44] Src [cmd_voice_catalog]: cmd_voice_catalog → print_json
      PURITY: 100% pure
  [45] Src [cmd_voice_capabilities]: cmd_voice_capabilities → print_json
      PURITY: 100% pure
  [46] Src [cmd_voice_install_packs]: cmd_voice_install_packs → install_voice_packs → voice_pack_install_hint → node_voice_capabilities → ...(1 more)
      PURITY: 100% pure
  [47] Src [cmd_webrtc_capabilities]: cmd_webrtc_capabilities → print_json
      PURITY: 100% pure
  [48] Src [cmd_webrtc_install_pack]: cmd_webrtc_install_pack → install_webrtc_pack → webrtc_pack_install_hint → node_webrtc_available
      PURITY: 100% pure
  [49] Src [cmd_webrtc_smoke]: cmd_webrtc_smoke → webrtc_smoke → node_webrtc_available
      PURITY: 100% pure
  [50] Src [cmd_voice_run]: cmd_voice_run → run_voice_command → plan_voice_command → load_flow_catalog → ...(1 more)
      PURITY: 100% pure

LAYERS:
  packages/                       CC̄=5.4    ←in:0  →out:0
  │ urisys_call                 62L  0C    3m  CC=10     ←0
  │ handlers.js                 54L  0C   10m  CC=10     ←3
  │ manifest.js                 38L  0C    0m  CC=0.0    ←0
  │ messages                    32L  0C    2m  CC=4      ←0
  │ plan                        26L  0C    1m  CC=11     ←0
  │ manifest.yaml               26L  0C    0m  CC=0.0    ←0
  │ manifest.yaml               26L  0C    0m  CC=0.0    ←0
  │ manifest.yaml               17L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │
  src/                            CC̄=4.1    ←in:0  →out:0
  │ !! gui                       1005L  2C   67m  CC=15     ←1
  │ !! runtime                    811L  4C   16m  CC=17     ←2
  │ !! cli                        675L  0C   34m  CC=19     ←0
  │ !! voice.js                   641L  0C  118m  CC=21     ←0
  │ !! chat_channels              531L  0C   17m  CC=34     ←3
  │ urirun_bridge              415L  0C   14m  CC=10     ←3
  │ !! gui_chat                   292L  1C   15m  CC=16     ←0
  │ voice_planner              289L  0C   11m  CC=14     ←5
  │ webrtc_peer.js             232L  1C   25m  CC=14     ←0
  │ !! network_scan               228L  0C    9m  CC=17     ←5
  │ !! connect_store              211L  0C   10m  CC=31     ←1
  │ !! voice_pipeline             197L  0C    6m  CC=23     ←3
  │ urisys_client              158L  1C   12m  CC=8      ←3
  │ !! flow_compile               154L  1C    6m  CC=15     ←4
  │ webrtc_pipeline            131L  0C    4m  CC=8      ←2
  │ flow_engine                129L  0C   10m  CC=6      ←6
  │ discovery                  126L  1C    6m  CC=9      ←2
  │ !! connectors                 121L  0C    6m  CC=15     ←1
  │ novnc_demo                 121L  0C    7m  CC=7      ←1
  │ remote_screen              116L  0C    4m  CC=11     ←3
  │ i18n.js                    114L  0C    4m  CC=4      ←0
  │ webrtc_signal              106L  0C    7m  CC=10     ←2
  │ storage                     97L  0C    8m  CC=3      ←11
  │ chat_store                  90L  1C    5m  CC=9      ←0
  │ flow_runner                 90L  0C    4m  CC=9      ←5
  │ sample_data                 79L  0C    1m  CC=3      ←1
  │ loader                      77L  0C    5m  CC=6      ←3
  │ url_state.js                70L  0C   15m  CC=9      ←7
  │ runtime                     62L  0C    3m  CC=5      ←2
  │ handlers.js                 54L  0C   10m  CC=10     ←0
  │ url_params                  43L  0C    3m  CC=5      ←3
  │ theme.js                    42L  0C    8m  CC=2      ←0
  │ manifest.js                 38L  0C    0m  CC=0.0    ←0
  │ paths                       36L  0C    5m  CC=4      ←2
  │ page_runtime.js             23L  0C    2m  CC=1      ←0
  │ __init__                    16L  0C    0m  CC=0.0    ←0
  │ __init__                     9L  0C    0m  CC=0.0    ←0
  │ __main__                     7L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=3.1    ←in:0  →out:6
  │ gui_smoke                  222L  0C    4m  CC=5      ←0
  │ build-platform             148L  0C    6m  CC=8      ←0
  │ bootstrap-lenovo-packs      60L  0C    2m  CC=5      ←0
  │ upgrade-lenovo-node.sh      58L  0C    1m  CC=0.0    ←0
  │ cd-github.sh                55L  0C    0m  CC=0.0    ←0
  │ test-gui-docker.sh          50L  0C    0m  CC=0.0    ←0
  │ upgrade-lenovo-remote       37L  0C    1m  CC=2      ←0
  │ vendor-uricore-js.sh        23L  0C    0m  CC=0.0    ←0
  │ ifuri_app_entry              9L  0C    0m  CC=0.0    ←0
  │ run-ifuri-app.sh             6L  0C    0m  CC=0.0    ←0
  │
  desktop/                        CC̄=1.5    ←in:0  →out:0
  │ !! desktop-schema.json       2310L  0C    0m  CC=0.0    ←0
  │ dev-server.sh               41L  0C    1m  CC=0.0    ←0
  │ tauri.conf.json             39L  0C    0m  CC=0.0    ←0
  │ Cargo.toml                  25L  0C    0m  CC=0.0    ←0
  │ lib.rs                      19L  0C    1m  CC=4      ←0
  │ default.json                11L  0C    0m  CC=0.0    ←0
  │ main.rs                      9L  0C    1m  CC=1      ←0
  │ build.rs                     6L  0C    1m  CC=1      ←0
  │ acl-manifests.json           1L  0C    0m  CC=0.0    ←0
  │ capabilities.json            1L  0C    0m  CC=0.0    ←0
  │
  docker/                         CC̄=0.0    ←in:0  →out:0
  │ entrypoint-gui-test.sh      67L  0C    1m  CC=0.0    ←0
  │ docker-compose.gui.yml      44L  0C    0m  CC=0.0    ←0
  │ install-gui-deps.sh         42L  0C    0m  CC=0.0    ←0
  │ entrypoint-gui-novnc.sh     39L  0C    0m  CC=0.0    ←0
  │ Dockerfile.gui-novnc        37L  0C    0m  CC=0.0    ←0
  │ docker-compose.novnc.yml    25L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  527L  0C    0m  CC=0.0    ←0
  │ Makefile                   184L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             117L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                99L  0C    0m  CC=0.0    ←0
  │ project.sh                  66L  0C    0m  CC=0.0    ←0
  │ nlp2uri.yaml                 8L  0C    0m  CC=0.0    ←0
  │ tree.sh                      4L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=0.0    ←in:0  →out:0
  │ local_network.uri.flow.yaml    13L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    92L  0C    0m  CC=0.0    ←0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                               src.ifuri_app   packages.ifuri-page               scripts  packages.ifuri-voice
         src.ifuri_app                    ──                     6                    ←6                    ←1  hub
   packages.ifuri-page                    ←6                    ──                                              hub
               scripts                     6                                          ──                      
  packages.ifuri-voice                     1                                                                ──
  CYCLES: none
  HUB: packages.ifuri-page/ (fan-in=6)
  HUB: src.ifuri_app/ (fan-in=7)

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 7 groups | 41f 7030L | 2026-06-21

SUMMARY:
  files_scanned: 41
  total_lines:   7030
  dup_groups:    7
  dup_fragments: 14
  saved_lines:   50
  scan_ms:       2321

HOTSPOTS[5] (files with most duplication):
  src/ifuri_app/cli.py  dup=44L  groups=4  frags=8  (0.6%)
  src/ifuri_app/urirun_bridge.py  dup=30L  groups=1  frags=2  (0.4%)
  src/ifuri_app/urisys_client.py  dup=14L  groups=1  frags=2  (0.2%)
  src/ifuri_app/flow_compile.py  dup=4L  groups=1  frags=1  (0.1%)
  src/ifuri_app/flow_engine.py  dup=4L  groups=1  frags=1  (0.1%)

DUPLICATES[7] (ranked by impact):
  [71b0c91d36991313]   STRU  list_routes  L=17 N=2 saved=17 sim=1.00
      src/ifuri_app/urirun_bridge.py:216-232  (list_routes)
      src/ifuri_app/urirun_bridge.py:366-378  (mcp_tools)
  [0de8715c258857c0]   STRU  cmd_flow_run  L=10 N=2 saved=10 sim=1.00
      src/ifuri_app/cli.py:205-214  (cmd_flow_run)
      src/ifuri_app/cli.py:217-226  (cmd_voice_plan)
  [befabce1a989deb4]   STRU  node_llm_available  L=7 N=2 saved=7 sim=1.00
      src/ifuri_app/urisys_client.py:39-45  (node_llm_available)
      src/ifuri_app/urisys_client.py:48-54  (node_webrtc_available)
  [47d5a29ae4df3970]   STRU  cmd_voice_install_packs  L=5 N=2 saved=5 sim=1.00
      src/ifuri_app/cli.py:242-246  (cmd_voice_install_packs)
      src/ifuri_app/cli.py:255-259  (cmd_webrtc_install_pack)
  [bc6e3b103bbf2be5]   STRU  cmd_voice_capabilities  L=4 N=2 saved=4 sim=1.00
      src/ifuri_app/cli.py:236-239  (cmd_voice_capabilities)
      src/ifuri_app/cli.py:249-252  (cmd_webrtc_capabilities)
  [4626c3d55952124f]   STRU  _scheme  L=4 N=2 saved=4 sim=1.00
      src/ifuri_app/flow_compile.py:151-154  (_scheme)
      src/ifuri_app/flow_engine.py:60-63  (uri_scheme)
  [81b8d023ddbd7602]   EXAC  _stop  L=3 N=2 saved=3 sim=1.00
      src/ifuri_app/cli.py:108-110  (_stop)
      src/ifuri_app/cli.py:149-151  (_stop)

REFACTOR[7] (ranked by priority):
  [1] ○ extract_function   → src/ifuri_app/utils/list_routes.py
      WHY: 2 occurrences of 17-line block across 1 files — saves 17 lines
      FILES: src/ifuri_app/urirun_bridge.py
  [2] ○ extract_function   → src/ifuri_app/utils/cmd_flow_run.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: src/ifuri_app/cli.py
  [3] ○ extract_function   → src/ifuri_app/utils/node_llm_available.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: src/ifuri_app/urisys_client.py
  [4] ○ extract_function   → src/ifuri_app/utils/cmd_voice_install_packs.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: src/ifuri_app/cli.py
  [5] ○ extract_function   → src/ifuri_app/utils/cmd_voice_capabilities.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: src/ifuri_app/cli.py
  [6] ○ extract_function   → src/ifuri_app/utils/_scheme.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: src/ifuri_app/flow_compile.py, src/ifuri_app/flow_engine.py
  [7] ○ extract_function   → src/ifuri_app/utils/_stop.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/ifuri_app/cli.py

QUICK_WINS[3] (low risk, high savings — do first):
  [1] extract_function   saved=17L  → src/ifuri_app/utils/list_routes.py
      FILES: urirun_bridge.py
  [2] extract_function   saved=10L  → src/ifuri_app/utils/cmd_flow_run.py
      FILES: cli.py
  [3] extract_function   saved=7L  → src/ifuri_app/utils/node_llm_available.py
      FILES: urisys_client.py

EFFORT_ESTIMATE (total ≈ 1.7h):
  medium list_routes                         saved=17L  ~34min
  easy   cmd_flow_run                        saved=10L  ~20min
  easy   node_llm_available                  saved=7L  ~14min
  easy   cmd_voice_install_packs             saved=5L  ~10min
  easy   cmd_voice_capabilities              saved=4L  ~8min
  easy   _scheme                             saved=4L  ~8min
  easy   _stop                               saved=3L  ~6min

METRICS-TARGET:
  dup_groups:  7 → 0
  saved_lines: 50 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 498 func | 43f | 2026-06-21
# generated in 0.00s

NEXT[10] (ranked by impact):
  [1] !! SPLIT           src/ifuri_app/gui.py
      WHY: 1005L, 2 classes, max CC=15
      EFFORT: ~4h  IMPACT: 15075

  [2] !! SPLIT-FUNC      channels_from_scan  CC=34  fan=16
      WHY: CC=34 exceeds 15
      EFFORT: ~1h  IMPACT: 544

  [3] !  SPLIT-FUNC      run_voice_command  CC=23  fan=18
      WHY: CC=23 exceeds 15
      EFFORT: ~1h  IMPACT: 414

  [4] !  SPLIT-FUNC      RuntimeState.run_flow  CC=17  fan=24
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 408

  [5] !  SPLIT-FUNC      send_chat_message  CC=18  fan=22
      WHY: CC=18 exceeds 15
      EFFORT: ~1h  IMPACT: 396

  [6] !  SPLIT-FUNC      scan_network  CC=17  fan=23
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 391

  [7] !! SPLIT-FUNC      normalize_packages  CC=31  fan=11
      WHY: CC=31 exceeds 15
      EFFORT: ~1h  IMPACT: 341

  [8] !  SPLIT-FUNC      scan_urisys_nodes  CC=15  fan=18
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 270

  [9] !  SPLIT-FUNC      renderChannelList  CC=21  fan=12
      WHY: CC=21 exceeds 15
      EFFORT: ~1h  IMPACT: 252

  [10] !  SPLIT-FUNC      ChatTabMixin._apply_chat_channels  CC=16  fan=15
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 240


RISKS[3]:
  ⚠ Splitting desktop/src-tauri/gen/schemas/desktop-schema.json may break 0 import paths
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting src/ifuri_app/gui.py may break 67 import paths

METRICS-TARGET:
  CC̄:          4.1 → ≤2.9
  max-CC:      34 → ≤17
  god-modules: 8 → 0
  high-CC(≥15): 18 → ≤9
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=4.1 → now CC̄=4.1
```

## Intent

ifURI desktop app — voice UI, urisys-node client, and URI flow runner for urisys-examples.
