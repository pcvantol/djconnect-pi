"use strict";

const assert = require("assert/strict");
const { contractFixture, requestJson } = require("./contract_fixture");
const { CLIENT_TYPE, DEVICE_ID, DEVICE_NAME, DEVICE_TOKEN, COMPATIBILITY_HTTP_ROUTES, HTTP_ROUTES, identity } = require("./ha_contract");

const postPayloads = {
  "/api/djconnect/v1/pair": { ...identity({ music_dna_key: undefined }), pair_code: "123456" },
  "/api/djconnect/v1/status": { ...identity(), playback: { title: "Ordinary World", artist: "Duran Duran" } },
  "/api/djconnect/v1/command": { ...identity(), command: "play", value: "spotify:track:contract-1" },
  "/api/djconnect/v1/event": { ...identity(), event: "screen_on" },
  "/api/djconnect/v1/voice": { ...identity(), audio: "base64-wav-fixture" },
  "/api/djconnect/v1/ask_dj": { ...identity(), text: "Wat past hierbij?" },
  "/api/djconnect/v1/ask_dj/message": { ...identity(), client_message_id: "msg-1", text: "Wat past hierbij?" },
  "/api/djconnect/v1/ask_dj/clear": { ...identity() },
  "/api/djconnect/v1/ask_dj/idle_suggestion": { ...identity() },
  "/api/djconnect/v1/ask_dj/history/clear": { ...identity() },
  "/api/djconnect/v1/ask_dj/history/export": { ...identity() },
  "/api/djconnect/v1/ask_dj/history_state": { ...identity({ since_revision: 0 }) },
  "/api/djconnect/v1/music_dna/profile": { ...identity() },
  "/api/djconnect/v1/music_dna/settings": { ...identity(), enabled: true },
  "/api/djconnect/v1/music_dna/clear": { ...identity() },
  "/api/djconnect/v1/music_dna/import": { ...identity(), profile: { summary: "Imported" } },
  "/api/djconnect/v1/music_dna/export": { ...identity() },
  "/api/djconnect/v1/music_discovery/refresh": { ...identity() },
  "/api/djconnect/v1/music_discovery/play": { ...identity(), section_id: "new_for_you", discovery_item_id: "disc-1" },
  "/api/djconnect/v1/music_discovery/feedback": { ...identity(), section_id: "new_for_you", discovery_item_id: "disc-1", feedback: "not_for_me" },
  "/api/djconnect/v1/track_insight": { ...identity(), track: { title: "Ordinary World", artist: "Duran Duran" } },
  "/api/djconnect/v1/websocket/session": { device_id: DEVICE_ID, client_type: CLIENT_TYPE, requested_commands: ["djconnect/command"] },
};

function concrete(path) {
  return path.replace("{token}.{extension}", "sample.mp3").replace("{token}", "cover-token");
}

(async () => {
  await contractFixture(async (fixture) => {
    for (const route of COMPATIBILITY_HTTP_ROUTES) {
      assert(HTTP_ROUTES.some(([, candidate]) => candidate === route), `${route} must be fixture-covered if listed as compatibility`);
    }

    for (const [method, route] of HTTP_ROUTES) {
      const path = concrete(route);
      const isSession = route === "/api/djconnect/v1/websocket/session";
      const headers = isSession ? { authorization: `Bearer ${DEVICE_TOKEN}` } : {};
      const body = method === "POST" ? postPayloads[route] || identity() : undefined;
      const requestPath =
        route === "/api/djconnect/v1/music_discovery" || route === "/api/djconnect/v1/vibecast" || route === "/api/djconnect/v1/ask_dj/history"
          ? `${path}?device_id=${encodeURIComponent(DEVICE_ID)}&client_id=${encodeURIComponent(DEVICE_ID)}&client_type=${encodeURIComponent(CLIENT_TYPE)}&device_name=${encodeURIComponent(DEVICE_NAME)}`
          : path;
      const { status, data } = await requestJson(fixture.url, method, requestPath, body, headers);
      assert(status >= 200 && status < 300, `${method} ${route} returned ${status}: ${JSON.stringify(data)}`);
      if (data && Object.hasOwn(data, "success")) assert.equal(data.success, true, `${method} ${route} success`);
      if (route === "/api/djconnect/v1/music_discovery") {
        assert.deepEqual(data.sections.map((section) => section.id), ["new_for_you", "accepted_recommendations"]);
        assert.equal(data.sections[0].items[0].id, "disc-1");
        assert.equal(data.sections[0].items[0].quality_band, "strong");
      }
      if (route === "/api/djconnect/v1/ask_dj/history") {
        assert.equal(data.recently_played_history.items[0].playback_actions.length, 0);
      }
      if (route === "/api/djconnect/v1/music_dna/profile") {
        assert.equal(data.privacy_dashboard.stores_raw_audio, false);
      }
      if (route === "/api/djconnect/v1/vibecast") {
        assert.equal(data.context.artist, "Duran Duran");
      }
    }

    const protectedRoute = await requestJson(fixture.url, "POST", "/api/djconnect/v1/status", { ...identity({ client_type: "esp32" }) });
    assert.equal(protectedRoute.status, 400);
    assert.equal(protectedRoute.data.error, "invalid_identity");
  });
})().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
