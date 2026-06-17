from __future__ import annotations

import json
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Any

from . import DEFAULT_PORT
from .discovery import DiscoveryResponder, discover
from .flow_engine import as_pretty_json, dry_run_flow
from .network_scan import scan_network
from .runtime import PortInUseError, RuntimeServer
from .storage import add_event, load_workspace, save_workspace, workspace_path
from .gui_chat import ChatTabMixin


class IfuriDesktop(ChatTabMixin, tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ifURI — URI Flow Runtime")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.workspace = load_workspace()
        self.current_group_index = 0
        self.current_flow_index = 0
        self.runtime: RuntimeServer | None = None
        self.discovery_responder: DiscoveryResponder | None = None
        self._build_style()
        self._build_ui()
        self._load_groups()
        self.after(300, self._refresh_chat_channels)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", padding=4)
        style.configure("TButton", padding=7)
        style.configure("Header.TLabel", font=("TkDefaultFont", 18, "bold"))

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=(12, 10))
        top.pack(fill="x")
        ttk.Label(top, text="ifURI", style="Header.TLabel").pack(side="left")
        ttk.Label(top, text="  if URI → then flow · local-first runtime", foreground="#5d6d7e").pack(side="left")
        ttk.Button(top, text="Save workspace", command=self.save_all).pack(side="right")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._build_chat_tab()
        self._build_network_tab()
        self._build_flows_tab()
        self._build_services_tab()
        self._build_events_tab()

    def _build_flows_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="URI flows")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        left = ttk.Frame(tab)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        ttk.Label(left, text="Groups").pack(anchor="w")
        self.group_list = tk.Listbox(left, width=28, exportselection=False)
        self.group_list.pack(fill="y", expand=True)
        self.group_list.bind("<<ListboxSelect>>", lambda _e: self._on_group_select())
        gbtn = ttk.Frame(left)
        gbtn.pack(fill="x", pady=6)
        ttk.Button(gbtn, text="+ group", command=self.new_group).pack(side="left")

        mid = ttk.Frame(tab)
        mid.grid(row=0, column=1, sticky="nsew")
        mid.columnconfigure(0, weight=1)
        mid.rowconfigure(1, weight=1)
        flow_top = ttk.Frame(mid)
        flow_top.grid(row=0, column=0, sticky="ew")
        ttk.Label(flow_top, text="Flows").pack(side="left")
        ttk.Button(flow_top, text="+ flow", command=self.new_flow).pack(side="right")
        ttk.Button(flow_top, text="Save flow", command=self.save_current_flow).pack(side="right", padx=6)
        ttk.Button(flow_top, text="Dry run", command=self.dry_run_current_flow).pack(side="right")

        body = ttk.PanedWindow(mid, orient="horizontal")
        body.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self.flow_list = tk.Listbox(body, width=32, exportselection=False)
        self.flow_list.bind("<<ListboxSelect>>", lambda _e: self._on_flow_select())
        body.add(self.flow_list, weight=1)
        editor_frame = ttk.Frame(body)
        editor_frame.rowconfigure(0, weight=1)
        editor_frame.columnconfigure(0, weight=1)
        self.editor = tk.Text(editor_frame, wrap="none", undo=True, font=("Consolas" if sys.platform.startswith("win") else "Menlo", 11))
        yscroll = ttk.Scrollbar(editor_frame, orient="vertical", command=self.editor.yview)
        xscroll = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.editor.xview)
        self.editor.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.editor.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        body.add(editor_frame, weight=4)

    def _build_services_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Services")
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        cols = ("scheme", "name", "uri", "scope", "enabled")
        self.services_tree = ttk.Treeview(tab, columns=cols, show="headings")
        for col in cols:
            self.services_tree.heading(col, text=col)
            self.services_tree.column(col, width=160 if col != "uri" else 440)
        self.services_tree.grid(row=0, column=0, sticky="nsew")
        controls = ttk.Frame(tab)
        controls.grid(row=1, column=0, sticky="ew", pady=8)
        self.service_name = tk.StringVar()
        self.service_uri = tk.StringVar(value="mcp://filesystem/list")
        self.service_scope = tk.StringVar(value="private")
        ttk.Entry(controls, textvariable=self.service_name, width=24).pack(side="left", padx=(0, 6))
        ttk.Entry(controls, textvariable=self.service_uri, width=52).pack(side="left", padx=(0, 6))
        ttk.Combobox(controls, textvariable=self.service_scope, values=["private", "shared", "public"], width=10).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Add service", command=self.add_service).pack(side="left")
        self._refresh_services()

    def _build_network_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Sieć lokalna")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(4, weight=1)
        self.port_var = tk.IntVar(value=int(self.workspace.get("node", {}).get("port", DEFAULT_PORT)))
        top = ttk.Frame(tab)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Label(top, text="Port").pack(side="left")
        ttk.Entry(top, textvariable=self.port_var, width=8).pack(side="left", padx=8)
        ttk.Button(top, text="Start runtime", command=self.start_runtime).pack(side="left")
        ttk.Button(top, text="Stop", command=self.stop_runtime).pack(side="left", padx=6)
        ttk.Button(top, text="Skanuj LAN", command=self.discover_peers).pack(side="left")
        self.runtime_status = tk.StringVar(value="Runtime stopped")
        self.scan_status = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.runtime_status).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Label(tab, textvariable=self.scan_status).grid(row=2, column=0, sticky="w")

        ttk.Label(tab, text="Urządzenia (ifURI / urisys-node)").grid(row=3, column=0, sticky="w", pady=(8, 0))
        dev_cols = ("kind", "name", "endpoint", "detail")
        self.device_tree = ttk.Treeview(tab, columns=dev_cols, show="headings", height=6)
        for col, w in zip(dev_cols, (90, 140, 220, 160)):
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=w)
        self.device_tree.grid(row=4, column=0, sticky="nsew", pady=4)
        self.device_tree.bind("<<TreeviewSelect>>", self._on_device_select)

        ttk.Label(tab, text="MCP · agent · LLM").grid(row=5, column=0, sticky="w", pady=(8, 0))
        svc_cols = ("scheme", "name", "uri", "source")
        self.lan_services_tree = ttk.Treeview(tab, columns=svc_cols, show="headings", height=5)
        for col in svc_cols:
            self.lan_services_tree.heading(col, text=col)
            self.lan_services_tree.column(col, width=150)
        self.lan_services_tree.grid(row=6, column=0, sticky="nsew", pady=4)

        peer_cols = ("name", "address", "api_port", "schemes")
        self.peer_tree = ttk.Treeview(tab, columns=peer_cols, show="headings", height=4)
        for col in peer_cols:
            self.peer_tree.heading(col, text=col)
            self.peer_tree.column(col, width=140)
        self.peer_tree.grid(row=7, column=0, sticky="nsew", pady=4)
        self._last_scan: dict[str, Any] = {}
        self._refresh_peers()

    def _build_events_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Run log")
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        self.log_text = tk.Text(tab, wrap="word", font=("Consolas" if sys.platform.startswith("win") else "Menlo", 10))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        ttk.Button(tab, text="Refresh", command=self.refresh_log).grid(row=1, column=0, sticky="e", pady=8)
        self.refresh_log()

    def _groups(self) -> list[dict[str, Any]]:
        return self.workspace.setdefault("groups", [])

    def _flows(self) -> list[dict[str, Any]]:
        groups = self._groups()
        if not groups:
            return []
        return groups[self.current_group_index].setdefault("flows", [])

    def _load_groups(self) -> None:
        self.group_list.delete(0, tk.END)
        for group in self._groups():
            self.group_list.insert(tk.END, group.get("name") or group.get("id") or "group")
        if self._groups():
            self.group_list.selection_set(0)
            self._load_flows()

    def _load_flows(self) -> None:
        self.flow_list.delete(0, tk.END)
        for flow in self._flows():
            self.flow_list.insert(tk.END, flow.get("name") or flow.get("id") or "flow")
        if self._flows():
            self.flow_list.selection_clear(0, tk.END)
            self.flow_list.selection_set(0)
            self.current_flow_index = 0
            self._load_current_flow_text()
        else:
            self.editor.delete("1.0", tk.END)

    def _load_current_flow_text(self) -> None:
        flows = self._flows()
        self.editor.delete("1.0", tk.END)
        if flows:
            self.editor.insert("1.0", flows[self.current_flow_index].get("text", ""))

    def _on_group_select(self) -> None:
        sel = self.group_list.curselection()
        if not sel:
            return
        self.current_group_index = int(sel[0])
        self.current_flow_index = 0
        self._load_flows()

    def _on_flow_select(self) -> None:
        sel = self.flow_list.curselection()
        if not sel:
            return
        self.current_flow_index = int(sel[0])
        self._load_current_flow_text()

    def new_group(self) -> None:
        name = simpledialog.askstring("New group", "Group name:", parent=self)
        if not name:
            return
        gid = name.lower().replace(" ", "-")
        self._groups().append({"id": gid, "name": name, "description": "", "flows": []})
        self.save_all()
        self._load_groups()

    def new_flow(self) -> None:
        if not self._groups():
            self.new_group()
        name = simpledialog.askstring("New flow", "Flow name:", parent=self)
        if not name:
            return
        fid = name.lower().replace(" ", "-")
        text = f"flow:\n  id: {fid}\n  group: {self._groups()[self.current_group_index]['id']}\n\ndo:\n  - mcp://filesystem/list:\n      path: ./\n  - llm://local/qwen/analyze\n"
        self._flows().append({"id": fid, "name": name, "filename": f"{fid}.uri.flow.yaml", "text": text})
        self.current_flow_index = len(self._flows()) - 1
        self.save_all()
        self._load_flows()

    def save_current_flow(self) -> None:
        flows = self._flows()
        if not flows:
            return
        flows[self.current_flow_index]["text"] = self.editor.get("1.0", tk.END).rstrip() + "\n"
        add_event(self.workspace, "flow.saved", flow=flows[self.current_flow_index].get("id"))
        self.save_all()
        self.append_log("Saved flow")

    def dry_run_current_flow(self) -> None:
        self.save_current_flow()
        text = self.editor.get("1.0", tk.END)
        result = dry_run_flow(text)
        add_event(self.workspace, "flow.dry_run", steps=len(result.get("steps", [])))
        save_workspace(self.workspace)
        self.append_log(as_pretty_json(result))
        self.notebook.select(self.notebook.index(self.notebook.tabs()[-1]))

    def _refresh_services(self) -> None:
        if not hasattr(self, "services_tree"):
            return
        self.services_tree.delete(*self.services_tree.get_children())
        for service in self.workspace.get("services", []):
            self.services_tree.insert("", tk.END, values=(service.get("scheme"), service.get("name"), service.get("uri"), service.get("scope"), service.get("enabled", True)))

    def add_service(self) -> None:
        uri = self.service_uri.get().strip()
        if "://" not in uri:
            messagebox.showerror("Invalid URI", "Service URI must contain ://")
            return
        scheme = uri.split("://", 1)[0]
        service = {"name": self.service_name.get().strip() or uri, "scheme": scheme, "uri": uri, "scope": self.service_scope.get(), "enabled": True}
        self.workspace.setdefault("services", []).append(service)
        add_event(self.workspace, "service.added", uri=uri)
        self.save_all()
        self._refresh_services()

    def start_runtime(self) -> None:
        if self.runtime:
            self.runtime_status.set(f"Runtime already running: {self.runtime.url}")
            return
        port = int(self.port_var.get())
        try:
            self.runtime = RuntimeServer("0.0.0.0", port).start()
            self.discovery_responder = DiscoveryResponder(api_port=port).start()
        except PortInUseError as exc:
            self.runtime = None
            messagebox.showerror("Runtime error", str(exc))
            return
        except OSError as exc:
            self.runtime = None
            messagebox.showerror("Runtime error", str(exc))
            return
        self.runtime_status.set(f"Runtime running: http://127.0.0.1:{port} · discovery UDP enabled")
        self.append_log(f"Runtime started on port {port}")

    def stop_runtime(self) -> None:
        if self.discovery_responder:
            self.discovery_responder.stop()
            self.discovery_responder = None
        if self.runtime:
            self.runtime.stop()
            self.runtime = None
        self.runtime_status.set("Runtime stopped")
        self.append_log("Runtime stopped")

    def discover_peers(self) -> None:
        self.scan_status.set("Skanowanie LAN…")
        self.update_idletasks()
        result = scan_network(timeout=1.5, scan_subnet=True)
        self._last_scan = result
        self.workspace = load_workspace()
        counts = result.get("counts") or {}
        self.scan_status.set(
            f"ifURI: {counts.get('ifuri_peers', 0)} · urisys-node: {counts.get('urisys_nodes', 0)} · MCP/agent: {counts.get('mcp_agent', 0)}"
        )
        self._refresh_network_views(result)
        self.append_log(as_pretty_json({"scan": counts}))

    def _refresh_network_views(self, scan: dict[str, Any] | None = None) -> None:
        scan = scan or self._last_scan
        if hasattr(self, "device_tree"):
            self.device_tree.delete(*self.device_tree.get_children())
            for node in scan.get("urisys_nodes") or []:
                self.device_tree.insert(
                    "",
                    tk.END,
                    values=(
                        "urisys-node",
                        node.get("node_id") or node.get("host"),
                        node.get("endpoint"),
                        f"routes={node.get('routes_count', '?')}",
                    ),
                )
            for peer in scan.get("ifuri_peers") or []:
                url = peer.get("api_url") or f"http://{peer.get('address')}:{peer.get('api_port', 8765)}"
                self.device_tree.insert(
                    "",
                    tk.END,
                    values=("ifuri", peer.get("name") or peer.get("id"), url, ",".join(peer.get("schemes") or [])),
                )
        if hasattr(self, "lan_services_tree"):
            self.lan_services_tree.delete(*self.lan_services_tree.get_children())
            for svc in (scan.get("mcp_agent_services") or []) + (scan.get("llm_services") or []):
                self.lan_services_tree.insert(
                    "",
                    tk.END,
                    values=(svc.get("scheme"), svc.get("name"), svc.get("uri"), svc.get("source")),
                )
        self._refresh_peers()

    def _on_device_select(self, _event=None) -> None:
        sel = self.device_tree.selection()
        if not sel:
            return
        vals = self.device_tree.item(sel[0], "values")
        if len(vals) >= 3 and vals[0] == "urisys-node":
            self.workspace.setdefault("urisys", {})["endpoint"] = vals[2]
            save_workspace(self.workspace)

    def _refresh_peers(self) -> None:
        if not hasattr(self, "peer_tree"):
            return
        self.peer_tree.delete(*self.peer_tree.get_children())
        peers = (self._last_scan.get("ifuri_peers") if self._last_scan else None) or self.workspace.get("peers", [])
        for peer in peers:
            self.peer_tree.insert(
                "",
                tk.END,
                values=(
                    peer.get("name"),
                    peer.get("address"),
                    peer.get("api_port"),
                    ", ".join(peer.get("schemes", [])),
                ),
            )

    def refresh_log(self) -> None:
        self.workspace = load_workspace()
        self.log_text.delete("1.0", tk.END)
        for event in self.workspace.get("events", [])[-80:]:
            self.log_text.insert(tk.END, json.dumps(event, ensure_ascii=False) + "\n")

    def append_log(self, text: str) -> None:
        self.log_text.insert(tk.END, text.rstrip() + "\n")
        self.log_text.see(tk.END)

    def save_all(self) -> None:
        save_workspace(self.workspace)

    def _on_close(self) -> None:
        self.save_all()
        self.stop_runtime()
        self.destroy()


def launch_gui() -> None:
    app = IfuriDesktop()
    app.mainloop()
