/**
 * ifURI /voice UI strings — PL + EN.
 */
(function (global) {
  const I18N = {
    pl: {
      title: "ifURI — czat",
      refreshTitle: "Odśwież czaty z LAN",
      sidebarAria: "Endpointy jako czaty",
      pickChat: "Wybierz czat",
      emptyList: "Brak endpointów — uruchom urisys-node :8790 lub ifuri-app serve w LAN.",
      emptyThread: "Każdy urisys-node :8790, MCP, A2A i peer ifURI to osobny czat.",
      newThread: "Nowy czat z",
      sendHint: "Wyślij polecenie lub pytanie.",
      placeholder: "Wiadomość do endpointu…",
      send: "Wyślij",
      scan: "Skanowanie LAN…",
      scanFail: "Skan nieudany",
      scanSummary: (nodes, mcp, peers) => `${nodes} node · ${mcp} MCP/A2A · ${peers} peer`,
      viewChat: "Czat",
      viewScreen: "Ekran",
      screenshot: "Screenshot",
      screenAuto: "auto",
      dryRun: "dry-run",
      you: "Ty",
      loadingHistory: "Ładowanie historii…",
      historyFail: "Nie udało się wczytać historii z urisys-node",
      speechMissing: "Web Speech API niedostępne — wpisz tekst ręcznie.",
      errorPrefix: "Błąd:",
      screenAlt: "Zrzut ekranu zdalnego",
      langAria: "Język",
      themeAria: "Motyw",
      listenTitle: "Dyktuj (Web Speech)",
      voicePackBanner: "Brak packów stt/tts na urisys-node — głos działa tylko przez wpisywanie tekstu.",
      voicePackInstall: "Zainstaluj packi głosowe",
      voicePackInstalling: "Instalacja…",
      voicePackDone: "Packi głosowe zainstalowane.",
      voicePackFail: "Instalacja packów nie powiodła się.",
      webrtcConnect: "Połącz WebRTC",
      webrtcDisconnect: "Rozłącz",
      webrtcStatusConnecting: "WebRTC: łączenie…",
      webrtcStatusConnected: "WebRTC: połączono",
      webrtcStatusError: "WebRTC: błąd",
      webrtcStatusClosed: "WebRTC: rozłączono",
      webrtcVoiceEmpty: "(brak odpowiedzi)",
      webrtcVoiceViaDc: "Głos przez WebRTC data channel",
      webrtcConnectFirst: "Najpierw kliknij „Połącz WebRTC”.",
    },
    en: {
      title: "ifURI — chat",
      refreshTitle: "Refresh chats from LAN",
      sidebarAria: "Endpoints as chats",
      pickChat: "Pick a chat",
      emptyList: "No endpoints — start urisys-node :8790 or ifuri-app serve on LAN.",
      emptyThread: "Each urisys-node :8790, MCP, A2A and ifURI peer is its own chat.",
      newThread: "New chat with",
      sendHint: "Send a command or question.",
      placeholder: "Message to endpoint…",
      send: "Send",
      scan: "Scanning LAN…",
      scanFail: "Scan failed",
      scanSummary: (nodes, mcp, peers) => `${nodes} node · ${mcp} MCP/A2A · ${peers} peer`,
      viewChat: "Chat",
      viewScreen: "Screen",
      screenshot: "Screenshot",
      screenAuto: "auto",
      dryRun: "dry-run",
      you: "You",
      loadingHistory: "Loading history…",
      historyFail: "Could not load history from urisys-node",
      speechMissing: "Web Speech API unavailable — type manually.",
      errorPrefix: "Error:",
      screenAlt: "Remote screen capture",
      langAria: "Language",
      themeAria: "Theme",
      listenTitle: "Dictate (Web Speech)",
      voicePackBanner: "stt/tts packs missing on urisys-node — voice input is text-only.",
      voicePackInstall: "Install voice packs",
      voicePackInstalling: "Installing…",
      voicePackDone: "Voice packs installed.",
      voicePackFail: "Voice pack install failed.",
      webrtcConnect: "Connect WebRTC",
      webrtcDisconnect: "Disconnect",
      webrtcStatusConnecting: "WebRTC: connecting…",
      webrtcStatusConnected: "WebRTC: connected",
      webrtcStatusError: "WebRTC: error",
      webrtcStatusClosed: "WebRTC: disconnected",
      webrtcVoiceEmpty: "(no reply)",
      webrtcVoiceViaDc: "Voice over WebRTC data channel",
      webrtcConnectFirst: "Click “Connect WebRTC” first.",
    },
  };

  const GROUP_LABELS = {
    pl: { node: "urisys-node :8790", mcp: "MCP", a2a: "A2A / agent", llm: "LLM", ifuri: "ifURI peer", webrtc: "WebRTC peer" },
    en: { node: "urisys-node :8790", mcp: "MCP", a2a: "A2A / agent", llm: "LLM", ifuri: "ifURI peer", webrtc: "WebRTC peer" },
  };

  function t(lang, key, ...args) {
    const bag = I18N[lang] || I18N.pl;
    const val = bag[key];
    if (typeof val === "function") return val(...args);
    return val ?? key;
  }

  function groupLabels(lang) {
    return GROUP_LABELS[lang] || GROUP_LABELS.pl;
  }

  global.IfuriI18n = { I18N, t, groupLabels };
})(window);
