/**
 * Persistent URL state — lang, theme, view and app-specific params.
 * Updates use pushState on user actions; shareable/bookmarkable links.
 */
(function (global) {
  const RESERVED = new Set(["lang", "theme", "view"]);

  function read() {
    const params = new URLSearchParams(global.location.search);
    const out = {};
    for (const [k, v] of params.entries()) out[k] = v;
    return out;
  }

  function write(next, { replace = false, pathname = global.location.pathname } = {}) {
    const merged = { ...read(), ...next };
    for (const key of Object.keys(merged)) {
      if (merged[key] === null || merged[key] === undefined || merged[key] === "") {
        delete merged[key];
      }
    }
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(merged)) qs.set(k, String(v));
    const q = qs.toString();
    const url = q ? `${pathname}?${q}` : pathname;
    if (replace) {
      global.history.replaceState({ ifuri: merged }, "", url);
    } else {
      global.history.pushState({ ifuri: merged }, "", url);
    }
    return merged;
  }

  function patch(partial, opts) {
    return write({ ...read(), ...partial }, opts);
  }

  function get(key, fallback) {
    const v = read()[key];
    return v === undefined ? fallback : v;
  }

  function onPopState(fn) {
    global.addEventListener("popstate", () => fn(read()));
  }

  function withParams(href, extra) {
    const base = new URL(href, global.location.href);
    const cur = read();
    for (const k of ["lang", "theme", "view", "channel", "prompt", "dry_run", "screen_auto"]) {
      if (cur[k] && !base.searchParams.has(k)) base.searchParams.set(k, cur[k]);
    }
    if (extra) {
      for (const [k, v] of Object.entries(extra)) {
        if (v === null || v === undefined || v === "") base.searchParams.delete(k);
        else base.searchParams.set(k, String(v));
      }
    }
    return base.pathname + base.search + base.hash;
  }

  global.IfuriUrlState = { read, write, patch, get, onPopState, withParams, RESERVED };
})(window);
