const U = () => window.IfuriUrlState;
const T = () => window.IfuriTheme;

const I18N = {
  pl: {
    pickChat: "Wybierz czat",
    emptyList: "Brak endpointów — uruchom urisys-node :8790 lub ifuri-app serve w LAN.",
    emptyThread: "Każdy urisys-node :8790, MCP, A2A i peer ifURI to osobny czat.",
    newThread: "Nowy czat z",
    sendHint: "Wyślij polecenie lub pytanie.",
    placeholder: "Wiadomość do endpointu…",
    send: "Wyślij",
    scan: "Skan LAN…",
    scanFail: "Skan nieudany",
    viewChat: "Czat",
    viewScreen: "Ekran",
    you: "Ty",
    loadingHistory: "Ładowanie historii…",
    historyFail: "Nie udało się wczytać historii z urisys-node",
    speechMissing: "Web Speech API niedostępne — wpisz tekst ręcznie.",
  },
  en: {
    pickChat: "Pick a chat",
    emptyList: "No endpoints — start urisys-node :8790 or ifuri-app serve on LAN.",
    emptyThread: "Each urisys-node :8790, MCP, A2A and ifURI peer is its own chat.",
    newThread: "New chat with",
    sendHint: "Send a command or question.",
    placeholder: "Message to endpoint…",
    send: "Send",
    scan: "Scanning LAN…",
    scanFail: "Scan failed",
    viewChat: "Chat",
    viewScreen: "Screen",
    you: "You",
    loadingHistory: "Loading history…",
    historyFail: "Could not load history from urisys-node",
    speechMissing: "Web Speech API unavailable — type manually.",
  },
};

const chatListEl = document.getElementById("chatList");
const scanStatus = document.getElementById("scanStatus");
const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const btnSend = document.getElementById("btnSend");
const btnListen = document.getElementById("btnListen");
const btnRefresh = document.getElementById("btnRefresh");
const btnScreen = document.getElementById("btnScreen");
const btnViewToggle = document.getElementById("btnViewToggle");
const dryRunEl = document.getElementById("dryRun");
const chatKindEl = document.getElementById("chatKind");
const chatTitleEl = document.getElementById("chatTitle");
const chatSubtitleEl = document.getElementById("chatSubtitle");
const remoteScreenEl = document.getElementById("remoteScreen");
const screenPanel = document.getElementById("screenPanel");
const screenAutoEl = document.getElementById("screenAuto");
const screenAutoWrap = document.getElementById("screenAutoWrap");
const langSelect = document.getElementById("langSelect");
const themeSelect = document.getElementById("themeSelect");

let channels = [];
let activeChannel = null;
let messages = {};
let channelPreviews = {};
let screenTimer = null;
let lang = "pl";
let autoSendPending = false;

const GROUP_LABELS = {
  pl: { node: "urisys-node :8790", mcp: "MCP", a2a: "A2A / agent", llm: "LLM", ifuri: "ifURI peer" },
  en: { node: "urisys-node :8790", mcp: "MCP", a2a: "A2A / agent", llm: "LLM", ifuri: "ifURI peer" },
};

function t(key) {
  return (I18N[lang] || I18N.pl)[key] || key;
}

function syncUrl(params, { replace = false } = {}) {
  U()?.patch(params, { replace });
}

let promptSyncTimer = null;

function syncPromptToUrl({ replace = true } = {}) {
  const prompt = inputEl.value;
  syncUrl({ prompt: prompt || null }, { replace });
}

function applyPromptFromUrl() {
  const prompt = U()?.get("prompt");
  if (prompt !== undefined && document.activeElement !== inputEl) {
    inputEl.value = prompt;
  }
}

function esc(text) {
  const d = document.createElement("div");
  d.textContent = String(text ?? "");
  return d.innerHTML;
}

