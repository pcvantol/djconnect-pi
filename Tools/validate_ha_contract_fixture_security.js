"use strict";

const assert = require("assert/strict");
const { contractFixture, requestJson, wsExchange, redact } = require("./contract_fixture");
const { DEVICE_ID, CLIENT_TYPE, DEVICE_TOKEN, WS_COMMANDS, CONTRACT_SOURCE, HTTP_ROUTES } = require("./ha_contract");

const SECRET_VALUES = [
  "ci-device-token",
  "ha-ws-session-token",
  "central-proof-secret",
  "apns-secret-token",
  "install-secret-token",
  "Bearer ci-device-token",
];

function serialized(value) {
  return JSON.stringify(value);
}

(async () => {
  assert(CONTRACT_SOURCE.files.includes("custom_components/djconnect/websocket_api.py"));
  assert(CONTRACT_SOURCE.files.includes("custom_components/djconnect/http.py"));
  assert(HTTP_ROUTES.some(([method, route]) => method === "GET" && route === "/api/djconnect/v1/vibecast"));
  assert(!WS_COMMANDS.includes("djconnect/vibecast"), "Fixture must not advertise a VibeCast WS route not present in HA");

  await contractFixture(async (fixture) => {
    const session = await requestJson(
      fixture.url,
      "POST",
      "/api/djconnect/v1/websocket/session",
      {
        device_id: DEVICE_ID,
        client_type: CLIENT_TYPE,
        requested_commands: WS_COMMANDS,
        central_api_bootstrap_proof: "central-proof-secret",
        apns_token: "apns-secret-token",
        ha_install_id: "install-secret-token",
      },
      { authorization: `Bearer ${DEVICE_TOKEN}` }
    );
    assert.equal(session.status, 200);
    await wsExchange(fixture.url, "djconnect/command", { command: "pause", authorization: "Bearer ci-device-token" });

    const output = serialized(fixture.state);
    for (const secret of SECRET_VALUES) {
      assert(!output.includes(secret), `Secret leaked in fixture state: ${secret}`);
    }
    assert(output.includes("<redacted>"), "Fixture should retain redacted markers for security debugging");
    assert.equal(redact({ device_token: "x", nested: { authorization: "Bearer y" } }).device_token, "<redacted>");
  });
})().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
