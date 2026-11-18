"use strict";

const assert = require("assert/strict");
const { contractFixture, requestJson, wsExchange } = require("./contract_fixture");
const { CLIENT_TYPE, DEVICE_ID, DEVICE_TOKEN, WS_COMMANDS, identity } = require("./ha_contract");

const payloadFor = {
  "djconnect/command": { command: "play", value: "spotify:track:contract-1" },
  "djconnect/ask_dj/message": { client_message_id: "msg-1", text: "Wat past hierbij?" },
  "djconnect/ask_dj/history": { since_revision: 0 },
  "djconnect/ask_dj/history/clear": {},
  "djconnect/ask_dj/history/state": { since_revision: 0 },
  "djconnect/ask_dj/idle_suggestion": {},
  "djconnect/track_insight": { track: { title: "Ordinary World", artist: "Duran Duran" } },
  "djconnect/music_dna/profile": {},
  "djconnect/music_dna/settings": { enabled: true },
  "djconnect/music_dna/clear": {},
  "djconnect/music_dna/import": { profile: { summary: "Imported" } },
  "djconnect/music_dna/export": {},
  "djconnect/music_discovery/feed": {},
  "djconnect/music_discovery/refresh": {},
  "djconnect/music_discovery/play": { section_id: "new_for_you", discovery_item_id: "disc-1" },
  "djconnect/music_discovery/feedback": { section_id: "new_for_you", discovery_item_id: "disc-1", feedback: "less_like_this" },
};

(async () => {
  await contractFixture(async (fixture) => {
    const session = await requestJson(fixture.url, "POST", "/api/djconnect/v1/websocket/session", {
      device_id: DEVICE_ID,
      client_type: CLIENT_TYPE,
      requested_commands: WS_COMMANDS.concat(["djconnect/vibecast"]),
    });
    assert.equal(session.status, 200);
    assert.equal(typeof session.data.access_token, "string");
    assert.deepEqual(session.data.commands, WS_COMMANDS);
    assert(!session.data.commands.includes("djconnect/vibecast"), "VibeCast must stay HTTP-only unless HA advertises a WS command");
    assert.equal(fixture.state.sessionRequests[0].device_id, DEVICE_ID);
    assert.equal(fixture.state.sessionRequests[0].client_type, CLIENT_TYPE);
    assert(!Object.keys(fixture.state.sessionRequests[0]).some((key) => /ha.*token|long_lived/i.test(key)));

    for (const command of WS_COMMANDS) {
      const result = await wsExchange(fixture.url, command, payloadFor[command] || {});
      assert.equal(result.type, "result", command);
      assert.equal(result.success, true, command);
      assert.equal(result.result.success, true, command);
      if (command === "djconnect/music_discovery/play") {
        assert.equal(result.result.section_id, "new_for_you");
        assert.equal(result.result.discovery_item_id, "disc-1");
      }
      if (command === "djconnect/music_discovery/feed") {
        assert.equal(result.result.sections[0].items[0].id, "disc-1");
      }
    }

    const vibecast = await requestJson(
      fixture.url,
      "GET",
      `/api/djconnect/v1/vibecast?device_id=${DEVICE_ID}&client_id=${DEVICE_ID}&client_type=${CLIENT_TYPE}`,
      undefined
    );
    assert.equal(vibecast.status, 200);
    assert.equal(vibecast.data.context.title, "Ordinary World");
  });

  await contractFixture(async (fixture) => {
    const wsResult = await wsExchange(fixture.url, "djconnect/music_discovery/feedback", {
      section_id: "new_for_you",
      discovery_item_id: "disc-1",
      feedback: "hide_artist",
    });
    assert.equal(wsResult.success, true);
  }, { commands: WS_COMMANDS.filter((command) => command !== "djconnect/vibecast") });

  await contractFixture(async (fixture) => {
    const fallbackOnlyCommands = WS_COMMANDS.filter((command) => command !== "djconnect/music_discovery/feedback");
    assert(!fallbackOnlyCommands.includes("djconnect/music_discovery/feedback"));
    const httpFallback = await requestJson(fixture.url, "POST", "/api/djconnect/v1/music_discovery/feedback", {
      ...identity(),
      section_id: "new_for_you",
      discovery_item_id: "disc-1",
      feedback: "not_for_me",
    });
    assert.equal(httpFallback.status, 200);
    assert.equal(httpFallback.data.feedback_recorded, true);
  }, { commands: WS_COMMANDS.filter((command) => command !== "djconnect/music_discovery/feedback") });
})().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