async function api(path, body) {
  const res = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

function routerEndpoint() {
  const node = channels.find((c) => c.type === "urisys-node");
  return node?.endpoint || localStorage.getItem("ifuri_node") || "";
}

async function loadChannelHistory(channel) {
  if (!channel?.id) return;
  messages[channel.id] = [];
  renderMessages();
  messagesEl.innerHTML = `<p class="empty-hint">${esc(t("loadingHistory"))}</p>`;
  const ep = routerEndpoint();
  const qs = new URLSearchParams({ channel_id: channel.id });
  if (ep) qs.set("endpoint", ep);
  try {
    const data = await api(`/api/chat/history?${qs.toString()}`);
    messages[channel.id] = (data.messages || []).map((m) => ({
      role: m.role,
      text: m.text,
      meta: m.meta || null,
      at: m.at,
    }));
    if (messages[channel.id].length) {
      const last = messages[channel.id][messages[channel.id].length - 1];
      channelPreviews[channel.id] = { text: last.text, at: last.at };
    }
  } catch {
    messages[channel.id] = [];
    messagesEl.innerHTML = `<p class="empty-hint">${esc(t("historyFail"))}</p>`;
  }
  renderMessages();
  maybeAutoSendFromUrl();
}

function maybeAutoSendFromUrl() {
  const prompt = (U()?.get("prompt") || "").trim();
  if (!prompt || !activeChannel || autoSendPending) return;
  if (U()?.get("action") !== "send") return;
  autoSendPending = true;
  inputEl.value = prompt;
  sendMessage();
}

function applyUiLanguage() {
  inputEl.placeholder = t("placeholder");
  btnSend.textContent = t("send");
  chatTitleEl.textContent = activeChannel ? activeChannel.title : t("pickChat");
}

function applyViewFromUrl() {
  const view = U()?.get("view", "chat");
  const showScreen = view === "screen";
  if (activeChannel?.type === "urisys-node") {
    screenPanel.hidden = !showScreen;
    btnViewToggle.hidden = false;
    btnScreen.hidden = false;
    screenAutoWrap.hidden = false;
    updateViewToggleLabel();
    if (showScreen) refreshScreen();
  } else {
    btnViewToggle.hidden = true;
  }
  const dry = U()?.get("dry_run", "0") === "1";
  dryRunEl.checked = dry;
  const auto = U()?.get("screen_auto", "0") === "1";
  screenAutoEl.checked = auto;
  setScreenAuto(auto, { replace: true });
}

function updateViewToggleLabel() {
  if (!btnViewToggle) return;
  const onScreen = U()?.get("view", "chat") === "screen";
  btnViewToggle.textContent = onScreen ? t("viewChat") : t("viewScreen");
  btnViewToggle.setAttribute("aria-pressed", onScreen ? "true" : "false");
}

function toggleView() {
  if (!activeChannel || activeChannel.type !== "urisys-node") return;
  if (window.IfuriPageRuntime) {
    window.IfuriPageRuntime.call("page://voice/view/command/toggle", {}, { approved: true }).catch(() => {
      _toggleViewDirect();
    });
    return;
  }
  _toggleViewDirect();
}

function _toggleViewDirect() {
  const next = U()?.get("view", "chat") === "screen" ? "chat" : "screen";
  syncUrl({ view: next }, { replace: false });
  applyViewFromUrl();
}

function appendMessage(channelId, role, text, meta, { render = true } = {}) {
  if (!messages[channelId]) messages[channelId] = [];
  messages[channelId].push({ role, text, meta: meta || null, at: new Date().toISOString() });
  if (messages[channelId].length > 200) messages[channelId] = messages[channelId].slice(-200);
  channelPreviews[channelId] = { text, at: new Date().toISOString() };
  if (render && activeChannel?.id === channelId) renderMessages();
}

function renderMessages() {
  messagesEl.innerHTML = "";
  if (!activeChannel) {
    messagesEl.innerHTML = `<p class="empty-hint">${esc(t("emptyThread"))}</p>`;
    return;
  }
  const thread = messages[activeChannel.id] || [];
  if (!thread.length) {
    messagesEl.innerHTML = `<p class="empty-hint">${esc(t("newThread"))} <strong>${esc(activeChannel.title)}</strong>. ${esc(t("sendHint"))}</p>`;
    return;
  }
  for (const msg of thread) {
    const div = document.createElement("div");
    div.className = `msg msg-${msg.role}`;
    const time = msg.at ? new Date(msg.at).toLocaleTimeString(lang === "en" ? "en-GB" : "pl-PL", { hour: "2-digit", minute: "2-digit" }) : "";
    div.innerHTML = `<div class="msg-meta">${msg.role === "user" ? esc(t("you")) : esc(activeChannel.title)} · ${time}</div><pre class="msg-body">${esc(msg.text)}</pre>`;
    messagesEl.appendChild(div);
  }
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function selectChannel(ch, { replace = false } = {}) {
  activeChannel = ch;
  localStorage.setItem("ifuri_chat_active", ch.id);
  syncUrl({ channel: ch.id, view: U()?.get("view", "chat") }, { replace });

  chatKindEl.textContent = (ch.kind || ch.type || "").toUpperCase();
  chatKindEl.className = `chat-kind kind-${ch.kind || ch.type}`;
  chatTitleEl.textContent = ch.title;
  chatSubtitleEl.textContent = ch.subtitle || "";
  inputEl.disabled = false;
  btnSend.disabled = false;
  btnListen.disabled = false;

  const isNode = ch.type === "urisys-node";
  btnScreen.hidden = !isNode;
  btnViewToggle.hidden = !isNode;
  screenAutoWrap.hidden = !isNode;
  if (isNode) {
    localStorage.setItem("ifuri_node", ch.endpoint);
    applyViewFromUrl();
  } else {
    screenPanel.hidden = true;
    syncUrl({ view: "chat" }, { replace: true });
  }

  document.querySelectorAll(".chat-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.id === ch.id);
  });
  loadChannelHistory(ch);
}

function renderChannelList(data) {
  chatListEl.innerHTML = "";
  const groups = data.groups || {};
  const historyIndex = data.history_index || {};
  const order = ["node", "mcp", "a2a", "llm", "ifuri"];
  const labels = GROUP_LABELS[lang] || GROUP_LABELS.pl;

  for (const key of order) {
    const items = groups[key] || [];
    if (!items.length) continue;
    const section = document.createElement("section");
    section.className = "chat-group";
    section.innerHTML = `<h3>${esc(labels[key] || key)} <span>${items.length}</span></h3>`;
    for (const ch of items) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chat-item";
      btn.dataset.id = ch.id;
      const hist = historyIndex[ch.id] || channelPreviews[ch.id];
      const preview = hist?.preview || (messages[ch.id] || []).slice(-1)[0]?.text;
      btn.innerHTML = `
        <span class="chat-item-kind">${esc(ch.kind)}</span>
        <strong>${esc(ch.title)}</strong>
        <span class="chat-item-sub">${esc(ch.subtitle || "")}</span>
        ${preview ? `<span class="chat-item-preview">${esc(String(preview).slice(0, 60))}</span>` : ""}`;
      btn.onclick = () => selectChannel(ch);
      section.appendChild(btn);
    }
    chatListEl.appendChild(section);
  }

  if (!channels.length) {
    chatListEl.innerHTML = `<p class="empty-hint">${esc(t("emptyList"))}</p>`;
    return;
  }

  const urlChannel = U()?.get("channel");
  const saved = urlChannel || localStorage.getItem("ifuri_chat_active");
  const pick = channels.find((c) => c.id === saved) || channels.find((c) => c.type === "urisys-node") || channels[0];
  if (pick) selectChannel(pick, { replace: !urlChannel });
}

