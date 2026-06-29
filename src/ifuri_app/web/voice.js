// Author: Tom Sapletta · https://tom.sapletta.com
// Part of the ifURI solution.

const U = () => window.IfuriUrlState;
const T = () => window.IfuriTheme;
const I = () => window.IfuriI18n;

const chatListEl = document.getElementById("chatList");
const scanStatus = document.getElementById("scanStatus");
const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const btnSend = document.getElementById("btnSend");
const btnListen = document.getElementById("btnListen");
const btnRefresh = document.getElementById("btnRefresh");
const btnScreen = document.getElementById("btnScreen");
const btnViewToggle = document.getElementById("btnViewToggle");
const btnWebRtcConnect = document.getElementById("btnWebRtcConnect");
const webrtcStatusEl = document.getElementById("webrtcStatus");
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
const dryRunLabel = document.getElementById("dryRunLabel");
const screenAutoLabel = document.getElementById("screenAutoLabel");
const voicePackBanner = document.getElementById("voicePackBanner");
const voicePackText = document.getElementById("voicePackText");
const btnInstallVoicePacks = document.getElementById("btnInstallVoicePacks");
const webrtcRemoteAudio = document.getElementById("webrtcRemoteAudio");

let channels = [];
let activeChannel = null;
let messages = {};
let channelPreviews = {};
let screenTimer = null;
let lang = "pl";
let autoSendPending = false;
let lastChannelData = null;
let localApiUrl = null;
let webrtcSession = null;

function t(key, ...args) {
  return I()?.t(lang, key, ...args) ?? key;
}

