# DJConnect Pi Handoff

## Current State

This repo contains the initial Raspberry Pi Zero 2 W DJConnect client scaffold.
It is designed as a touch-only display remote for HyperPixel 4.0 Square Touch.

Implemented:

- Python package `djconnect-pi`
- Qt Quick/QML fullscreen 720x720 kiosk UI with PySide6 backend
- `client_type: raspberry_pi`
- Stable device ID prefix `djconnect-raspberry-pi-`
- Pair/status/command calls to the Home Assistant DJConnect API
- Separate `djconnect-pi-api` daemon for HA -> Pi pairing, command, forget and
  text DJ response
- `_djconnect._tcp` mDNS advertisement from `djconnect-api.service`
- Full-screen startup splash with DJConnect banner and spinner
- Blocking first-run pairing screen with Client API URL and pairing code input
- Blocking Home Assistant version-mismatch screen. For example, client `3.1.z`
  accepts HA `>=3.1.0` and `<3.2.0`; mismatch triggers
  `djconnect-updater.service` once.
- Backend-driven notification toast for short user/action feedback
- Touch-only local games matching the Apple app set: Paddle Rally, Meteor Run,
  Sky Dash and Maze Chase.
- Separate GitHub release updater
- Separate apt maintenance command
- Persistent rotating file logging with sensitive-message redaction
- Startup Raspberry Pi system-info logging for UI and API daemon
- Debug logging around HA/API calls, HTTP status codes, JSON parse failures,
  exceptions and touch user actions
- Configurable screen blanking from the touch settings panel. Default is 120
  seconds and tap wakes the rendered screen.
- Configurable app-level brightness from the touch settings panel
- Local language setting. First value comes from Raspberry Pi OS locale, not
  Home Assistant pairing provisioning.
- Local demo mode before pairing. It must not store a bearer token or send HA
  traffic.
- Stable/beta client update channel setting
- App updates default to the public distribution repo
  `pcvantol/djconnect-pi-releases`.
- GitHub Actions workflow publishes tagged release assets from this source repo
  to the public distribution repo. It requires the source repo secret
  `DJCONNECT_RELEASES_TOKEN`.
- systemd unit/timer templates
- release and cleanup scripts
- Install script targets Raspberry Pi OS Desktop/GUI 64-bit, switches boot to
  console, starts the local API daemon, and starts the Qt frontend automatically
  through `xinit`.

Not implemented by design:

- PTT
- microphone capture
- raw WAV upload to `/api/djconnect/voice`
- local TTS/DJ response audio playback
- ESP-only OTA, reboot, battery, Wi-Fi RSSI or screen entities

## Next Agent Checklist

- Keep the Pi client app-like, closer to iOS/macOS than ESP firmware.
- Preserve `client_type: raspberry_pi` in pairing and status payloads.
- Preserve HA/client major-minor version compatibility checks. Do not silently
  ignore explicit `ha_version` or `ha_major_minor` mismatches.
- Do not add voice/audio response features unless the product decision changes.
- Keep updater and OS maintenance separate from the UI process.
- Keep the local Client API separate from the UI process. The UI must not host
  the HTTP API or mDNS service; `djconnect-api.service` owns that.
- Keep unattended updates atomic under `/opt/djconnect/releases`.
- Keep source and distribution repos separate unless the product decision
  changes: source is `pcvantol/djconnect-pi`, public release assets are in
  `pcvantol/djconnect-pi-releases`.
- Keep the Client API app-like. Do not add ESP OTA routes.
- `POST /api/device/dj_response` is accepted by the API daemon, written to the
  local DJ-response event file, displayed by the UI, and reports
  `audio_played:false` unless real Pi audio support is explicitly added later.
- Keep logs free of bearer tokens, HA tokens, Spotify secrets and Wi-Fi
  passwords. `logging_config.py` redacts obviously sensitive messages.
- Keep language client-owned for Raspberry Pi, just like iOS/macOS. Only ESP
  should consume HA language provisioning.
- Keep local games client-only. They must not require HA pairing, keyboard input
  or backend traffic.
- Screen blanking is implemented in the QML layer as a black wake-on-tap
  overlay; OS-level DPMS control is not yet wired.
- Brightness is implemented as QML dimming; hardware backlight control still
  needs HyperPixel validation before using sysfs or DRM controls.
- When changing protocol behavior, sync `SYNC_PROMPTS.md` across all five repos.

## Verification So Far

- `python3 -m compileall src tests` passes.
- `QT_QPA_PLATFORM=offscreen python3 -m djconnect_pi.app --windowed --exit-after-ms 1500`
  loads the QML scene and exits cleanly.
- `python3 -m pytest` passes with the expanded suite; socket-bound Client API
  tests may skip in sandboxes that deny local bind.
