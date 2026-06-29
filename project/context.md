# System Architecture Analysis
<!-- generated in 0.00s -->

## Overview

- **Project**: ~/github/if-uri/app
- **Primary Language**: python
- **Languages**: python: 41, shell: 11, yaml: 10, javascript: 10, json: 5
- **Analysis Mode**: static
- **Total Functions**: 512
- **Total Classes**: 12
- **Modules**: 86
- **Entry Points**: 297

## Architecture by Module

### src.ifuri_app.web.voice
- **Functions**: 133
- **File**: `voice.js`

### src.ifuri_app.gui
- **Functions**: 67
- **Classes**: 2
- **File**: `gui.py`

### src.ifuri_app.cli
- **Functions**: 34
- **File**: `cli.py`

### src.ifuri_app.web.webrtc_peer
- **Functions**: 27
- **Classes**: 1
- **File**: `webrtc_peer.js`

### src.ifuri_app.chat_channels
- **Functions**: 17
- **File**: `chat_channels.py`

### src.ifuri_app.runtime
- **Functions**: 16
- **Classes**: 4
- **File**: `runtime.py`

### src.ifuri_app.web.url_state
- **Functions**: 15
- **File**: `url_state.js`

### src.ifuri_app.gui_chat
- **Functions**: 15
- **Classes**: 1
- **File**: `gui_chat.py`

### src.ifuri_app.urirun_bridge
- **Functions**: 14
- **File**: `urirun_bridge.py`

### packages.ifuri-page.handlers
- **Functions**: 13
- **File**: `handlers.js`

### src.ifuri_app.web.page.handlers
- **Functions**: 13
- **File**: `handlers.js`

### src.ifuri_app.urisys_client
- **Functions**: 12
- **Classes**: 1
- **File**: `urisys_client.py`

### src.ifuri_app.voice_planner
- **Functions**: 11
- **File**: `voice_planner.py`

### src.ifuri_app.connect_store
- **Functions**: 10
- **File**: `connect_store.py`

### src.ifuri_app.flow_engine
- **Functions**: 10
- **File**: `flow_engine.py`

### src.ifuri_app.network_scan
- **Functions**: 9
- **File**: `network_scan.py`

### src.ifuri_app.storage
- **Functions**: 8
- **File**: `storage.py`

### src.ifuri_app.web.theme
- **Functions**: 8
- **File**: `theme.js`

### src.ifuri_app.webrtc_signal
- **Functions**: 7
- **File**: `webrtc_signal.py`

### src.ifuri_app.novnc_demo
- **Functions**: 7
- **File**: `novnc_demo.py`

## Key Entry Points

Main execution flows into the system:

### src.ifuri_app.gui.IfuriDesktop._build_network_tab
- **Calls**: ttk.Frame, self.notebook.add, tab.columnconfigure, tab.rowconfigure, tk.IntVar, ttk.Frame, top.grid, None.pack

### src.ifuri_app.gui.IfuriDesktop._build_connect_tab
> IFURI-017 scaffold: browse the connect.ifuri.com hub, install packages, preview run payloads.

