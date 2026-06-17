/**
 * page:// handlers — mirror url_state.js for uricore-js registry.
 * Requires IfuriUrlState (web/url_state.js) on window.
 */

function urlState() {
  if (typeof window !== 'undefined' && window.IfuriUrlState) {
    return window.IfuriUrlState;
  }
  return null;
}

export function get_url_state(payload, context) {
  const key = context?.variables?.key || payload?.key || 'all';
  const us = urlState();
  if (!us) {
    return { ok: false, error: 'IfuriUrlState not loaded' };
  }
  const state = typeof us.read === 'function' ? us.read() : {};
  if (key === 'all') {
    return { ok: true, state };
  }
  return { ok: true, key, value: state[key] ?? null };
}

export function set_url_state(payload, context) {
  const key = context?.variables?.key || payload?.key;
  const value = payload?.value;
  const us = urlState();
  if (!us || !key) {
    return { ok: false, error: 'missing key or IfuriUrlState' };
  }
  if (typeof us.set === 'function') {
    us.set(key, value);
  }
  return { ok: true, key, value };
}

export function toggle_view(_payload, _context) {
  const us = urlState();
  if (!us || typeof us.read !== 'function' || typeof us.set !== 'function') {
    return { ok: false, error: 'IfuriUrlState not loaded' };
  }
  const current = us.read()?.view === 'screen' ? 'screen' : 'chat';
  const next = current === 'screen' ? 'chat' : 'screen';
  us.set('view', next);
  const btn = document.getElementById('btnViewToggle');
  if (btn) {
    btn.click();
  }
  return { ok: true, view: next };
}