async function refreshChannels() {
  scanStatus.textContent = t("scan");
  syncUrl({ action: "scan" }, { replace: false });
  try {
    const ep = routerEndpoint();
    const qs = ep ? `?timeout=1.8&endpoint=${encodeURIComponent(ep)}` : "?timeout=1.8";
    const data = await api(`/api/chat/channels${qs}`);
    channels = data.channels || [];
    const node = channels.find((c) => c.type === "urisys-node");
    if (node?.endpoint) localStorage.setItem("ifuri_node", node.endpoint);
    const c = data.counts || {};
    scanStatus.textContent = `${c.urisys_nodes ?? 0} node · ${c.mcp_agent ?? 0} MCP/A2A · ${c.ifuri_peers ?? 0} peer`;
    renderChannelList(data);
  } catch (err) {
    scanStatus.textContent = t("scanFail");
    chatListEl.innerHTML = `<p class="empty-hint">${esc(String(err))}</p>`;
  }
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || !activeChannel) return;
  syncUrl({ action: "send", prompt: text }, { replace: false });
  appendMessage(activeChannel.id, "user", text);
  inputEl.value = "";
  syncUrl({ prompt: null }, { replace: true });
  appendMessage(activeChannel.id, "assistant", "…", { pending: true });

  const payload = {
    channel: activeChannel,
    text,
    prompt: text,
    dry_run: dryRunEl.checked,
    router_endpoint: routerEndpoint(),
  };
  if (activeChannel.type === "urisys-node") payload.endpoint = activeChannel.endpoint;

  try {
    const data = await api("/api/chat/send", payload);
    messages[activeChannel.id].pop();
    appendMessage(activeChannel.id, "assistant", data.text || data.error || JSON.stringify(data, null, 2), data);
    await loadChannelHistory(activeChannel);
  } catch (err) {
    messages[activeChannel.id].pop();
    appendMessage(activeChannel.id, "assistant", `Błąd: ${err}`, { error: true });
  }
}

