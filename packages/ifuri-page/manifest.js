/**
 * Browser-side page:// handlers for /voice (uricore-js).
 * Import in web/voice.js when @uricore/js is wired.
 */
export const ifuriPageManifest = {
  id: 'ifuri-page-pack',
  version: 1,
  scheme: 'page',
  description: 'DOM and URL state inside ifURI /voice UI.',
  uri_patterns: [
    {
      pattern: 'page://voice/state/{key}/query/get',
      kind: 'query',
      operation: 'get_url_state',
      handler: 'get_url_state',
      side_effects: false,
    },
    {
      pattern: 'page://voice/state/{key}/command/set',
      kind: 'command',
      operation: 'set_url_state',
      handler: 'set_url_state',
      side_effects: true,
      approval: 'not_required',
    },
    {
      pattern: 'page://voice/view/command/toggle',
      kind: 'command',
      operation: 'toggle_view',
      handler: 'toggle_view',
      side_effects: true,
      approval: 'not_required',
    },
  ],
};
