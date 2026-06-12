# DJConnect Pi

Version: `3.1.1`

Raspberry Pi Zero 2 W touch-display client for DJConnect. This client uses
Qt Quick/QML with a PySide6 backend and is meant for a Pimoroni HyperPixel 4.0
Square Touch style kiosk remote: pairing, status, now playing and playback
controls only.

It intentionally does not implement PTT, microphone upload, local DJ response
audio, ESP firmware OTA, ESP battery sensors, Wi-Fi RSSI sensors or a local
`/api/device/dj_response` endpoint.

## Client Contract

- `client_type`: `raspberry_pi`
- Device ID: `djconnect-raspberry-pi-XXXXXXXXXXXX`
- Home Assistant endpoints:
  - `POST /api/djconnect/pair`
  - `POST /api/djconnect/status`
  - `POST /api/djconnect/command`
- Supported commands:
  - `status`
  - `play`
  - `pause`
  - `next`
  - `previous`
  - `set_volume`
  - `set_shuffle`
  - `set_repeat`

## UI Shape

The app is a 720x720 fullscreen touch remote:

- album art area / status area in the center
- large play/pause button
- previous/next buttons left and right
- bottom volume slider
- shuffle and repeat toggles
- compact HA/pairing/backend status
- settings for screen blanking and stable/beta update channel
- persistent rotating client log

## Quick Start

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
djconnect-pi-client --ha-url http://homeassistant.local:8123
```

Use `--windowed` during desktop development.

For a headless smoke test:

```sh
QT_QPA_PLATFORM=offscreen djconnect-pi-client --windowed --exit-after-ms 1500
```

On first launch, enter the pairing code shown by Home Assistant. The client
stores config under `~/.config/djconnect-pi/config.json` unless `--config` is
provided.

## Unattended Updates

The updater is a separate process from the UI app. It checks GitHub Releases,
downloads a tarball asset and optional `.sha256`, installs into:

```text
/opt/djconnect/releases/<version>
/opt/djconnect/current -> /opt/djconnect/releases/<version>
```

It then restarts `djconnect-client.service`. App updates are atomic at the
symlink level and preserve config outside the release directory.

Set the updater channel to `stable` for normal releases or `beta` to allow
GitHub prereleases.

OS maintenance is also separate. The maintenance command can run apt update,
upgrade and reboot only when `/var/run/reboot-required` exists, optionally
inside a configured maintenance window.

See `systemd/` for service and timer templates.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Bootstrap a Pi Zero 2 W + HyperPixel](docs/BOOTSTRAP.md)
- [Performance and Security Review](docs/PERFORMANCE_SECURITY.md)
- [Handoff](HANDOFF.md)
- [Changelog](CHANGELOG.md)
- [Issues](ISSUES.md)
- [Todo](TODO.md)
- [Tests](TESTS.md)
