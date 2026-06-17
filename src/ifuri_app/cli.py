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
from .gui import launch_gui
from .runtime import RuntimeServer
from .storage import load_workspace, save_workspace, workspace_path


def print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_init(_args) -> int:
    data = load_workspace()
    save_workspace(data)
    print(f"workspace: {workspace_path()}")
    return 0


def cmd_app(_args) -> int:
    launch_gui()
    return 0


def cmd_serve(args) -> int:
    server = RuntimeServer(args.host, args.port).start()
    responder = DiscoveryResponder(api_port=args.port).start() if args.discovery else None
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
    parser.add_argument("--version", action="version", version=f"ifuri-app {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_app = sub.add_parser("app", help="open desktop app")
    p_app.set_defaults(func=cmd_app)

    p_init = sub.add_parser("init", help="create default workspace")
    p_init.set_defaults(func=cmd_init)

    p_serve = sub.add_parser("serve", help="start local runtime HTTP API")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    p_serve.add_argument("--no-discovery", dest="discovery", action="store_false")
    p_serve.set_defaults(func=cmd_serve, discovery=True)

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
