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
- Separate GitHub release updater
- Separate apt maintenance command
- systemd unit/timer templates
- release and cleanup scripts

Not implemented by design:

- PTT
- microphone capture
- raw WAV upload to `/api/djconnect/voice`
- local TTS/DJ response playback
- local `/api/device/dj_response`
- ESP-only OTA, reboot, battery, Wi-Fi RSSI or screen entities

## Next Agent Checklist

- Keep the Pi client app-like, closer to iOS/macOS than ESP firmware.
- Preserve `client_type: raspberry_pi` in pairing and status payloads.
- Do not add voice/audio response features unless the product decision changes.
- Keep updater and OS maintenance separate from the UI process.
- Keep unattended updates atomic under `/opt/djconnect/releases`.
- When changing protocol behavior, sync `SYNC_PROMPTS.md` across all five repos.

## Verification So Far

- `python3 -m compileall src tests` passes.
- `QT_QPA_PLATFORM=offscreen python3 -m djconnect_pi.app --windowed --exit-after-ms 1500`
  loads the QML scene and exits cleanly.
- `python3 -m pytest` passes with 28 tests.
