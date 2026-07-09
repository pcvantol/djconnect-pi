"use strict";

const CLIENT_TYPE = "raspberry_pi";
const DEVICE_ID = "djconnect-raspberry-pi-ABCDEF123456";
const DEVICE_NAME = "DJConnect Pi CI";
const DEVICE_TOKEN = "ci-device-token";
const MUSIC_DNA_KEY = "user:ha-contract-fixture";
const HA_VERSION = "3.2.46";

const HTTP_ROUTES = [
  ["POST", "/api/djconnect/v1/pair"],
  ["POST", "/api/djconnect/v1/status"],
  ["POST", "/api/djconnect/v1/command"],
  ["POST", "/api/djconnect/v1/event"],
  ["POST", "/api/djconnect/v1/voice"],
  ["POST", "/api/djconnect/v1/ask_dj"],
  ["POST", "/api/djconnect/v1/ask_dj/message"],
  ["POST", "/api/djconnect/v1/ask_dj/clear"],
  ["POST", "/api/djconnect/v1/ask_dj/idle_suggestion"],
  ["GET", "/api/djconnect/v1/ask_dj/history"],
  ["POST", "/api/djconnect/v1/ask_dj/history/clear"],
  ["POST", "/api/djconnect/v1/ask_dj/history/export"],
  ["POST", "/api/djconnect/v1/ask_dj/history_state"],
  ["POST", "/api/djconnect/v1/music_dna/profile"],
  ["POST", "/api/djconnect/v1/music_dna/settings"],
  ["POST", "/api/djconnect/v1/music_dna/clear"],
  ["POST", "/api/djconnect/v1/music_dna/import"],
  ["POST", "/api/djconnect/v1/music_dna/export"],
  ["GET", "/api/djconnect/v1/music_discovery"],
  ["POST", "/api/djconnect/v1/music_discovery/refresh"],
  ["POST", "/api/djconnect/v1/music_discovery/play"],
  ["POST", "/api/djconnect/v1/music_discovery/feedback"],
  ["POST", "/api/djconnect/v1/track_insight"],
  ["GET", "/api/djconnect/v1/vibecast"],
  ["GET", "/api/djconnect/v1/tts/{token}.{extension}"],
  ["GET", "/api/djconnect/v1/image_proxy/{token}"],
  ["GET", "/api/djconnect/v1/debug/last_voice.wav"],
  ["POST", "/api/djconnect/v1/websocket/session"],
];

const WS_COMMANDS = [
  "djconnect/command",
  "djconnect/ask_dj/message",
  "djconnect/ask_dj/history",
  "djconnect/ask_dj/history/clear",
  "djconnect/ask_dj/history/state",
  "djconnect/ask_dj/idle_suggestion",
  "djconnect/track_insight",
  "djconnect/music_dna/profile",
  "djconnect/music_dna/settings",
  "djconnect/music_dna/clear",
  "djconnect/music_dna/import",
  "djconnect/music_dna/export",
  "djconnect/music_discovery/feed",
  "djconnect/music_discovery/refresh",
  "djconnect/music_discovery/play",
  "djconnect/music_discovery/feedback",
];

const FALLBACKS = {
  ask_dj_chat: { available: true, preferred_transport: "websocket", http_path: "/api/djconnect/v1/ask_dj/message", missing_behavior: "use_http" },
  ask_dj_history: {
    available: true,
    preferred_transport: "websocket",
    http_paths: {
      history: "/api/djconnect/v1/ask_dj/history",
      clear: "/api/djconnect/v1/ask_dj/history/clear",
    },
    missing_behavior: "use_http",
  },
  backend_commands: { available: true, preferred_transport: "websocket", http_path: "/api/djconnect/v1/command", missing_behavior: "use_http" },
  track_insight: { available: true, preferred_transport: "websocket", http_path: "/api/djconnect/v1/track_insight", missing_behavior: "use_http" },
  music_dna: {
    available: true,
    preferred_transport: "websocket",
    http_paths: {
      profile: "/api/djconnect/v1/music_dna/profile",
      settings: "/api/djconnect/v1/music_dna/settings",
      clear: "/api/djconnect/v1/music_dna/clear",
      import: "/api/djconnect/v1/music_dna/import",
      export: "/api/djconnect/v1/music_dna/export",
    },
    missing_behavior: "use_http_or_hide_feature",
  },
  music_discovery: {
    available: true,
    preferred_transport: "websocket",
    http_paths: {
      feed: "/api/djconnect/v1/music_discovery",
      refresh: "/api/djconnect/v1/music_discovery/refresh",
      play: "/api/djconnect/v1/music_discovery/play",
    },
    missing_behavior: "use_http_or_hide_feature",
  },
  music_discovery_feedback: {
    available: true,
    preferred_transport: "websocket",
    http_path: "/api/djconnect/v1/music_discovery/feedback",
    missing_behavior: "hide_negative_feedback_controls",
  },
};

const FEATURES = {
  ask_dj_chat: true,
  ask_dj_history: true,
  ask_dj_idle_suggestion: true,
  backend_commands: true,
  track_insight: true,
  music_dna: true,
  music_discovery: true,
  music_discovery_feedback: true,
};

const CONTRACT_SOURCE = {
  repo: "pcvantol/djconnect",
  files: [
    "custom_components/djconnect/const.py",
    "custom_components/djconnect/http.py",
    "custom_components/djconnect/api_handlers.py",
    "custom_components/djconnect/websocket_api.py",
    "tests/test_music_discovery.py",
    "tests/test_music_dna_api_handlers.py",
    "tests/test_vibecast.py",
    "tests/test_ask_dj_history.py",
  ],
};

function identity(overrides = {}) {
  return {
    device_id: DEVICE_ID,
    client_id: DEVICE_ID,
    client_type: CLIENT_TYPE,
    device_name: DEVICE_NAME,
    music_dna_key: MUSIC_DNA_KEY,
    ...overrides,
  };
}

module.exports = {
  CLIENT_TYPE,
  DEVICE_ID,
  DEVICE_NAME,
  DEVICE_TOKEN,
  MUSIC_DNA_KEY,
  HA_VERSION,
  HTTP_ROUTES,
  WS_COMMANDS,
  FALLBACKS,
  FEATURES,
  CONTRACT_SOURCE,
  identity,
};
