/**
 * Apply theme + language from URL (?theme= dark|light|ifuri &lang= pl|en).
 */
(function (global) {
  const THEMES = ["dark", "light", "ifuri"];

  function applyTheme(name) {
    const theme = THEMES.includes(name) ? name : "dark";
    document.documentElement.setAttribute("data-theme", theme);
    return theme;
  }

  function applyLang(code) {
    const lang = code === "en" ? "en" : "pl";
    document.documentElement.lang = lang;
    return lang;
  }

  function initFromUrl() {
    const U = global.IfuriUrlState;
    if (!U) return { theme: "dark", lang: "pl" };
    return {
      theme: applyTheme(U.get("theme", "dark")),
      lang: applyLang(U.get("lang", "pl")),
    };
  }

  function setTheme(name, { replace } = { replace: false }) {
    applyTheme(name);
    global.IfuriUrlState?.patch({ theme: name }, { replace: !!replace });
  }

  function setLang(code, { replace } = { replace: false }) {
    applyLang(code);
    global.IfuriUrlState?.patch({ lang: code }, { replace: !!replace });
  }

  global.IfuriTheme = { initFromUrl, applyTheme, applyLang, setTheme, setLang, THEMES };
})(window);
