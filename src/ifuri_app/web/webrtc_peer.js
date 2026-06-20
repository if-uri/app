// Author: Tom Sapletta · https://tom.sapletta.com
// Part of the ifURI solution.

/**
 * WebRTC peer session — HTTP signaling + duplex audio + voice data channel.
 */
(function (global) {
  const DEFAULT_ICE = [{ urls: "stun:stun.l.google.com:19302" }];

  function api(path, body) {
    return fetch(path, {
      method: body ? "POST" : "GET",
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
    }).then((r) => r.json());
  }

  function postRemote(remoteBase, payload) {
    const base = String(remoteBase || "").replace(/\/$/, "");
    return fetch(`${base}/api/webrtc/signal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json());
  }

  function newId() {
    return `v${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  }

  class WebRtcPeerSession {
    constructor({ room, localUrl, remoteUrl, onStatus, onMessage, remoteAudioEl }) {
      this.room = room;
      this.localUrl = localUrl;
      this.remoteUrl = remoteUrl;
      this.remoteAudioEl = remoteAudioEl || null;
      this.initiator = localUrl <= remoteUrl;
      this.onStatus = onStatus || (() => {});
      this.onMessage = onMessage || (() => {});
      this.pc = null;
      this.dataChannel = null;
      this.localStream = null;
      this.pollTimer = null;
      this.since = 0;
      this._stopped = false;
      this._pending = new Map();
    }

    isReady() {
      return Boolean(this.dataChannel && this.dataChannel.readyState === "open");
    }

    _setStatus(state, detail) {
      this.onStatus({ state, detail: detail || null, room: this.room });
    }

    _dispatch(envelope) {
      if (!envelope || typeof envelope !== "object") return;
      if (envelope.kind === "voice-reply" && envelope.id && this._pending.has(envelope.id)) {
        const { resolve, reject, timer } = this._pending.get(envelope.id);
        clearTimeout(timer);
        this._pending.delete(envelope.id);
        if (envelope.ok === false) reject(new Error(envelope.error || "voice failed"));
        else resolve(envelope);
        return;
      }
      this.onMessage(envelope);
    }

    async start() {
      this._stopped = false;
      this._setStatus("connecting");
      this.pc = new RTCPeerConnection({ iceServers: DEFAULT_ICE });
      this.pc.onconnectionstatechange = () => {
        this._setStatus(this.pc.connectionState, { ice: this.pc.iceConnectionState });
      };
      this.pc.ontrack = (ev) => {
        const stream = ev.streams?.[0];
        if (stream && this.remoteAudioEl) {
          this.remoteAudioEl.srcObject = stream;
          this.remoteAudioEl.play?.().catch(() => {});
        }
      };
      this.pc.onicecandidate = async (ev) => {
        if (!ev.candidate || this._stopped) return;
        try {
          await postRemote(this.remoteUrl, {
            room: this.room,
            from: this.localUrl,
            type: "ice",
            data: ev.candidate.toJSON(),
          });
        } catch (err) {
          this._setStatus("error", String(err));
        }
      };
      this.pc.ondatachannel = (ev) => this._wireChannel(ev.channel);
      if (this.initiator) {
        this.dataChannel = this.pc.createDataChannel("uri");
        this._wireChannel(this.dataChannel);
      }
      try {
        this.localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        this.localStream.getTracks().forEach((t) => this.pc.addTrack(t, this.localStream));
      } catch {
        /* mic optional — text-only duplex still works */
      }
      this.pollTimer = setInterval(() => this._poll(), 400);
      if (this.initiator) {
        const offer = await this.pc.createOffer();
        await this.pc.setLocalDescription(offer);
        const posted = await postRemote(this.remoteUrl, {
          room: this.room,
          from: this.localUrl,
          type: "offer",
          data: offer,
        });
        if (!posted.ok) throw new Error(posted.error || "offer post failed");
      }
      await this._poll();
    }

    _wireChannel(channel) {
      this.dataChannel = channel;
      channel.onopen = () => this._setStatus("datachannel-open");
      channel.onmessage = (ev) => {
        try {
          this._dispatch(JSON.parse(ev.data));
        } catch {
          this._dispatch({ kind: "raw", raw: ev.data });
        }
      };
    }

    async _poll() {
      if (this._stopped) return;
      let data;
      try {
        data = await api(`/api/webrtc/signal?room=${encodeURIComponent(this.room)}&since=${this.since}`);
      } catch (err) {
        this._setStatus("error", String(err));
        return;
      }
      if (!data.ok) return;
      this.since = data.next ?? this.since;
      for (const sig of data.signals || []) {
        await this._applySignal(sig);
      }
    }

    async _applySignal(sig) {
      if (!this.pc || this._stopped) return;
      const t = sig.type;
      const payload = sig.data;
      if (t === "offer" && !this.initiator) {
        await this.pc.setRemoteDescription(payload);
        const answer = await this.pc.createAnswer();
        await this.pc.setLocalDescription(answer);
        await postRemote(this.remoteUrl, {
          room: this.room,
          from: this.localUrl,
          type: "answer",
          data: answer,
        });
      } else if (t === "answer" && this.initiator) {
        await this.pc.setRemoteDescription(payload);
      } else if (t === "ice" && payload) {
        try {
          await this.pc.addIceCandidate(payload);
        } catch {
          /* duplicate / timing */
        }
      }
    }

    sendEnvelope(envelope) {
      if (!this.isReady()) return { ok: false, error: "data channel not open" };
      this.dataChannel.send(JSON.stringify(envelope));
      return { ok: true };
    }

    sendVoiceRequest(text, dryRun = false, { timeoutMs = 120000 } = {}) {
      if (!this.isReady()) return Promise.reject(new Error("data channel not open"));
      const id = newId();
      const envelope = { kind: "voice", id, text: String(text || ""), dry_run: Boolean(dryRun) };
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          this._pending.delete(id);
          reject(new Error("voice reply timeout"));
        }, timeoutMs);
        this._pending.set(id, { resolve, reject, timer });
        try {
          this.dataChannel.send(JSON.stringify(envelope));
        } catch (err) {
          clearTimeout(timer);
          this._pending.delete(id);
          reject(err);
        }
      });
    }

    sendVoiceReply(id, result) {
      const payload = {
        kind: "voice-reply",
        id,
        ok: Boolean(result?.ok !== false),
        text: String(result?.text || result?.summary || result?.error || ""),
        body: result || null,
      };
      return this.sendEnvelope(payload);
    }

    stop() {
      this._stopped = true;
      if (this.pollTimer) clearInterval(this.pollTimer);
      this.pollTimer = null;
      for (const [, pending] of this._pending) clearTimeout(pending.timer);
      this._pending.clear();
      if (this.localStream) {
        this.localStream.getTracks().forEach((t) => t.stop());
        this.localStream = null;
      }
      if (this.remoteAudioEl) this.remoteAudioEl.srcObject = null;
      if (this.pc) this.pc.close();
      this.pc = null;
      this.dataChannel = null;
      this._setStatus("closed");
    }
  }

  global.IfuriWebRtcPeer = { WebRtcPeerSession, DEFAULT_ICE };
})(window);
