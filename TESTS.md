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
- Dutch/English translation key parity and selected user-facing copy checks
- Home Assistant pairing/status/command payloads
- local Client API info, pairing-info, pair, command, DJ response auth and mDNS
  TXT properties
- separate Client API daemon event bridge for DJ responses
- installer/systemd contract for separate API and touch UI services
- release bundle contract for including docs, systemd units, `scripts/install.sh`
  and a bundled wheel without the loose `src/` app source tree
- repo-only OS bootstrap contract for Raspberry Pi OS Lite 64-bit, modern
  HyperPixel KMS DPI overlay setup, root filesystem expansion, persistent 1GB
  swapfile, timezone, SSH, apt full-upgrade, minimal X11/Qt runtime dependencies
  and Raspberry Pi Connect
- installer contract that OS bootstrap tasks stay out of the app release cycle
- installer contract for rerunnable manual updates: existing config is kept,
  systemd units are refreshed, and API/UI services are restarted
- installer contract for early free-space and active-swap checks before large
  PySide6 downloads
- installer contract for resource snapshots, inode reporting, CPU/Python/path/
  GitHub/thermal checks and incomplete `.venv` cleanup before dependency retry
- bootstrap/README contract that public release download examples match the
  current project version
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
- generated six-digit pairing code persistence and `/api/device/pairing-info`
  aliases
- dark DJConnect blue/purple gradient QML theme contract checks
- transparent rounded touch button, readable logs, scrollable settings, About,
  queue and playlist QML contract checks
- kiosk branding contract checks for the bundled app icon, no visible quit
  action, fixed-size media play buttons and settings without pairing controls
- compact touch log formatting and 24-hour album-art cache behavior
- HA queue/playlist media parser coverage for artwork aliases from the shared
  contract
- game title QML contract checks ensuring titles come from translation keys
- blocking version-mismatch QML contract checks
- touch-only games panel packaging and four-game QML contract checks
- updater release asset selection, SHA256 verification, top-level tarball
  directory stripping, bundled-wheel venv installation and atomic activation
- updater post-install cleanup of old release directories while keeping the
  active release and one rollback release
- updater pip install environment coverage for cache-local temp files under
  `/var/cache/djconnect-pip`
- updater stable/beta prerelease channel handling
- apt maintenance windows, upgrade command flow and reboot gating
