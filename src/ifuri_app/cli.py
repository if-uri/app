from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from pathlib import Path

from . import DEFAULT_PORT, __version__
from .discovery import DiscoveryResponder, discover
from .flow_engine import dry_run_flow, dry_run_uri, expand_flow
from .flow_runner import run_flow_file
from .gui import launch_gui
from .runtime import PortInUseError, RuntimeServer, _port_available, find_free_port
from .storage import load_workspace, save_workspace, workspace_path
from .packs.loader import pack_summary
from .packs.runtime import local_runtime_info
from .urisys_client import UrisysNodeClient
from .url_params import voice_url
from .voice_pipeline import plan_voice_command, run_voice_command
from .voice_planner import load_flow_catalog, voice_planner_mode


def print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_init(args) -> int:
    data = load_workspace()
    if args.endpoint:
        data.setdefault("urisys", {})["endpoint"] = args.endpoint.rstrip("/")
    elif args.scan_lan:
        from .network_scan import scan_urisys_nodes

        nodes = scan_urisys_nodes(timeout=min(max(args.timeout, 0.5), 5.0))
        if not nodes:
            print("No urisys-node found on LAN", file=sys.stderr)
            return 1
        preferred = next((n for n in nodes if n.get("node_id") == "lenovo"), nodes[0])
        data.setdefault("urisys", {})["endpoint"] = preferred["endpoint"]
    save_workspace(data)
    client = UrisysNodeClient()
    health = client.health()
    print_json(
        {
            "ok": bool(health.get("ok")),
            "workspace": str(workspace_path()),
            "endpoint": client.endpoint,
            "health": health,
        }
    )
    return 0 if health.get("ok") else 1


def cmd_app(_args) -> int:
    launch_gui()
    return 0


