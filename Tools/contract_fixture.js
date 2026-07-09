"use strict";

const crypto = require("crypto");
const http = require("http");
const net = require("net");
const { URL } = require("url");
const {
  CLIENT_TYPE,
  DEVICE_ID,
  DEVICE_NAME,
  DEVICE_TOKEN,
  MUSIC_DNA_KEY,
  HA_VERSION,
  WS_COMMANDS,
  FALLBACKS,
  FEATURES,
  identity,
} = require("./ha_contract");

const SECRET_KEY_RE = /(token|authorization|proof|apns|install|bearer|password|secret)/i;
const SHORT_LIVED_TOKEN = "ha-ws-session-token";

function redact(value) {
  if (Array.isArray(value)) return value.map(redact);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, SECRET_KEY_RE.test(key) ? "<redacted>" : redact(item)]));
  }
  return value;
}

function jsonResponse(res, statusCode, body) {
  const payload = JSON.stringify(body);
  res.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(payload),
  });
  res.end(payload);
}

function binaryResponse(res, statusCode, contentType, body) {
  const payload = Buffer.isBuffer(body) ? body : Buffer.from(body);
  res.writeHead(statusCode, {
    "content-type": contentType,
    "content-length": payload.length,
  });
  res.end(payload);
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  if (!chunks.length) return {};
  const raw = Buffer.concat(chunks).toString("utf8");
  if (!raw.trim()) return {};
  return JSON.parse(raw);
}

function routeKey(method, pathname) {
  return `${method.toUpperCase()} ${pathname}`;
}

function baseResponse(extra = {}) {
  return {
    success: true,
    ha_version: HA_VERSION,
    device_id: DEVICE_ID,
    client_type: CLIENT_TYPE,
    music_backend: "spotify_direct",
    music_backend_available: true,
    ...extra,
  };
}

function askDjHistory() {
  return baseResponse({
    revision: 2,
    items: [
      {
        id: "ask-1",
        role: "assistant",
        text: "Zet deze sfeer rustig voort.",
        timestamp: "2026-07-09T10:00:00Z",
        playback_actions: [],
      },
    ],
    recently_played_history: {
      items: [
        {
          id: "recent-1",
          title: "Ordinary World",
          subtitle: "Duran Duran",
          playback_actions: [],
        },
      ],
    },
  });
}

function musicDnaProfile(enabled = true) {
  return baseResponse({
    enabled,
    music_dna_key: MUSIC_DNA_KEY,
    state: enabled ? "ready" : "disabled",
    profile: enabled
      ? {
          summary: "Melodic pop, new wave and warm singalong tracks.",
          top_artists: ["Duran Duran", "Editors"],
          top_genres: ["new wave", "pop rock"],
        }
      : {},
    privacy_dashboard: {
      enabled,
      data_sources: ["spotify_recently_played", "spotify_top_items", "accepted_recommendations"],
      controls: ["settings", "clear", "export", "import"],
      stores_raw_audio: false,
      stores_oauth_tokens: false,
      stores_full_prompts: false,
    },
  });
}

function discoveryFeed() {
  return baseResponse({
    enabled: true,
    revision: 3,
    cache: { hit: true },
    sections: [
      {
        id: "new_for_you",
        title: "Nieuw voor jou",
        items: [
          {
            id: "disc-1",
            kind: "track",
            title: "The Promise",
            subtitle: "When In Rome",
            uri: "spotify:track:contract-1",
            image_url: "/api/djconnect/v1/image_proxy/cover-token",
            reason: "Past bij je Music DNA-profiel.",
            reason_sources: ["music_dna_artists", "music_dna_genres"],
            quality_score: 0.91,
            quality_band: "strong",
            quality_factors: { genre_fit: 0.9, novelty: 0.8 },
          },
        ],
      },
      {
        id: "accepted_recommendations",
        title: "Meer zoals je keuzes",
        items: [
          {
            id: "disc-2",
            kind: "artist",
            title: "Talk Talk",
            subtitle: "Artiest",
            uri: "spotify:artist:contract-2",
            reason: "Gerelateerd aan eerdere geaccepteerde keuzes.",
            reason_sources: ["accepted_recommendations"],
            quality_score: 0.78,
            quality_band: "medium",
            quality_factors: { related_artist: 0.78 },
          },
        ],
      },
    ],
  });
}

