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
- Home Assistant command payloads include `device_id` and
  `client_type=raspberry_pi`
- local Client API info, pairing-info, pair, command, DJ response auth and mDNS
  TXT properties
- Raspberry Pi-specific local Client API restart/shutdown endpoints, including
  bearer-token auth, optional device-id header validation and JSON responses
- mDNS discovery is suppressed while the Pi is paired and can return after
  pairing is reset/forgotten
- separate Client API daemon event bridges for queued HA commands and DJ
  response toasts
- installer/systemd contract for separate API and touch UI services
- systemd startup contract that the touch client pulls in the updater service
  on boot/start before the UI process starts
- installer contract for the narrow reboot, shutdown and update-check sudoers
  rule used by the touch/web UI, including absolute `systemctl` paths and
  `visudo -cf` validation
- web portal contract for save-on-change Settings, warning-styled reboot,
  refresh busy states, clipboard feedback and newest-log scrolling
- touch UI contract for Settings power/update actions, output-device "Geen",
  warning-styled reboot, wrapped Logs text, macOS-style toast presentation,
  queue `play_context_at` routing and playlist item command routing
- release bundle contract for including docs, systemd units, `scripts/install.sh`
  and a bundled wheel without the loose `src/` app source tree
- repo-only OS bootstrap contract for Raspberry Pi OS Lite 64-bit, modern
  HyperPixel KMS DPI overlay setup, root filesystem expansion, persistent 1GB
  swapfile, boot-time filesystem repair checks for unsafe power-loss recovery,
  timezone, NTP time synchronization, SSH, apt full-upgrade, minimal X11/Qt
  runtime dependencies and Raspberry Pi Connect
- installer contract that OS bootstrap tasks stay out of the app release cycle
- technical design decisions documentation is linked from README and contains
  dependency/style/release-maintenance sections
- release hygiene points to canonical `pcvantol/djconnect/SYNC_PROMPTS.md` and
  `pcvantol/djconnect/PRODUCT_ROADMAP.md`; local copies are forbidden
- installer contract for rerunnable manual updates: existing config is kept,
  systemd units are refreshed, and API/UI services are restarted
- installer contract for early free-space and active-swap checks before large
  PySide6 downloads
- installer contract for resource snapshots, inode reporting, CPU/Python/path/
  GitHub/thermal checks and incomplete `.venv` cleanup before dependency retry
- installer contract for disabling the old updater/client before manual
  installs and for per-package dependency markers under release `.install-state`
- bootstrap/README contract that public release download examples match the
  current project version
- config private permissions and atomic-write behavior
- Raspberry Pi system-info logging
- debug logging paths for invalid HA JSON and local API request limits
- Home Assistant 401 authentication errors and backend-unavailable responses
  are parsed into specific user-facing backend states instead of raw JSON/status
  text
- backend availability property coverage for red/green kiosk connection status
- local Client API debug screenshot route, API-daemon screenshot event file and
  QML `grabToImage` capture contract
- loopback-only local Client API debug screen switching and screenshot
  response coverage
- backend notification toast state
- auth/backend toast suppression while the Pi is waiting on the blocking
  pairing screen
- playback response alias parsing
- playback output-device response parsing, `set_output` command dispatch and
  fallback HA `devices` command loading when status omits the device list
- playback refresh contract that Now Playing album art is cached locally before
  QML renders it
- Home Assistant playback contract coverage for no-active-playback status
  snapshots, empty HTTP 2xx body errors, HTTP 401/403/404 auth failures,
  `success:true` empty playback command responses, `devices`/`outputs` aliases,
  nested playlist response shapes and queue/playlist decoding up to 100 items
- live output-device validation and rollback coverage when HA rejects a
  selected output device
- queue loading contract sends `command:"queue"` with `limit=100`
- queue row playback contract sends `command:"play_context_at"` with nested
  `value.uri`, keeps direct Spotify episode/track URIs playable without
  context and preserves context plus offset behavior for playlist, album and
  show contexts
- playlist loading contract sends `command:"playlists"` with `limit=100` from
  both the touch UI and web portal state endpoint
- installer/updater contract that pip self-upgrade is skipped by default and can
  still be forced with `DJCONNECT_UPGRADE_PIP=1`
- shared `examples/voice_intents.json` availability for website/docs alignment
  without enabling local Raspberry Pi voice capture
- HA major/minor version compatibility checks and blocking mismatch behavior
- protocol mismatch error handling
- PySide backend properties and command dispatch
- persistent logging and redaction
- bundled QML files and offscreen QML load
- startup splash, blocking pairing screen, tap-to-wake blanking, wake refresh,
  navigation idle-timer restart, splash-on-wake and toast QML contract checks
- previous/next wake-screen signal coverage, including HA command-event
  previous/next
- modal overlay touch-blocking, settings reset-pairing/reboot confirmation,
  opaque Logs/Over/Instellingen backgrounds and About full-width website
  contract checks
- generated six-digit pairing code persistence and `/api/device/pairing-info`
  aliases
- dark DJConnect blue/purple gradient QML theme contract checks
- transparent rounded touch button, readable logs, scrollable settings, About,
  queue and playlist QML contract checks
- Games screen full-background touch blocking so Speelt nu controls cannot be
  tapped through transparent game areas
- touch-friendly icon bottom navigation order, height, selected-state checks
  and the dedicated Bediening tab
- shared AppBackground gradient, display-only Speelt nu checks and enlarged
  Bediening playback-control sizing checks, including that Speelt nu album art
  has no play/pause overlay
- Maze Chase power-pellet and vulnerable ghost QML contract checks
- Empty queue/playlist labels and backend behavior that only loads demo media
  after explicitly entering demo mode
- kiosk branding contract checks for the bundled app icon, no visible quit
  action, explicit media-row geometry with fixed-size media play buttons and
  settings without pairing controls
- compact touch log formatting and 24-hour album-art cache helper behavior
- bounded log tail reading before QML log display formatting
- HA queue/playlist media parser coverage for artwork aliases from the shared
  contract
- backend media-list artwork background-cache coverage so Queue/Playlists show
  rows immediately, cache only the first visible batch and keep album art
  without blocking QML delegates
- QML memory-pressure checks for artwork `sourceSize` bounds and disabled
  dynamic image cache retention
- backend guard coverage that duplicate queue/playlist loads are skipped while
  a matching request is already in flight
- opaque queue/playlist main screens, manual refresh controls and no
  DJ-response dismiss dialog in QML
- web portal Diagnostics rendering plus daemon-side systemd status
  normalization for running/stopped/failed/unknown component health
- volume cap at 60, fixed screen-timeout dropdown, anchored media-row geometry
  and reboot sudoers contract coverage
- local Client API pairing-info and logging regression coverage, plus Postman
  collection endpoint contract checks
- game title QML contract checks ensuring titles come from translation keys
- blocking version-mismatch QML contract checks
- touch-only games panel packaging and four-game QML contract checks
- updater release asset selection, SHA256 verification, top-level tarball
  directory stripping, bundled-wheel venv installation and atomic activation
- updater post-install cleanup of old release directories while keeping the
  active release and one rollback release
- updater pip install environment coverage for cache-local temp files under
  `/var/cache/djconnect-pip`
- updater dependency install coverage for resumable marked steps, including
  shiboken6, PySide6 Essentials, PySide6 Addons, PySide6, requests, zeroconf
  and the bundled wheel
- updater stable/beta prerelease channel handling
- apt maintenance windows, upgrade command flow and reboot gating
