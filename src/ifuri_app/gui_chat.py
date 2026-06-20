# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Desktop chat tab — each :8790 / MCP / A2A endpoint as a thread."""

from __future__ import annotations

import threading
import tkinter as tk
import webbrowser
from tkinter import ttk
from typing import Any, TYPE_CHECKING

from .chat_channels import fetch_chat_history, list_chat_channels, send_chat_message_routed
from .storage import load_workspace, save_workspace
from .url_params import voice_url

if TYPE_CHECKING:
    from .gui import IfuriDesktop

GROUP_LABELS = {
    "node": "node :8790",
    "mcp": "MCP",
    "a2a": "A2A",
    "llm": "LLM",
    "ifuri": "ifURI",
}


class ChatTabMixin:
    """Mixin for IfuriDesktop — call _build_chat_tab() from _build_ui."""

    _chat_channels: list[dict[str, Any]]
    _chat_active: dict[str, Any] | None
    _chat_threads: dict[str, list[tuple[str, str]]]
    _chat_channel_map: dict[str, dict[str, Any]]

    def _build_chat_tab(self: IfuriDesktop) -> None:
        self._chat_channels = []
        self._chat_active = None
        self._chat_threads = {}
        self._chat_channel_map = {}

        tab = ttk.Frame(self.notebook, padding=8)
        # Chat is built first into an empty notebook, so it is already index 0;
        # insert(0, ...) raises "Slave index 0 out of bounds" on Tk 8.6.15+.
        self.notebook.add(tab, text="Czaty")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        left = ttk.Frame(tab, width=260)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        left.rowconfigure(1, weight=1)

        head = ttk.Frame(left)
        head.pack(fill="x")
        ttk.Label(head, text="Endpointy", font=("TkDefaultFont", 11, "bold")).pack(side="left")
        ttk.Button(head, text="↻", width=3, command=self._refresh_chat_channels).pack(side="right")

        self.chat_scan_status = tk.StringVar(value="Skanuj LAN…")
        ttk.Label(left, textvariable=self.chat_scan_status, foreground="#5d6d7e").pack(anchor="w", pady=(4, 6))

        self.chat_channel_list = tk.Listbox(left, exportselection=False, font=("TkDefaultFont", 10))
        self.chat_channel_list.pack(fill="both", expand=True)
        self.chat_channel_list.bind("<<ListboxSelect>>", self._on_chat_channel_select)

        right = ttk.Frame(tab)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.chat_header = tk.StringVar(value="Wybierz czat z listy")
        ttk.Label(right, textvariable=self.chat_header, font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, sticky="w")

        self.chat_log = tk.Text(
            right,
            wrap="word",
            state="disabled",
            font=("Menlo", 10),
            background="#0f1419",
            foreground="#e8eef4",
        )
        self.chat_log.grid(row=1, column=0, sticky="nsew", pady=(6, 6))

        composer = ttk.Frame(right)
        composer.grid(row=2, column=0, sticky="ew")
        composer.columnconfigure(0, weight=1)

        self.chat_input = tk.Text(composer, height=3, wrap="word", font=("TkDefaultFont", 11))
        self.chat_input.grid(row=0, column=0, sticky="ew")
        self.chat_input.bind("<Control-Return>", lambda _e: (self._send_chat_message(), "break"))
        self.chat_input.bind("<KeyRelease>", lambda _e: self._sync_chat_prompt_url())

        bar = ttk.Frame(composer)
        bar.grid(row=1, column=0, sticky="e", pady=(6, 0))
        self.chat_dry_run = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text="dry-run", variable=self.chat_dry_run, command=self._sync_chat_prompt_url).pack(side="left", padx=(0, 8))
        ttk.Button(bar, text="Web ↗", command=self._open_chat_in_browser).pack(side="left", padx=(0, 8))
        ttk.Button(bar, text="Wyślij", command=self._send_chat_message).pack(side="left")

        self._chat_voice_url = tk.StringVar(value="")
        ttk.Entry(composer, textvariable=self._chat_voice_url, state="readonly").grid(row=2, column=0, sticky="ew", pady=(6, 0))

        self.after(400, self._refresh_chat_channels)

    def _router_endpoint(self: IfuriDesktop) -> str | None:
        for ch in self._chat_channels:
            if ch.get("type") == "urisys-node" and ch.get("endpoint"):
                return str(ch["endpoint"])
        ws = load_workspace()
        ep = (ws.get("urisys") or {}).get("endpoint")
        return str(ep).rstrip("/") if ep else None

    def _runtime_base_url(self: IfuriDesktop) -> str:
        if getattr(self, "runtime", None):
            return self.runtime.url.rstrip("/")
        port = int(self.port_var.get()) if hasattr(self, "port_var") else 8765
        return f"http://127.0.0.1:{port}"

    def _chat_prompt_text(self: IfuriDesktop) -> str:
        return self.chat_input.get("1.0", tk.END).strip()

    def _sync_chat_prompt_url(self: IfuriDesktop) -> None:
        prompt = self._chat_prompt_text()
        channel_id = self._chat_active.get("id") if self._chat_active else None
        url = voice_url(
            self._runtime_base_url(),
            lang="pl",
            theme="dark",
            view="chat",
            channel=channel_id,
            prompt=prompt or None,
            dry_run="1" if self.chat_dry_run.get() else None,
        )
        self._chat_voice_url.set(url)

    def _open_chat_in_browser(self: IfuriDesktop) -> None:
        self._sync_chat_prompt_url()
        url = self._chat_voice_url.get()
        if url:
            webbrowser.open(url)

    def _refresh_chat_channels(self: IfuriDesktop) -> None:
        self.chat_scan_status.set("Skan LAN…")
        self.update_idletasks()

        def worker() -> None:
            try:
                data = list_chat_channels(timeout=1.8)
                self.after(0, lambda: self._apply_chat_channels(data))
            except Exception as exc:
                self.after(0, lambda: self.chat_scan_status.set(f"Błąd skanu: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_chat_channels(self: IfuriDesktop, data: dict[str, Any]) -> None:
        self._chat_channels = data.get("channels") or []
        self._chat_channel_map.clear()
        self.chat_channel_list.delete(0, tk.END)

        groups = data.get("groups") or {}
        for key in ("node", "mcp", "a2a", "llm", "ifuri"):
            for ch in groups.get(key) or []:
                label = f"[{GROUP_LABELS.get(key, key)}] {ch.get('title', '?')}"
                self.chat_channel_list.insert(tk.END, label)
                self._chat_channel_map[label] = ch

        counts = data.get("counts") or {}
        self.chat_scan_status.set(
            f"{counts.get('urisys_nodes', 0)} node · {counts.get('mcp_agent', 0)} MCP/A2A · {counts.get('ifuri_peers', 0)} peer"
        )

        if self._chat_channels and self.chat_channel_list.size() and not self._chat_active:
            self.chat_channel_list.selection_set(0)
            self._on_chat_channel_select()

        self._refresh_network_views(
            {
                "urisys_nodes": [n for n in self._chat_channels if n.get("type") == "urisys-node"],
                "ifuri_peers": [],
                "mcp_agent_services": [c for c in self._chat_channels if c.get("kind") in {"mcp", "a2a"}],
                "llm_services": [c for c in self._chat_channels if c.get("kind") == "llm"],
            }
        )

    def _on_chat_channel_select(self: IfuriDesktop, _event=None) -> None:
        sel = self.chat_channel_list.curselection()
        if not sel:
            return
        label = self.chat_channel_list.get(sel[0])
        ch = self._chat_channel_map.get(label)
        if not ch:
            return
        self._chat_active = ch
        self.chat_header.set(f"{ch.get('title')} — {ch.get('subtitle', '')}")
        if ch.get("type") == "urisys-node" and ch.get("endpoint"):
            self.workspace.setdefault("urisys", {})["endpoint"] = ch["endpoint"]
            save_workspace(self.workspace)
        self._load_chat_history_from_urisys(ch)
        self._sync_chat_prompt_url()

    def _load_chat_history_from_urisys(self: IfuriDesktop, ch: dict[str, Any]) -> None:
        self.chat_log.configure(state="normal")
        self.chat_log.delete("1.0", tk.END)
        self.chat_log.insert(tk.END, "Ładowanie historii z urisys-node…\n")
        self.chat_log.configure(state="disabled")

        def worker() -> None:
            try:
                data = fetch_chat_history(
                    str(ch.get("id") or ""),
                    router_endpoint=self._router_endpoint(),
                    channel=ch,
                )
                rows = [
                    (str(m.get("role") or "assistant"), str(m.get("text") or ""))
                    for m in (data.get("messages") or [])
                ]
            except Exception as exc:
                rows = [("assistant", f"Historia niedostępna: {exc}")]
            self.after(0, lambda: self._apply_chat_history(ch["id"], rows))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_chat_history(self: IfuriDesktop, channel_id: str, rows: list[tuple[str, str]]) -> None:
        self._chat_threads[channel_id] = rows[-100:]
        if self._chat_active and self._chat_active.get("id") == channel_id:
            self._render_chat_thread()

    def _render_chat_thread(self: IfuriDesktop) -> None:
        self.chat_log.configure(state="normal")
        self.chat_log.delete("1.0", tk.END)
        if not self._chat_active:
            self.chat_log.configure(state="disabled")
            return
        thread = self._chat_threads.get(self._chat_active["id"], [])
        for role, text in thread:
            prefix = "Ty" if role == "user" else self._chat_active.get("title", "bot")
            self.chat_log.insert(tk.END, f"{prefix}\n", "meta")
            self.chat_log.insert(tk.END, f"{text}\n\n")
        self.chat_log.see(tk.END)
        self.chat_log.configure(state="disabled")

    def _append_chat(self: IfuriDesktop, role: str, text: str) -> None:
        if not self._chat_active:
            return
        cid = self._chat_active["id"]
        self._chat_threads.setdefault(cid, []).append((role, text))
        if len(self._chat_threads[cid]) > 100:
            self._chat_threads[cid] = self._chat_threads[cid][-100:]
        self._render_chat_thread()

    def _send_chat_message(self: IfuriDesktop) -> None:
        if not self._chat_active:
            return
        text = self.chat_input.get("1.0", tk.END).strip()
        if not text:
            return
        self.chat_input.delete("1.0", tk.END)
        self._sync_chat_prompt_url()
        channel = dict(self._chat_active)
        dry = self.chat_dry_run.get()
        router = self._router_endpoint()

        self._append_chat("user", text)
        self._append_chat("assistant", "…")

        def worker() -> None:
            try:
                result = send_chat_message_routed(
                    channel,
                    text,
                    router_endpoint=router,
                    dry_run=dry,
                )
                reply = result.get("text") or result.get("error") or str(result)
            except Exception as exc:
                reply = f"Błąd: {exc}"
            self.after(0, lambda: self._finish_chat_reply(channel, reply))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_chat_reply(self: IfuriDesktop, channel: dict[str, Any], reply: str) -> None:
        if not self._chat_active or self._chat_active.get("id") != channel.get("id"):
            return
        cid = self._chat_active["id"]
        thread = self._chat_threads.get(cid, [])
        if thread and thread[-1] == ("assistant", "…"):
            thread.pop()
        self._append_chat("assistant", reply)
        self.append_log(f"chat [{self._chat_active.get('title')}]: {reply[:120]}")
        self._load_chat_history_from_urisys(self._chat_active)
