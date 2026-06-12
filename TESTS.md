# Tests

Install development dependencies:

```sh
python3 -m pip install -e ".[dev]"
```

Run the full suite:

```sh
python3 -m pytest
```

Run syntax/package smoke checks:

```sh
python3 -m compileall src tests
QT_QPA_PLATFORM=offscreen python3 -m djconnect_pi.app --windowed --exit-after-ms 1500
```

## Coverage Areas

- config creation, persistence and device ID backfill
- Home Assistant pairing/status/command payloads
- local Client API info, pairing-info, pair, command, DJ response auth and mDNS
  TXT properties
- separate Client API daemon event bridge for DJ responses
- installer/systemd contract for separate API and touch UI services
- release bundle contract for including install scripts, docs, source and
  systemd units
- installer contract for modern HyperPixel KMS DPI overlay setup and
  Raspberry Pi OS dark-mode fallback configuration
- config private permissions and atomic-write behavior
- Raspberry Pi system-info logging
- debug logging paths for invalid HA JSON and local API request limits
- backend notification toast state
- playback response alias parsing
- HA major/minor version compatibility checks and blocking mismatch behavior
- protocol mismatch error handling
- PySide backend properties and command dispatch
- persistent logging and redaction
- bundled QML files and offscreen QML load
- startup splash, blocking pairing screen, tap-to-wake blanking and toast QML
  contract checks
- dark DJConnect blue/purple gradient QML theme contract checks
- blocking version-mismatch QML contract checks
- touch-only games panel packaging and four-game QML contract checks
- updater release asset selection, SHA256 verification and atomic install
- updater stable/beta prerelease channel handling
- apt maintenance windows, upgrade command flow and reboot gating