def cmd_serve(args) -> int:
    data = load_workspace()
    data.setdefault("urisys", {})["endpoint"] = args.urisys_endpoint
    save_workspace(data)
    port = args.port
    if args.auto_port and not _port_available(args.host, port):
        port = find_free_port(args.host, port)
        print(f"auto-port: using {port}", file=sys.stderr)
    try:
        server = RuntimeServer(args.host, port).start()
    except PortInUseError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    responder = DiscoveryResponder(api_port=port).start() if args.discovery else None
    print(f"ifURI runtime listening on {server.url}")
    if args.discovery:
        print(f"LAN discovery enabled on UDP")
    stop = False

    def _stop(_sig, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    try:
        while not stop:
            time.sleep(0.2)
    finally:
        if responder:
            responder.stop()
        server.stop()
    return 0


def cmd_discover(args) -> int:
    peers = discover(timeout=args.timeout, api_port=args.port)
    print_json({"ok": True, "peers": peers})
    return 0


def cmd_voice(args) -> int:
    port = args.port
    if args.auto_port and not _port_available(args.host, port):
        port = find_free_port(args.host, port)
        print(f"auto-port: using {port}", file=sys.stderr)
    try:
        server = RuntimeServer(args.host, port).start()
    except PortInUseError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"ifURI voice UI: {voice_url(server.url, lang=args.lang, theme=args.theme, view=args.view, channel=args.channel, prompt=args.prompt)}")
    print(f"urisys-node: {args.urisys_endpoint}")
    data = load_workspace()
    data.setdefault("urisys", {})["endpoint"] = args.urisys_endpoint
    save_workspace(data)
    if args.discovery:
        DiscoveryResponder(api_port=port).start()
    stop = False

    def _stop(_sig, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    try:
        while not stop:
            time.sleep(0.2)
    finally:
        server.stop()
    return 0


def cmd_node_health(args) -> int:
    client = UrisysNodeClient(args.endpoint)
    print_json({"endpoint": client.endpoint, "health": client.health()})
    return 0


def cmd_node_call(args) -> int:
    client = UrisysNodeClient(args.endpoint)
    payload = json.loads(args.payload or "{}")
    print_json(client.call_uri(args.uri, payload, dry_run=args.dry_run))
    return 0


def cmd_node_control_test(args) -> int:
    client = UrisysNodeClient(args.endpoint)
    result = probe_remote_control(client, node_id=args.node_id)
    print_json(result)
    return 0 if result.get("ok") else 1


def cmd_node_screen(args) -> int:
    client = UrisysNodeClient(args.endpoint)
    result = capture_remote_screen(
        client,
        node_id=args.node_id,
        monitor=args.monitor,
        source=args.source,
    )
    if result.get("ok") and result.get("png") and args.out:
        Path(args.out).write_bytes(result["png"])
        result = dict(result)
        result.pop("png")
        result["saved"] = args.out
    elif result.get("ok") and result.get("png"):
        import base64

        result = dict(result)
        result["png_b64"] = base64.b64encode(result.pop("png")).decode("ascii")
    print_json(result)
    return 0 if result.get("ok") else 1


def cmd_flow_run(args) -> int:
    client = UrisysNodeClient(args.endpoint) if args.endpoint else None
    print_json(
        run_flow_file(
            args.flow,
            client=client,
            dry_run=args.dry_run,
        )
    )
    return 0


def cmd_voice_plan(args) -> int:
    client = UrisysNodeClient(args.endpoint) if args.endpoint else None
    print_json(
        plan_voice_command(
            args.text,
            client=client,
            planner=args.planner,
        )
    )
    return 0


def cmd_voice_catalog(_args) -> int:
    print_json({"planner": voice_planner_mode(), "flows": load_flow_catalog(refresh=True)})
    return 0


def cmd_voice_run(args) -> int:
    client = UrisysNodeClient(args.endpoint) if args.endpoint else None
    result = run_voice_command(
        args.text,
        client=client,
        dry_run=args.dry_run,
        speak=not args.no_speak,
    )
    print_json(result)
    return 0 if result.get("ok") else 1


def cmd_chat_channels(args) -> int:
    data = list_chat_channels(timeout=args.timeout, scan_subnet=not args.no_scan)
    print_json(data)
    return 0 if data.get("ok") else 1


def cmd_chat_send(args) -> int:
    text = (args.prompt or args.text or "").strip()
    if not text:
        print_json({"ok": False, "error": "missing text — pass message or --prompt"})
        return 1
    data = list_chat_channels(timeout=min(args.timeout, 2.0), scan_subnet=not args.no_scan)
    channels = data.get("channels") or []
    match = None
    if args.channel_id:
        match = next((c for c in channels if c.get("id") == args.channel_id), None)
    elif args.endpoint:
        match = next((c for c in channels if c.get("endpoint") == args.endpoint.rstrip("/")), None)
    elif args.uri:
        match = next((c for c in channels if c.get("uri") == args.uri), None)
    if not match:
        print_json({"ok": False, "error": "channel not found", "channels": [c.get("id") for c in channels]})
        return 1
    result = send_chat_message_routed(
        match,
        text,
        router_endpoint=args.router or args.endpoint,
        dry_run=args.dry_run,
    )
    print_json(result)
    return 0 if result.get("ok", True) and not result.get("error") else 1


def cmd_chat_migrate(args) -> int:
    result = migrate_local_chat_to_urisys(
        router_endpoint=args.endpoint,
        dry_run=args.dry_run,
        force=args.force,
    )
    print_json(result)
    return 0 if result.get("ok") else 1


def cmd_chat_status(args) -> int:
    print_json(urisys_chat_available(router_endpoint=args.endpoint))
    return 0


def cmd_packs(_args) -> int:
    print_json({"summary": pack_summary(), "runtime": local_runtime_info()})
    return 0


def cmd_flow_validate(args) -> int:
    from .flow_compile import validate_flow_compiled

    text = Path(args.flow_file).read_text(encoding="utf-8")
    print_json(validate_flow_compiled(text))
    return 0


def cmd_run(args) -> int:
    target = args.target
    if Path(target).exists():
        text = Path(target).read_text(encoding="utf-8")
        result = dry_run_flow(text) if args.dry_run else dry_run_flow(text)
    elif "://" in target:
        result = dry_run_uri(target)
    else:
        print(f"not a file or URI: {target}", file=sys.stderr)
        return 2
    print_json(result)
    return 0


def cmd_expand(args) -> int:
    text = Path(args.flow_file).read_text(encoding="utf-8")
    print_json(expand_flow(text))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ifuri-app", description="ifURI desktop app and local URI runtime")
    parser.add_argument("--version", action="version", version=f"ifuri {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_app = sub.add_parser("app", help="open desktop app")
    p_app.set_defaults(func=cmd_app)

    p_init = sub.add_parser("init", help="create workspace and configure urisys-node endpoint")
    p_init.add_argument("--endpoint", help="urisys-node base URL, e.g. http://192.168.188.201:8790")
    p_init.add_argument("--scan-lan", action="store_true", help="discover urisys-node on /24 and save first hit")
    p_init.add_argument("--timeout", type=float, default=2.0, help="LAN scan timeout when using --scan-lan")
    p_init.set_defaults(func=cmd_init)

    p_serve = sub.add_parser("serve", help="start local runtime HTTP API")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    p_serve.add_argument("--auto-port", action="store_true", help="pick next free port if --port is busy")
    p_serve.add_argument("--no-discovery", dest="discovery", action="store_false")
    p_serve.add_argument("--urisys-endpoint", default=UrisysNodeClient().endpoint)
    p_serve.set_defaults(func=cmd_serve, discovery=True)

    p_voice = sub.add_parser("voice", help="voice UI + runtime (stt/tts → urisys flows)")
    p_voice.add_argument("--host", default="127.0.0.1")
    p_voice.add_argument("--port", type=int, default=DEFAULT_PORT)
    p_voice.add_argument("--auto-port", action="store_true", default=True, help="pick next free port if --port is busy (default: on)")
    p_voice.add_argument("--no-auto-port", dest="auto_port", action="store_false")
    p_voice.add_argument("--urisys-endpoint", default=UrisysNodeClient().endpoint)
    p_voice.add_argument("--lang", default=None, help="URL param lang=pl|en")
    p_voice.add_argument("--theme", default=None, help="URL param theme=dark|light|ifuri")
    p_voice.add_argument("--view", default=None, help="URL param view=chat|screen")
    p_voice.add_argument("--channel", default=None, help="URL param channel=<id>")
    p_voice.add_argument("--prompt", default=None, help="URL param prompt=<message>")
    p_voice.add_argument("--no-discovery", dest="discovery", action="store_false")
    p_voice.set_defaults(func=cmd_voice, discovery=True)

    p_nh = sub.add_parser("node-health", help="GET urisys-node /health")
    p_nh.add_argument("--endpoint", default=UrisysNodeClient().endpoint)
    p_nh.set_defaults(func=cmd_node_health)

    p_nc = sub.add_parser("node-call", help="POST urisys-node /uri/call")
    p_nc.add_argument("uri")
    p_nc.add_argument("--payload", default="{}")
    p_nc.add_argument("--endpoint", default=UrisysNodeClient().endpoint)
    p_nc.add_argument("--dry-run", action="store_true")
    p_nc.set_defaults(func=cmd_node_call)

    p_nct = sub.add_parser("node-control-test", help="probe remote node control (health + screen)")
    p_nct.add_argument("--endpoint", default=UrisysNodeClient().endpoint)
    p_nct.add_argument("--node-id", default="lenovo")
    p_nct.set_defaults(func=cmd_node_control_test)

    p_ns = sub.add_parser("node-screen", help="capture remote screen PNG via screen:// or kvm://")
    p_ns.add_argument("--endpoint", default=UrisysNodeClient().endpoint)
    p_ns.add_argument("--node-id", default="lenovo")
    p_ns.add_argument("--monitor", type=int, default=1)
    p_ns.add_argument("--source", choices=["screen", "kvm"], default="screen")
    p_ns.add_argument("--out", help="save PNG to file")
    p_ns.set_defaults(func=cmd_node_screen)

    p_fr = sub.add_parser("flow-run", help="run urisys-examples *.uri.flow.yaml via node")
    p_fr.add_argument("flow", help="e.g. lenovo-remote/08-kvm-linkedin.uri.flow.yaml")
    p_fr.add_argument("--endpoint", default=UrisysNodeClient().endpoint)
    p_fr.add_argument("--dry-run", action="store_true")
    p_fr.set_defaults(func=cmd_flow_run)

    p_vp = sub.add_parser("voice-plan", help="plan voice text → flow")
    p_vp.add_argument("text")
    p_vp.add_argument("--endpoint", default=UrisysNodeClient().endpoint, help="urisys-node for llm:// planner")
    p_vp.add_argument("--planner", choices=["auto", "regex", "catalog", "llm"], default=None)
    p_vp.set_defaults(func=cmd_voice_plan)

    p_vc = sub.add_parser("voice-catalog", help="list urisys-examples flows for voice planner")
    p_vc.set_defaults(func=cmd_voice_catalog)

    p_vr = sub.add_parser("voice-run", help="run voice command pipeline")
    p_vr.add_argument("text")
    p_vr.add_argument("--endpoint", default=UrisysNodeClient().endpoint)
    p_vr.add_argument("--dry-run", action="store_true")
    p_vr.add_argument("--no-speak", action="store_true")
    p_vr.set_defaults(func=cmd_voice_run)

    p_cc = sub.add_parser("chat-channels", help="list LAN endpoints as chat channels")
    p_cc.add_argument("--timeout", type=float, default=1.8)
    p_cc.add_argument("--no-scan", action="store_true", help="only configured hosts, skip /24 scan")
    p_cc.set_defaults(func=cmd_chat_channels)

    p_cs = sub.add_parser("chat-send", help="send message to a chat channel")
    p_cs.add_argument("text", nargs="?", default=None)
    p_cs.add_argument("--prompt", help="message text (alias for positional text)")
    p_cs.add_argument("--channel-id", help="channel id from chat-channels")
    p_cs.add_argument("--endpoint", help="urisys-node endpoint channel")
    p_cs.add_argument("--uri", help="MCP/A2A/LLM uri channel")
    p_cs.add_argument("--router", help="urisys-node router for MCP/A2A calls")
    p_cs.add_argument("--timeout", type=float, default=1.8)
    p_cs.add_argument("--no-scan", action="store_true")
    p_cs.add_argument("--dry-run", action="store_true")
    p_cs.set_defaults(func=cmd_chat_send)

    p_cm = sub.add_parser("chat-migrate", help="upload local ~/.ifuri/app-chat.jsonl to urisys-node /app/chat")
    p_cm.add_argument("--endpoint", default=UrisysNodeClient().endpoint, help="urisys-node with /app/chat/*")
    p_cm.add_argument("--dry-run", action="store_true")
    p_cm.add_argument("--force", action="store_true", help="upload even when remote channel has messages")
    p_cm.set_defaults(func=cmd_chat_migrate)

    p_cst = sub.add_parser("chat-status", help="check if urisys-node exposes /app/chat/*")
    p_cst.add_argument("--endpoint", default=UrisysNodeClient().endpoint)
    p_cst.set_defaults(func=cmd_chat_status)

    p_packs = sub.add_parser("packs", help="list local URI packs (packages/)")
    p_packs.set_defaults(func=cmd_packs)

    p_fv = sub.add_parser("flow-validate", help="validate compact URI flow YAML")
    p_fv.add_argument("flow_file")
    p_fv.set_defaults(func=cmd_flow_validate)

    p_disc = sub.add_parser("discover", help="discover ifuri:// apps in local network")
    p_disc.add_argument("--timeout", type=float, default=1.2)
    p_disc.add_argument("--port", type=int, default=DEFAULT_PORT)
    p_disc.set_defaults(func=cmd_discover)

    p_run = sub.add_parser("run", help="dry-run URI or .uri.flow.yaml file")
    p_run.add_argument("target")
    p_run.add_argument("--dry-run", action="store_true", default=True)
    p_run.set_defaults(func=cmd_run)

    p_expand = sub.add_parser("expand", help="expand compact URI flow to workflow_graph")
    p_expand.add_argument("flow_file")
    p_expand.set_defaults(func=cmd_expand)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        return cmd_app(args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
