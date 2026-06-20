// Author: Tom Sapletta · https://tom.sapletta.com
// Part of the ifURI solution.

/**
 * ifURI page:// runtime — @uricore/js + packages/ifuri-page handlers.
 */
import {
  CapabilityRegistry,
  LocalStorageEventStore,
  PolicyGate,
  UriControlRuntime,
} from "./vendor/uricore/index.js";
import { ifuriPageManifest } from "./page/manifest.js";
import * as pageHandlers from "./page/handlers.js";

const registry = new CapabilityRegistry().loadManifest(ifuriPageManifest, pageHandlers);
const runtime = new UriControlRuntime({
  registry,
  eventStore: new LocalStorageEventStore("ifuri.page.events"),
  policy: new PolicyGate({ requireApprovalForSideEffects: false }),
});

window.IfuriPageRuntime = runtime;