function groupLabels() {
  return I()?.groupLabels(lang) || {};
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
  document.documentElement.lang = lang === "en" ? "en" : "pl";
  document.title = t("title");
  btnRefresh.title = t("refreshTitle");
  chatListEl.setAttribute("aria-label", t("sidebarAria"));
  langSelect.setAttribute("aria-label", t("langAria"));
  themeSelect.setAttribute("aria-label", t("themeAria"));
  btnListen.title = t("listenTitle");
  inputEl.placeholder = t("placeholder");
  btnSend.textContent = t("send");
  btnScreen.textContent = t("screenshot");
  if (dryRunLabel) dryRunLabel.textContent = t("dryRun");
  if (screenAutoLabel) screenAutoLabel.textContent = t("screenAuto");
  remoteScreenEl.alt = t("screenAlt");
  if (btnInstallVoicePacks) btnInstallVoicePacks.textContent = t("voicePackInstall");
  chatTitleEl.textContent = activeChannel ? activeChannel.title : t("pickChat");
  if (!activeChannel && messagesEl) {
    messagesEl.innerHTML = `<p class="empty-hint">${esc(t("emptyThread"))}</p>`;
  }
  updateViewToggleLabel();
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
  const isWebRtc = ch.type === "webrtc-peer";
  btnScreen.hidden = !isNode;
  btnViewToggle.hidden = !isNode;
  screenAutoWrap.hidden = !isNode;
  if (btnWebRtcConnect) {
    btnWebRtcConnect.hidden = !isWebRtc;
    btnWebRtcConnect.textContent = webrtcSession ? t("webrtcDisconnect") : t("webrtcConnect");
  }
  if (webrtcStatusEl) webrtcStatusEl.hidden = !isWebRtc;
  if (isWebRtc && webrtcSession) {
    /* keep session across channel re-select */
  } else if (!isWebRtc && webrtcSession) {
    disconnectWebRtc();
  }
  if (isNode) {
    localStorage.setItem("ifuri_node", ch.endpoint);
    applyViewFromUrl();
    refreshVoiceCapabilities(ch.endpoint);
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
  const order = ["node", "mcp", "a2a", "llm", "ifuri", "webrtc"];
  const labels = groupLabels();

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

async function refreshVoiceCapabilities(endpoint) {
  if (!endpoint || !voicePackBanner) return;
  try {
    const qs = new URLSearchParams({ endpoint });
    const data = await api(`/api/voice/capabilities?${qs}`);
    const hint = data.voice_pack_hint || {};
    const caps = data.capabilities || {};
    if (hint.needed) {
      voicePackText.textContent = t("voicePackBanner");
      voicePackBanner.hidden = false;
      voicePackBanner.classList.remove("ok");
      if (btnInstallVoicePacks) btnInstallVoicePacks.disabled = false;
    } else {
      voicePackBanner.hidden = true;
    }
  } catch {
    voicePackBanner.hidden = true;
  }
}

async function installVoicePacks() {
  const ep = activeChannel?.endpoint || routerEndpoint();
  if (!ep || !btnInstallVoicePacks) return;
  btnInstallVoicePacks.disabled = true;
  btnInstallVoicePacks.textContent = t("voicePackInstalling");
  try {
    const data = await api("/api/voice/install-packs", { endpoint: ep, dry_run: dryRunEl.checked });
    if (data.ok && !(data.voice_pack_hint || {}).needed) {
      voicePackText.textContent = t("voicePackDone");
      voicePackBanner.classList.add("ok");
      voicePackBanner.hidden = false;
      setTimeout(() => { voicePackBanner.hidden = true; }, 4000);
    } else {
      voicePackText.textContent = t("voicePackFail");
      voicePackBanner.hidden = false;
    }
    await refreshVoiceCapabilities(ep);
  } catch (err) {
    voicePackText.textContent = `${t("voicePackFail")} ${err}`;
    voicePackBanner.hidden = false;
  } finally {
    btnInstallVoicePacks.textContent = t("voicePackInstall");
    btnInstallVoicePacks.disabled = false;
  }
}

async function refreshChannels() {
  scanStatus.textContent = t("scan");
  syncUrl({ action: "scan" }, { replace: false });
  try {
    const ep = routerEndpoint();
    const qs = ep ? `?timeout=1.8&endpoint=${encodeURIComponent(ep)}` : "?timeout=1.8";
    const data = await api(`/api/chat/channels${qs}`);
    channels = data.channels || [];
    localApiUrl = data.local_api_url || localApiUrl;
    const node = channels.find((c) => c.type === "urisys-node");
    if (node?.endpoint) {
      localStorage.setItem("ifuri_node", node.endpoint);
      await refreshVoiceCapabilities(node.endpoint);
    }
    const c = data.counts || {};
    lastChannelData = data;
    scanStatus.textContent = t("scanSummary", c.urisys_nodes ?? 0, c.mcp_agent ?? 0, c.ifuri_peers ?? 0);
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

  if (activeChannel.type === "webrtc-peer") {
    if (!webrtcSession?.isReady()) {
      messages[activeChannel.id].pop();
      appendMessage(activeChannel.id, "assistant", t("webrtcConnectFirst"), { error: true });
      return;
    }
    try {
      const reply = await webrtcSession.sendVoiceRequest(text, dryRunEl.checked);
      messages[activeChannel.id].pop();
      appendMessage(activeChannel.id, "assistant", reply.text || t("webrtcVoiceEmpty"), reply);
    } catch (err) {
      messages[activeChannel.id].pop();
      appendMessage(activeChannel.id, "assistant", `${t("errorPrefix")} ${err}`, { error: true });
    }
    return;
  }

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
    appendMessage(activeChannel.id, "assistant", `${t("errorPrefix")} ${err}`, { error: true });
  }
}

function screenImageUrl() {
  if (!activeChannel || activeChannel.type !== "urisys-node") return "";
  const ep = encodeURIComponent(activeChannel.endpoint);
  const nodeId = encodeURIComponent(activeChannel.node_id || "");
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
  syncUrl({ lang }, { replace: false });
  applyUiLanguage();
  if (lastChannelData) renderChannelList(lastChannelData);
  else renderChannelList({ groups: groupChannels(channels) });
  renderMessages();
});

themeSelect.addEventListener("change", () => {
  T()?.setTheme(themeSelect.value);
});

function groupChannels(list) {
  const groups = { node: [], mcp: [], a2a: [], llm: [], ifuri: [], webrtc: [] };
  for (const ch of list) groups[ch.kind]?.push(ch);
  return groups;
}

function setWebRtcStatus(state, detail) {
  if (!webrtcStatusEl) return;
  webrtcStatusEl.hidden = false;
  webrtcStatusEl.classList.toggle("error", state === "error" || state === "failed");
  const labels = {
    connecting: t("webrtcStatusConnecting"),
    connected: t("webrtcStatusConnected"),
    closed: t("webrtcStatusClosed"),
    error: t("webrtcStatusError"),
    failed: t("webrtcStatusError"),
  };
  webrtcStatusEl.textContent = labels[state] || `WebRTC: ${state}${detail ? ` (${detail})` : ""}`;
}

async function handleWebRtcEnvelope(envelope) {
  if (!envelope || envelope.kind !== "voice" || !envelope.id) {
    if (envelope?.kind === "uri" && activeChannel) {
      appendMessage(activeChannel.id, "assistant", `URI envelope:\n${JSON.stringify(envelope, null, 2)}`);
    }
    return;
  }
  const channelId = activeChannel?.id;
  if (channelId) {
    appendMessage(channelId, "user", `[peer] ${envelope.text}`, { via: "webrtc" });
    appendMessage(channelId, "assistant", "…", { pending: true });
  }
  try {
    const ep = routerEndpoint();
    const data = await api("/api/voice/run", {
      text: envelope.text,
      endpoint: ep || undefined,
      dry_run: Boolean(envelope.dry_run),
      speak: !envelope.dry_run,
    });
    const summary = data.summary || data.text || JSON.stringify(data, null, 2);
    if (channelId) {
      messages[channelId].pop();
      appendMessage(channelId, "assistant", summary, data);
    }
    webrtcSession?.sendVoiceReply(envelope.id, { ok: data.ok !== false, text: summary, body: data });
  } catch (err) {
    if (channelId) {
      messages[channelId].pop();
      appendMessage(channelId, "assistant", `${t("errorPrefix")} ${err}`, { error: true });
    }
    webrtcSession?.sendVoiceReply(envelope.id, { ok: false, text: String(err) });
  }
}

async function connectWebRtc() {
  if (!activeChannel || activeChannel.type !== "webrtc-peer") return;
  if (webrtcSession) {
    disconnectWebRtc();
    return;
  }
  const localUrl = localApiUrl || (await api("/api/webrtc/capabilities")).local_api_url;
  const remoteUrl = activeChannel.peer_url;
  const room = activeChannel.signaling_room;
  if (!localUrl || !remoteUrl || !room || !window.IfuriWebRtcPeer) {
    setWebRtcStatus("error", "missing peer config");
    return;
  }
  webrtcSession = new window.IfuriWebRtcPeer.WebRtcPeerSession({
    room,
    localUrl,
    remoteUrl,
    remoteAudioEl: webrtcRemoteAudio,
    onStatus: ({ state, detail }) => {
      setWebRtcStatus(state, detail);
      if (state === "connected" || state === "datachannel-open") {
        if (btnWebRtcConnect) btnWebRtcConnect.textContent = t("webrtcDisconnect");
        if (btnListen) btnListen.disabled = false;
      }
    },
    onMessage: (envelope) => handleWebRtcEnvelope(envelope),
  });
  if (btnWebRtcConnect) btnWebRtcConnect.textContent = t("webrtcDisconnect");
  try {
    await webrtcSession.start();
  } catch (err) {
    setWebRtcStatus("error", String(err));
    disconnectWebRtc();
  }
}

function disconnectWebRtc() {
  if (webrtcSession) {
    webrtcSession.stop();
    webrtcSession = null;
  }
  if (btnWebRtcConnect) btnWebRtcConnect.textContent = t("webrtcConnect");
  setWebRtcStatus("closed");
}

btnRefresh.onclick = refreshChannels;
btnSend.onclick = sendMessage;
btnScreen.onclick = refreshScreen;
btnViewToggle.onclick = toggleView;
if (btnWebRtcConnect) btnWebRtcConnect.onclick = connectWebRtc;
if (btnInstallVoicePacks) btnInstallVoicePacks.onclick = installVoicePacks;
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
  rec.onresult = async (ev) => {
    const transcript = ev.results[0][0].transcript;
    inputEl.value = transcript;
    syncPromptToUrl({ replace: true });
    if (activeChannel.type === "webrtc-peer" && webrtcSession?.isReady()) {
      await sendMessage();
    }
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
applyUiLanguage();
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