function trackInsight() {
  return baseResponse({
    title: "Ordinary World",
    artist: "Duran Duran",
    analysis: {
      summary: "Melodic and familiar with a strong chorus.",
      metrics: { energy: 0.8, danceability: 0.72, intensity: 0.65, confidence: 0.88 },
      listening_cues: ["Herkenbare melodie", "Ruime refreinen"],
    },
  });
}

function vibecast() {
  return baseResponse({
    context: {
      title: "Ordinary World",
      artist: "Duran Duran",
      artist_image_url: "/api/djconnect/v1/image_proxy/artist-token",
    },
    cards: [{ id: "vibe-1", title: "New wave glow", text: "Past bij de huidige sfeer." }],
  });
}

function validateIdentity(payload, headers = {}) {
  const deviceId = payload.device_id || headers["x-djconnect-device-id"];
  const clientType = payload.client_type || headers["x-djconnect-client-type"];
  return deviceId === DEVICE_ID && clientType === CLIENT_TYPE;
}

function createHttpHandler(state, options) {
  return async (req, res) => {
    try {
      const url = new URL(req.url, "http://127.0.0.1");
      const key = routeKey(req.method, url.pathname);
      let body = {};
      if (req.method !== "GET") body = await readBody(req);
      state.requests.push({ transport: "http", method: req.method, path: url.pathname, query: Object.fromEntries(url.searchParams), body: redact(body), headers: redact(req.headers) });

      if (key === "POST /api/djconnect/v1/websocket/session") {
        if (req.headers.authorization !== `Bearer ${DEVICE_TOKEN}`) return jsonResponse(res, 401, { success: false, error: "unauthorized" });
        if (body.access_token || body.ha_token || body.long_lived_access_token) return jsonResponse(res, 400, { success: false, error: "ha_token_not_allowed" });
        state.sessionRequests.push(redact(body));
        return jsonResponse(res, 200, {
          success: true,
          access_token: SHORT_LIVED_TOKEN,
          expires_at: Math.floor(Date.now() / 1000) + 300,
          websocket_url: `ws://127.0.0.1:${state.port}/api/websocket`,
          commands: options.commands,
        });
      }

      if (url.pathname === "/api/djconnect/v1/tts/sample.mp3") return binaryResponse(res, 200, "audio/mpeg", "fixture-audio");
      if (url.pathname === "/api/djconnect/v1/image_proxy/cover-token" || url.pathname === "/api/djconnect/v1/image_proxy/artist-token") return binaryResponse(res, 200, "image/png", Buffer.from([0x89, 0x50, 0x4e, 0x47]));
      if (key === "GET /api/djconnect/v1/debug/last_voice.wav") return binaryResponse(res, 200, "audio/wav", "fixture-wav");

      const payload = req.method === "GET" ? Object.fromEntries(url.searchParams) : body;
      if (!["POST /api/djconnect/v1/pair", "GET /api/djconnect/v1/vibecast"].includes(key) && !validateIdentity(payload, req.headers)) {
        return jsonResponse(res, 400, { success: false, error: "invalid_identity" });
      }

      if (key === "POST /api/djconnect/v1/pair") return jsonResponse(res, 200, baseResponse({ device_token: DEVICE_TOKEN, paired: true }));
      if (key === "POST /api/djconnect/v1/status") return jsonResponse(res, 200, baseResponse({ status: "ok", playback: body.playback || {} }));
      if (key === "POST /api/djconnect/v1/command") return jsonResponse(res, 200, baseResponse({ command: body.command || "", transport: "http" }));
      if (key === "POST /api/djconnect/v1/event") return jsonResponse(res, 200, baseResponse({ accepted: true }));
      if (key === "POST /api/djconnect/v1/voice") return jsonResponse(res, 200, baseResponse({ transcript: "fixture voice", response: "ok" }));
      if (key === "POST /api/djconnect/v1/ask_dj" || key === "POST /api/djconnect/v1/ask_dj/message") return jsonResponse(res, 200, baseResponse({ reply: "Fixture Ask DJ response", items: askDjHistory().items }));
      if (key === "POST /api/djconnect/v1/ask_dj/clear") return jsonResponse(res, 200, baseResponse({ cleared: true }));
      if (key === "POST /api/djconnect/v1/ask_dj/idle_suggestion") return jsonResponse(res, 200, baseResponse({ suggestion: "Speel iets dat hierbij past." }));
      if (key === "GET /api/djconnect/v1/ask_dj/history") return jsonResponse(res, 200, askDjHistory());
      if (key === "POST /api/djconnect/v1/ask_dj/history/clear") return jsonResponse(res, 200, baseResponse({ cleared: true, revision: 3 }));
      if (key === "POST /api/djconnect/v1/ask_dj/history/export") return jsonResponse(res, 200, baseResponse({ format: "djconnect.ask_dj.history.export", items: askDjHistory().items }));
      if (key === "POST /api/djconnect/v1/ask_dj/history_state") return jsonResponse(res, 200, baseResponse({ revision: 2, items: askDjHistory().items }));
      if (key === "POST /api/djconnect/v1/music_dna/profile") return jsonResponse(res, 200, musicDnaProfile(true));
      if (key === "POST /api/djconnect/v1/music_dna/settings") return jsonResponse(res, 200, musicDnaProfile(body.enabled !== false));
      if (key === "POST /api/djconnect/v1/music_dna/clear") return jsonResponse(res, 200, musicDnaProfile(false));
      if (key === "POST /api/djconnect/v1/music_dna/import") return jsonResponse(res, 200, baseResponse({ imported: true, music_dna_key: MUSIC_DNA_KEY }));
      if (key === "POST /api/djconnect/v1/music_dna/export") return jsonResponse(res, 200, baseResponse({ format: "djconnect.music_dna.export", exported_by_client_type: CLIENT_TYPE, profile: musicDnaProfile(true) }));
      if (key === "GET /api/djconnect/v1/music_discovery") return jsonResponse(res, 200, discoveryFeed());
      if (key === "POST /api/djconnect/v1/music_discovery/refresh") return jsonResponse(res, 200, { ...discoveryFeed(), refreshed: true });
      if (key === "POST /api/djconnect/v1/music_discovery/play") return jsonResponse(res, 200, baseResponse({ played: true, section_id: body.section_id, discovery_item_id: body.discovery_item_id }));
      if (key === "POST /api/djconnect/v1/music_discovery/feedback") return jsonResponse(res, 200, baseResponse({ feedback_recorded: true, feedback: body.feedback, section_id: body.section_id, discovery_item_id: body.discovery_item_id }));
      if (key === "POST /api/djconnect/v1/track_insight") return jsonResponse(res, 200, trackInsight());
      if (key === "GET /api/djconnect/v1/vibecast") return jsonResponse(res, 200, vibecast());

      return jsonResponse(res, 404, { success: false, error: "not_found" });
    } catch (error) {
      state.errors.push(error && error.message ? error.message : String(error));
      return jsonResponse(res, 500, { success: false, error: "fixture_error" });
    }
  };
}