The catalog HTTP contract is provisional (see ifuri_app
- **Calls**: ttk.Frame, self.notebook.add, tab.columnconfigure, tab.rowconfigure, ttk.Frame, top.grid, top.columnconfigure, None.grid

### src.ifuri_app.gui_chat.ChatTabMixin._build_chat_tab
- **Calls**: ttk.Frame, self.notebook.add, tab.columnconfigure, tab.rowconfigure, ttk.Frame, left.grid, left.rowconfigure, ttk.Frame

### src.ifuri_app.gui.IfuriDesktop._build_flows_tab
- **Calls**: ttk.Frame, self.notebook.add, tab.columnconfigure, tab.rowconfigure, ttk.Frame, left.grid, None.pack, tk.Listbox

### src.ifuri_app.gui.IfuriDesktop._build_services_tab
- **Calls**: ttk.Frame, self.notebook.add, tab.rowconfigure, tab.columnconfigure, ttk.Frame, tree_frame.grid, tree_frame.rowconfigure, tree_frame.columnconfigure

### src.ifuri_app.runtime.RuntimeState.run_flow
- **Calls**: self.load, src.ifuri_app.flow_engine.expand_flow, UrisysNodeClient, src.ifuri_app.runtime._load_urirun_policy, src.ifuri_app.storage.add_event, src.ifuri_app.storage.save_workspace, src.ifuri_app.flow_engine.dry_run_flow, src.ifuri_app.storage.add_event

### src.ifuri_app.gui.FirstRunWizard.__init__
- **Calls**: None.__init__, self.title, self.geometry, self.transient, self.resizable, ttk.Frame, frm.pack, None.pack

### src.ifuri_app.gui.IfuriDesktop._refresh_network_views
- **Calls**: hasattr, hasattr, self._refresh_peers, self.device_tree.delete, self.lan_services_tree.delete, scan.get, self.device_tree.insert, scan.get

### src.ifuri_app.gui.IfuriDesktop._build_connectors_tab
- **Calls**: ttk.Frame, self.notebook.add, tab.columnconfigure, tab.rowconfigure, ttk.Frame, top.grid, None.pack, None.pack

### src.ifuri_app.runtime.RuntimeState.call_uri
- **Calls**: self.load, urirun_dispatch, src.ifuri_app.flow_engine.dry_run_uri, src.ifuri_app.storage.add_event, src.ifuri_app.storage.save_workspace, None.get, src.ifuri_app.packs.runtime.dispatch_local_uri, src.ifuri_app.packs.runtime.get_local_uri_runtime

### src.ifuri_app.chat_store.LocalChatStore.list_channels
- **Calls**: max, None.splitlines, sorted, self.path.exists, min, row.get, str, by_id.values

### src.ifuri_app.gui_chat.ChatTabMixin._apply_chat_channels
- **Calls**: self._chat_channel_map.clear, self.chat_channel_list.delete, self.chat_scan_status.set, self._refresh_network_views, data.get, data.get, data.get, self.chat_channel_list.size

### src.ifuri_app.gui.IfuriDesktop._render_payload_form
- **Calls**: self.payload_form.winfo_children, packages.ifuri-page.handlers.next, None.grid, src.ifuri_app.connect_store.payload_form_fields, enumerate, child.destroy, pkg.get, None.grid

### src.ifuri_app.cli.cmd_init
- **Calls**: src.ifuri_app.storage.load_workspace, src.ifuri_app.storage.save_workspace, UrisysNodeClient, client.health, src.ifuri_app.cli.print_json, args.endpoint.rstrip, health.get, data.setdefault

### src.ifuri_app.cli.cmd_serve
- **Calls**: src.ifuri_app.storage.load_workspace, src.ifuri_app.storage.save_workspace, print, signal.signal, signal.signal, data.setdefault, src.ifuri_app.runtime.find_free_port, print

### src.ifuri_app.cli.cmd_voice
- **Calls**: print, print, src.ifuri_app.storage.load_workspace, src.ifuri_app.storage.save_workspace, signal.signal, signal.signal, src.ifuri_app.runtime.find_free_port, print

### src.ifuri_app.cli.cmd_chat_send
- **Calls**: None.strip, src.ifuri_app.chat_channels.list_chat_channels, src.ifuri_app.chat_channels.send_chat_message_routed, src.ifuri_app.cli.print_json, src.ifuri_app.cli.print_json, data.get, packages.ifuri-page.handlers.next, src.ifuri_app.cli.print_json

### packages.ifuri-bridge.handlers.urisys_call.urisys_call
- **Calls**: str, packages.ifuri-bridge.handlers.urisys_call._endpoint, bool, bool, payload.get, payload.get, payload.get, UrisysNodeClient

### src.ifuri_app.gui_chat.ChatTabMixin._load_chat_history_from_urisys
- **Calls**: self.chat_log.configure, self.chat_log.delete, self.chat_log.insert, self.chat_log.configure, None.start, self.after, src.ifuri_app.chat_channels.fetch_chat_history, threading.Thread

### src.ifuri_app.gui_chat.ChatTabMixin._send_chat_message
- **Calls**: None.strip, self.chat_input.delete, self._sync_chat_prompt_url, dict, self.chat_dry_run.get, self._router_endpoint, self._append_chat, self._append_chat

### src.ifuri_app.runtime.RuntimeState.health
- **Calls**: self.load, None.health, None.get, data.get, str, len, len, src.ifuri_app.packs.runtime.local_runtime_info

### src.ifuri_app.gui.IfuriDesktop._build_ui
- **Calls**: ttk.Frame, top.pack, None.pack, None.pack, None.pack, ttk.Notebook, self.notebook.pack, self._build_chat_tab

### src.ifuri_app.gui.IfuriDesktop._connectors_done
- **Calls**: tree.delete, self.connectors_status.set, res.get, len, tree.insert, None.items, tree.get_children, res.get

### src.ifuri_app.gui.IfuriDesktop.start_runtime
- **Calls**: int, self.runtime_status.set, src.ifuri_app.storage.save_workspace, hasattr, self.append_log, self.runtime_status.set, self.port_var.get, None.start

### src.ifuri_app.cli.cmd_node_screen
- **Calls**: UrisysNodeClient, src.ifuri_app.remote_screen.capture_remote_screen, src.ifuri_app.cli.print_json, result.get, result.get, None.write_bytes, dict, result.pop

### src.ifuri_app.web.webrtc_peer.WebRtcPeerSession.start
- **Calls**: src.ifuri_app.web.webrtc_peer.WebRtcPeerSession._setStatus, src.ifuri_app.web.webrtc_peer.RTCPeerConnection, src.ifuri_app.web.webrtc_peer.postRemote, src.ifuri_app.web.webrtc_peer.toJSON, src.ifuri_app.web.webrtc_peer.String, src.ifuri_app.web.webrtc_peer.WebRtcPeerSession._wireChannel, src.ifuri_app.web.webrtc_peer.createDataChannel, src.ifuri_app.web.webrtc_peer.getUserMedia

### src.ifuri_app.discovery.DiscoveryResponder._loop
- **Calls**: socket.socket, sock.setsockopt, sock.settimeout, sock.bind, self._stop.is_set, src.ifuri_app.discovery.local_descriptor, sock.recvfrom, json.loads

### src.ifuri_app.gui.IfuriDesktop.install_selected_connector
- **Calls**: self._selected_package, src.ifuri_app.connect_store.install_command, self._connect_log, self.connect_status.set, None.start, self.connect_status.set, self._connect_log, self.after

### src.ifuri_app.gui.IfuriDesktop.discover_peers
- **Calls**: self.scan_status.set, self.update_idletasks, src.ifuri_app.network_scan.scan_network, src.ifuri_app.storage.load_workspace, self.scan_status.set, self._refresh_network_views, self.append_log, result.get

### src.ifuri_app.cli.cmd_run
- **Calls**: None.exists, src.ifuri_app.cli.print_json, src.ifuri_app.urirun_bridge.parse_json_object, None.read_text, src.ifuri_app.cli.print_json, Path, src.ifuri_app.flow_engine.dry_run_flow, None.run_flow

## Process Flows

Key execution flows identified:

### Flow 1: _build_network_tab
```
_build_network_tab [src.ifuri_app.gui.IfuriDesktop]
```

### Flow 2: _build_connect_tab
```
_build_connect_tab [src.ifuri_app.gui.IfuriDesktop]
```

### Flow 3: _build_chat_tab
```
_build_chat_tab [src.ifuri_app.gui_chat.ChatTabMixin]
```

### Flow 4: _build_flows_tab
```
_build_flows_tab [src.ifuri_app.gui.IfuriDesktop]
```

### Flow 5: _build_services_tab
```
_build_services_tab [src.ifuri_app.gui.IfuriDesktop]
```

### Flow 6: run_flow
```
run_flow [src.ifuri_app.runtime.RuntimeState]
  └─ →> expand_flow
      └─> _legacy_expand_flow
          └─> extract_steps
          └─> flow_id_from_text
  └─ →> _load_urirun_policy
  └─ →> add_event
      └─> now_iso
```

### Flow 7: __init__
```
__init__ [src.ifuri_app.gui.FirstRunWizard]
```

### Flow 8: _refresh_network_views
```
_refresh_network_views [src.ifuri_app.gui.IfuriDesktop]
```

### Flow 9: _build_connectors_tab
```
_build_connectors_tab [src.ifuri_app.gui.IfuriDesktop]
```

### Flow 10: call_uri
```
call_uri [src.ifuri_app.runtime.RuntimeState]
  └─ →> dry_run_uri
      └─> classify_route
          └─> uri_scheme
  └─ →> add_event
      └─> now_iso
  └─ →> save_workspace
      └─> normalize_workspace
      └─> ensure_home
          └─> app_home
```

## Key Classes

### src.ifuri_app.gui.IfuriDesktop
- **Methods**: 59
- **Key Methods**: src.ifuri_app.gui.IfuriDesktop.__init__, src.ifuri_app.gui.IfuriDesktop._set_app_icon, src.ifuri_app.gui.IfuriDesktop._build_style, src.ifuri_app.gui.IfuriDesktop._build_ui, src.ifuri_app.gui.IfuriDesktop._build_flows_tab, src.ifuri_app.gui.IfuriDesktop._build_services_tab, src.ifuri_app.gui.IfuriDesktop._build_network_tab, src.ifuri_app.gui.IfuriDesktop._build_connectors_tab, src.ifuri_app.gui.IfuriDesktop._connector_endpoints, src.ifuri_app.gui.IfuriDesktop.refresh_connectors
- **Inherits**: ChatTabMixin, tk.Tk

### src.ifuri_app.web.webrtc_peer.WebRtcPeerSession
- **Methods**: 23
- **Key Methods**: src.ifuri_app.web.webrtc_peer.WebRtcPeerSession.isReady, src.ifuri_app.web.webrtc_peer.WebRtcPeerSession._setStatus, src.ifuri_app.web.webrtc_peer.WebRtcPeerSession._dispatch, src.ifuri_app.web.webrtc_peer.WebRtcPeerSession.clearTimeout, src.ifuri_app.web.webrtc_peer.WebRtcPeerSession.start, src.ifuri_app.web.webrtc_peer.WebRtcPeerSession.stream, src.ifuri_app.web.webrtc_peer.WebRtcPeerSession.offer, src.ifuri_app.web.webrtc_peer.WebRtcPeerSession.posted, src.ifuri_app.web.webrtc_peer.WebRtcPeerSession._wireChannel, src.ifuri_app.web.webrtc_peer.WebRtcPeerSession._poll

### src.ifuri_app.gui_chat.ChatTabMixin
> Mixin for IfuriDesktop — call _build_chat_tab() from _build_ui.
- **Methods**: 15
- **Key Methods**: src.ifuri_app.gui_chat.ChatTabMixin._build_chat_tab, src.ifuri_app.gui_chat.ChatTabMixin._router_endpoint, src.ifuri_app.gui_chat.ChatTabMixin._runtime_base_url, src.ifuri_app.gui_chat.ChatTabMixin._chat_prompt_text, src.ifuri_app.gui_chat.ChatTabMixin._sync_chat_prompt_url, src.ifuri_app.gui_chat.ChatTabMixin._open_chat_in_browser, src.ifuri_app.gui_chat.ChatTabMixin._refresh_chat_channels, src.ifuri_app.gui_chat.ChatTabMixin._apply_chat_channels, src.ifuri_app.gui_chat.ChatTabMixin._on_chat_channel_select, src.ifuri_app.gui_chat.ChatTabMixin._load_chat_history_from_urisys

### src.ifuri_app.urisys_client.UrisysNodeClient
- **Methods**: 8
- **Key Methods**: src.ifuri_app.urisys_client.UrisysNodeClient.__init__, src.ifuri_app.urisys_client.UrisysNodeClient.health, src.ifuri_app.urisys_client.UrisysNodeClient.call_uri, src.ifuri_app.urisys_client.UrisysNodeClient.app_chat_messages, src.ifuri_app.urisys_client.UrisysNodeClient.app_chat_channels, src.ifuri_app.urisys_client.UrisysNodeClient.app_chat_append, src.ifuri_app.urisys_client.UrisysNodeClient._get, src.ifuri_app.urisys_client.UrisysNodeClient._post

### src.ifuri_app.gui.FirstRunWizard
> First-run setup: scan the LAN, pick (or type) a urirun node endpoint, save it.

Self-contained modal
- **Methods**: 7
- **Key Methods**: src.ifuri_app.gui.FirstRunWizard.__init__, src.ifuri_app.gui.FirstRunWizard._scan, src.ifuri_app.gui.FirstRunWizard._scan_done, src.ifuri_app.gui.FirstRunWizard._on_pick, src.ifuri_app.gui.FirstRunWizard._save, src.ifuri_app.gui.FirstRunWizard._skip, src.ifuri_app.gui.FirstRunWizard._finish
- **Inherits**: tk.Toplevel

### src.ifuri_app.runtime.RuntimeState
- **Methods**: 5
- **Key Methods**: src.ifuri_app.runtime.RuntimeState.__init__, src.ifuri_app.runtime.RuntimeState.load, src.ifuri_app.runtime.RuntimeState.health, src.ifuri_app.runtime.RuntimeState.call_uri, src.ifuri_app.runtime.RuntimeState.run_flow

### src.ifuri_app.chat_store.LocalChatStore
- **Methods**: 4
- **Key Methods**: src.ifuri_app.chat_store.LocalChatStore.__init__, src.ifuri_app.chat_store.LocalChatStore.append, src.ifuri_app.chat_store.LocalChatStore.list_messages, src.ifuri_app.chat_store.LocalChatStore.list_channels

### src.ifuri_app.discovery.DiscoveryResponder
- **Methods**: 4
- **Key Methods**: src.ifuri_app.discovery.DiscoveryResponder.__init__, src.ifuri_app.discovery.DiscoveryResponder.start, src.ifuri_app.discovery.DiscoveryResponder.stop, src.ifuri_app.discovery.DiscoveryResponder._loop

### src.ifuri_app.runtime.RuntimeServer
- **Methods**: 4
- **Key Methods**: src.ifuri_app.runtime.RuntimeServer.__init__, src.ifuri_app.runtime.RuntimeServer.url, src.ifuri_app.runtime.RuntimeServer.start, src.ifuri_app.runtime.RuntimeServer.stop

### src.ifuri_app.flow_compile.FlowCompileError
> Flow text could not be compiled.
- **Methods**: 0
- **Inherits**: RuntimeError

### src.ifuri_app.runtime.PortInUseError
> HTTP bind failed because the port is already taken.
- **Methods**: 0
- **Inherits**: OSError

### src.ifuri_app.runtime.ThreadingHTTPServer
- **Methods**: 0
- **Inherits**: ThreadingMixIn, HTTPServer

## Data Transformation Functions

Key functions that process and transform data:

### src.ifuri_app.flow_compile._parse_flow_input
- **Output to**: isinstance, isinstance, load_flow, yaml.safe_load, isinstance

### src.ifuri_app.flow_compile.validate_flow_compiled
> Validate compact flow via uri2flow; return warnings or error.
- **Output to**: src.ifuri_app.flow_compile._parse_flow_input, src.ifuri_app.flow_compile.uri2flow_available, ImportError, validate_flow_document, validate_expanded_flow

### src.ifuri_app.voice_planner._parse_llm_plan_json
- **Output to**: isinstance, isinstance, data.get, src.ifuri_app.voice_planner._flow_plan, data.get

### src.ifuri_app.cli.cmd_flow_validate
- **Output to**: None.read_text, src.ifuri_app.cli.print_json, src.ifuri_app.flow_compile.validate_flow_compiled, Path

### src.ifuri_app.cli.build_parser
- **Output to**: argparse.ArgumentParser, parser.add_argument, parser.add_subparsers, sub.add_parser, p_app.set_defaults

### src.ifuri_app.chat_channels._format_json_reply
- **Output to**: json.dumps

### src.ifuri_app.chat_channels._format_voice_reply
- **Output to**: plan.get, result.get, isinstance, result.get, None.join

### src.ifuri_app.urirun_bridge.parse_json_object
- **Output to**: isinstance, json.loads, isinstance, ValueError

### scripts.gui_smoke.parse_args
- **Output to**: argparse.ArgumentParser, p.add_argument, p.add_argument, p.add_argument, p.parse_args

### src.ifuri_app.runtime.format_port_in_use_error
- **Output to**: src.ifuri_app.runtime._port_listeners, None.join, lines.append, lines.extend

## Behavioral Patterns

### state_machine_RuntimeState
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: src.ifuri_app.runtime.RuntimeState.__init__, src.ifuri_app.runtime.RuntimeState.load, src.ifuri_app.runtime.RuntimeState.health, src.ifuri_app.runtime.RuntimeState.call_uri, src.ifuri_app.runtime.RuntimeState.run_flow

### state_machine_IfuriDesktop
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: src.ifuri_app.gui.IfuriDesktop.__init__, src.ifuri_app.gui.IfuriDesktop._set_app_icon, src.ifuri_app.gui.IfuriDesktop._build_style, src.ifuri_app.gui.IfuriDesktop._build_ui, src.ifuri_app.gui.IfuriDesktop._build_flows_tab

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `src.ifuri_app.runtime.make_handler` - 453 calls
- `src.ifuri_app.cli.build_parser` - 174 calls
- `scripts.gui_smoke.run_gui_smoke` - 93 calls
- `src.ifuri_app.chat_channels.channels_from_scan` - 49 calls
- `src.ifuri_app.urirun_bridge.serve_http` - 46 calls
- `src.ifuri_app.connect_store.normalize_packages` - 41 calls
- `src.ifuri_app.runtime.RuntimeState.run_flow` - 41 calls
- `src.ifuri_app.network_scan.scan_network` - 35 calls
- `src.ifuri_app.chat_channels.send_chat_message` - 33 calls
- `src.ifuri_app.voice_pipeline.run_voice_command` - 30 calls
- `src.ifuri_app.discovery.discover` - 29 calls
- `src.ifuri_app.flow_compile.expand_flow_compiled` - 26 calls
- `src.ifuri_app.remote_screen.probe_remote_control` - 26 calls
- `src.ifuri_app.chat_channels.migrate_local_chat_to_urisys` - 26 calls
- `src.ifuri_app.chat_channels.send_chat_message_routed` - 25 calls
- `src.ifuri_app.runtime.RuntimeState.call_uri` - 25 calls
- `scripts.build-platform.run_pyinstaller` - 23 calls
- `src.ifuri_app.remote_screen.capture_remote_screen` - 22 calls
- `src.ifuri_app.voice_planner.load_flow_catalog` - 21 calls
- `src.ifuri_app.connectors.normalize_routes` - 21 calls
- `src.ifuri_app.chat_store.LocalChatStore.list_channels` - 20 calls
- `src.ifuri_app.voice_pipeline.install_voice_packs` - 20 calls
- `src.ifuri_app.network_scan.scan_urisys_nodes` - 19 calls
- `src.ifuri_app.voice_planner.plan_with_llm` - 19 calls
- `src.ifuri_app.cli.cmd_init` - 19 calls
- `src.ifuri_app.cli.cmd_serve` - 19 calls
- `src.ifuri_app.cli.cmd_voice` - 19 calls
- `src.ifuri_app.storage.load_workspace` - 18 calls
- `src.ifuri_app.cli.cmd_chat_send` - 18 calls
- `src.ifuri_app.chat_channels.fetch_chat_history` - 18 calls
- `src.ifuri_app.urirun_bridge.registry_summary` - 18 calls
- `src.ifuri_app.connect_store.payload_form_fields` - 17 calls
- `packages.ifuri-bridge.handlers.urisys_call.urisys_call` - 17 calls
- `src.ifuri_app.webrtc_pipeline.install_webrtc_pack` - 17 calls
- `src.ifuri_app.runtime.RuntimeState.health` - 17 calls
- `src.ifuri_app.gui.IfuriDesktop.start_runtime` - 17 calls
- `src.ifuri_app.storage.normalize_workspace` - 16 calls
- `src.ifuri_app.cli.cmd_node_screen` - 16 calls
- `src.ifuri_app.web.webrtc_peer.WebRtcPeerSession.start` - 16 calls
- `src.ifuri_app.gui.IfuriDesktop.install_selected_connector` - 16 calls

## System Interactions

How components interact:

```mermaid
graph TD
    _build_network_tab --> Frame
    _build_network_tab --> add
    _build_network_tab --> columnconfigure
    _build_network_tab --> rowconfigure
    _build_network_tab --> IntVar
    _build_connect_tab --> Frame
    _build_connect_tab --> add
    _build_connect_tab --> columnconfigure
    _build_connect_tab --> rowconfigure
    _build_chat_tab --> Frame
    _build_chat_tab --> add
    _build_chat_tab --> columnconfigure
    _build_chat_tab --> rowconfigure
    _build_flows_tab --> Frame
    _build_flows_tab --> add
    _build_flows_tab --> columnconfigure
    _build_flows_tab --> rowconfigure
    _build_services_tab --> Frame
    _build_services_tab --> add
    _build_services_tab --> rowconfigure
    _build_services_tab --> columnconfigure
    run_flow --> load
    run_flow --> expand_flow
    run_flow --> UrisysNodeClient
    run_flow --> _load_urirun_policy
    run_flow --> add_event
    __init__ --> __init__
    __init__ --> title
    __init__ --> geometry
    __init__ --> transient
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.