function screenImageUrl() {
  if (!activeChannel || activeChannel.type !== "urisys-node") return "";
  const ep = encodeURIComponent(activeChannel.endpoint);
  const nodeId = encodeURIComponent(activeChannel.node_id || "lenovo");
  return `/api/urisys/screen.png?endpoint=${ep}&node_id=${nodeId}&source=screen&monitor=1&_=${Date.now()}`;
}

async function refreshScreen() {
  syncUrl({ view: "screen", action: "screenshot" }, { replace: false });
  const url = screenImageUrl();
  if (!url) return;
  try {
    const res = await fetch(url);
    if (!res.ok) return;
    const blob = await res.blob();
    remoteScreenEl.src = URL.createObjectURL(blob);
    screenPanel.hidden = false;
  } catch {
    /* ignore */
  }
}

function setScreenAuto(on, { replace = false } = {}) {
  if (screenTimer) clearInterval(screenTimer);
  screenTimer = null;
  if (on) screenTimer = setInterval(refreshScreen, 3000);
  syncUrl({ screen_auto: on ? "1" : "0" }, { replace });
}

function initSettingsFromUrl() {
  const prefs = T()?.initFromUrl() || { lang: "pl", theme: "dark" };
  lang = prefs.lang;
  langSelect.value = lang;
  themeSelect.value = prefs.theme;
  applyUiLanguage();
}

langSelect.addEventListener("change", () => {
  lang = langSelect.value;
  T()?.setLang(lang);
  applyUiLanguage();
  renderChannelList({ groups: groupChannels(channels) });
  renderMessages();
});

themeSelect.addEventListener("change", () => {
  T()?.setTheme(themeSelect.value);
});

function groupChannels(list) {
  const groups = { node: [], mcp: [], a2a: [], llm: [], ifuri: [] };
  for (const ch of list) groups[ch.kind]?.push(ch);
  return groups;
}

btnRefresh.onclick = refreshChannels;
btnSend.onclick = sendMessage;
btnScreen.onclick = refreshScreen;
btnViewToggle.onclick = toggleView;
screenAutoEl.addEventListener("change", () => setScreenAuto(screenAutoEl.checked));
dryRunEl.addEventListener("change", () => syncUrl({ dry_run: dryRunEl.checked ? "1" : "0" }));

inputEl.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && !ev.shiftKey) {
    ev.preventDefault();
    sendMessage();
  }
});

inputEl.addEventListener("input", () => {
  clearTimeout(promptSyncTimer);
  promptSyncTimer = setTimeout(() => syncPromptToUrl({ replace: true }), 150);
});

btnListen.onclick = () => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR || !activeChannel) {
    if (activeChannel) appendMessage(activeChannel.id, "assistant", t("speechMissing"));
    return;
  }
  const rec = new SR();
  rec.lang = lang === "en" ? "en-US" : "pl-PL";
  rec.onresult = (ev) => {
    inputEl.value = ev.results[0][0].transcript;
    syncPromptToUrl({ replace: true });
  };
  rec.start();
};

U()?.onPopState(() => {
  initSettingsFromUrl();
  applyPromptFromUrl();
  const cid = U()?.get("channel");
  if (cid && channels.length) {
    const ch = channels.find((c) => c.id === cid);
    if (ch) selectChannel(ch, { replace: true });
  }
  applyViewFromUrl();
});

initSettingsFromUrl();
applyPromptFromUrl();
U()?.patch(
  {
    lang: U().get("lang", "pl"),
    theme: U().get("theme", "dark"),
    view: U().get("view", "chat"),
    prompt: U().get("prompt") || null,
  },
  { replace: true }
);
refreshChannels();
window.ifuriApplyView = applyViewFromUrl;