function websocketAccept(key) {
  return crypto.createHash("sha1").update(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`).digest("base64");
}

function encodeFrame(object) {
  const payload = Buffer.from(JSON.stringify(object), "utf8");
  if (payload.length < 126) return Buffer.concat([Buffer.from([0x81, payload.length]), payload]);
  const header = Buffer.alloc(4);
  header[0] = 0x81;
  header[1] = 126;
  header.writeUInt16BE(payload.length, 2);
  return Buffer.concat([header, payload]);
}

function decodeFrames(buffer) {
  const frames = [];
  let offset = 0;
  while (buffer.length - offset >= 2) {
    const first = buffer[offset++];
    const second = buffer[offset++];
    const opcode = first & 0x0f;
    const masked = (second & 0x80) !== 0;
    let length = second & 0x7f;
    if (length === 126) {
      if (buffer.length - offset < 2) break;
      length = buffer.readUInt16BE(offset);
      offset += 2;
    } else if (length === 127) {
      throw new Error("large websocket frames are not supported by the fixture");
    }
    const mask = masked ? buffer.subarray(offset, offset + 4) : null;
    if (masked) offset += 4;
    if (buffer.length - offset < length) break;
    const payload = Buffer.from(buffer.subarray(offset, offset + length));
    offset += length;
    if (mask) {
      for (let i = 0; i < payload.length; i += 1) payload[i] ^= mask[i % 4];
    }
    if (opcode === 0x8) frames.push({ close: true });
    if (opcode === 0x1) frames.push({ text: payload.toString("utf8") });
  }
  return { frames, rest: buffer.subarray(offset) };
}

function wsResult(id, result) {
  return { id, type: "result", success: true, result };
}

function handleWsMessage(state, options, socket, message) {
  const type = message.type;
  state.requests.push({ transport: "websocket", type, body: redact(message) });
  if (type === "auth") {
    if (message.access_token === SHORT_LIVED_TOKEN) socket.write(encodeFrame({ type: "auth_ok", ha_version: HA_VERSION }));
    else socket.write(encodeFrame({ type: "auth_invalid", message: "Invalid access token" }));
    return;
  }
  if (type === "djconnect/capabilities") {
    socket.write(encodeFrame(wsResult(message.id, {
      success: true,
      domain: "djconnect",
      ha_version: HA_VERSION,
      websocket_supported: true,
      commands: options.commands,
      features: FEATURES,
      fallbacks: FALLBACKS,
      transports: { http: true, websocket: true },
    })));
    return;
  }
  if (!options.commands.includes(type)) {
    socket.write(encodeFrame({ id: message.id, type: "result", success: false, error: { code: "unknown_command", message: "Command is not advertised" } }));
    return;
  }
  if (!validateIdentity(message, {})) {
    socket.write(encodeFrame({ id: message.id, type: "result", success: false, error: { code: "invalid_identity", message: "Invalid DJConnect identity" } }));
    return;
  }
  const map = {
    "djconnect/command": () => baseResponse({ command: message.command || "", transport: "websocket" }),
    "djconnect/ask_dj/message": () => baseResponse({ reply: "Fixture Ask DJ response", items: askDjHistory().items }),
    "djconnect/ask_dj/history": () => askDjHistory(),
    "djconnect/ask_dj/history/clear": () => baseResponse({ cleared: true, revision: 3 }),
    "djconnect/ask_dj/history/state": () => baseResponse({ revision: 2, items: askDjHistory().items }),
    "djconnect/ask_dj/idle_suggestion": () => baseResponse({ suggestion: "Speel iets dat hierbij past." }),
    "djconnect/track_insight": () => trackInsight(),
    "djconnect/music_dna/profile": () => musicDnaProfile(true),
    "djconnect/music_dna/settings": () => musicDnaProfile(message.enabled !== false),
    "djconnect/music_dna/clear": () => musicDnaProfile(false),
    "djconnect/music_dna/import": () => baseResponse({ imported: true, music_dna_key: MUSIC_DNA_KEY }),
    "djconnect/music_dna/export": () => baseResponse({ format: "djconnect.music_dna.export", exported_by_client_type: CLIENT_TYPE, profile: musicDnaProfile(true) }),
    "djconnect/music_discovery/feed": () => discoveryFeed(),
    "djconnect/music_discovery/refresh": () => ({ ...discoveryFeed(), refreshed: true }),
    "djconnect/music_discovery/play": () => baseResponse({ played: true, section_id: message.section_id, discovery_item_id: message.discovery_item_id }),
    "djconnect/music_discovery/feedback": () => baseResponse({ feedback_recorded: true, feedback: message.feedback, section_id: message.section_id, discovery_item_id: message.discovery_item_id }),
  };
  socket.write(encodeFrame(wsResult(message.id, map[type]())));
}

function attachWebSocket(server, state, options) {
  server.on("upgrade", (req, socket) => {
    if (req.url !== "/api/websocket") {
      socket.destroy();
      return;
    }
    state.sockets.add(socket);
    socket.on("close", () => state.sockets.delete(socket));
    const key = req.headers["sec-websocket-key"];
    socket.write(
      "HTTP/1.1 101 Switching Protocols\r\n" +
        "Upgrade: websocket\r\n" +
        "Connection: Upgrade\r\n" +
        `Sec-WebSocket-Accept: ${websocketAccept(key)}\r\n\r\n`
    );
    socket.write(encodeFrame({ type: "auth_required", ha_version: HA_VERSION }));
    let buffer = Buffer.alloc(0);
    socket.on("data", (chunk) => {
      buffer = Buffer.concat([buffer, chunk]);
      const decoded = decodeFrames(buffer);
      buffer = decoded.rest;
      for (const frame of decoded.frames) {
        if (frame.close) {
          socket.end();
          continue;
        }
        handleWsMessage(state, options, socket, JSON.parse(frame.text));
      }
    });
  });
}

async function startContractServer(options = {}) {
  const state = {
    port: 0,
    requests: [],
    sessionRequests: [],
    errors: [],
    sockets: new Set(),
  };
  const config = {
    commands: options.commands || WS_COMMANDS.slice(),
  };
  const server = http.createServer(createHttpHandler(state, config));
  attachWebSocket(server, state, config);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  state.port = server.address().port;
  return {
    url: `http://127.0.0.1:${state.port}`,
    wsUrl: `ws://127.0.0.1:${state.port}/api/websocket`,
    state,
    commands: config.commands,
    close: () => {
      for (const socket of state.sockets) socket.destroy();
      return new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));
    },
  };
}

async function contractFixture(callback, options = {}) {
  const fixture = await startContractServer(options);
  try {
    return await callback(fixture);
  } finally {
    await fixture.close();
  }
}

async function requestJson(baseUrl, method, path, body, headers = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: { "content-type": "application/json", authorization: `Bearer ${DEVICE_TOKEN}`, "x-djconnect-device-id": DEVICE_ID, "x-djconnect-client-type": CLIENT_TYPE, ...headers },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") && text ? JSON.parse(text) : { raw: text };
  return { status: response.status, data };
}

function encodeClientFrame(object) {
  const payload = Buffer.from(JSON.stringify(object), "utf8");
  const mask = crypto.randomBytes(4);
  const header = payload.length < 126 ? Buffer.from([0x81, 0x80 | payload.length]) : Buffer.from([0x81, 0x80 | 126, payload.length >> 8, payload.length & 0xff]);
  const masked = Buffer.from(payload);
  for (let i = 0; i < masked.length; i += 1) masked[i] ^= mask[i % 4];
  return Buffer.concat([header, mask, masked]);
}

async function wsExchange(baseUrl, type, payload = {}) {
  const session = await requestJson(baseUrl, "POST", "/api/djconnect/v1/websocket/session", { device_id: DEVICE_ID, client_type: CLIENT_TYPE, requested_commands: WS_COMMANDS });
  if (session.status !== 200) throw new Error("session bootstrap failed");
  const wsUrl = new URL(session.data.websocket_url);
  const socket = net.createConnection({ host: wsUrl.hostname, port: Number(wsUrl.port) });
  const key = crypto.randomBytes(16).toString("base64");
  let buffer = Buffer.alloc(0);
  let handshakeDone = false;
  const messages = [];
  const waiters = [];
  const deliver = (message) => {
    const waiter = waiters.shift();
    if (waiter) waiter.resolve(message);
    else messages.push(message);
  };
  const fail = (error) => {
    for (const waiter of waiters.splice(0)) waiter.reject(error);
  };
  socket.on("data", (chunk) => {
    buffer = Buffer.concat([buffer, chunk]);
    if (!handshakeDone) {
      const headerEnd = buffer.indexOf("\r\n\r\n");
      if (headerEnd < 0) return;
      buffer = buffer.subarray(headerEnd + 4);
      handshakeDone = true;
    }
    const decoded = decodeFrames(buffer);
    buffer = decoded.rest;
    for (const frame of decoded.frames) {
      if (frame.text) deliver(JSON.parse(frame.text));
    }
  });
  socket.on("error", fail);
  await new Promise((resolve, reject) => {
    socket.once("connect", resolve);
    socket.once("error", reject);
  });
  socket.write(`GET ${wsUrl.pathname} HTTP/1.1\r\nHost: ${wsUrl.host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: ${key}\r\nSec-WebSocket-Version: 13\r\n\r\n`);
  const nextMessage = () => {
    if (messages.length) return Promise.resolve(messages.shift());
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("websocket fixture response timeout")), 3000);
      waiters.push({
        resolve: (message) => {
          clearTimeout(timer);
          resolve(message);
        },
        reject: (error) => {
          clearTimeout(timer);
          reject(error);
        },
      });
    });
  };
  await nextMessage();
  socket.write(encodeClientFrame({ type: "auth", access_token: session.data.access_token }));
  const auth = await nextMessage();
  if (auth.type !== "auth_ok") throw new Error("websocket auth failed");
  socket.write(encodeClientFrame({ id: 1, type, ...identity(), device_token: DEVICE_TOKEN, ...payload }));
  const result = await nextMessage();
  socket.destroy();
  return result;
}

module.exports = {
  SHORT_LIVED_TOKEN,
  redact,
  startContractServer,
  contractFixture,
  requestJson,
  wsExchange,
};
