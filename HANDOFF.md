# DJConnect Pi Handoff

## Current State

This repo contains the initial Raspberry Pi Zero 2 W DJConnect client scaffold.
It is designed as a touch-only display remote for HyperPixel 4.0 Square Touch.

Implemented:

- Python package `djconnect-pi`
- Qt Quick/QML fullscreen 720x720 kiosk UI with PySide6 backend
- Dark DJConnect touch UI with blue/purple gradient backgrounds across the main
  screens, splash, games, logs and blocking overlays
- Bottom navigation is a larger touch-friendly icon+label bar ordered Speelt
  nu, Bediening, Wachtrij, Afspeellijsten, Games, Instellingen.
- Speelt nu is display-focused: status, refresh, large album art and
  title/artist. It no longer sends hidden playback commands from cover taps or
  swipes.
- Bediening is the dedicated touch-control screen with enlarged previous,
  play/pause, next, track progress, volume, output-device, shuffle and repeat
  controls.
- Volume control is capped at HA value 60. The UI presents value 60 as 100% so
  the wall device cannot accidentally exceed the intended maximum loudness.
- Screen timeout is a fixed dropdown with 30, 60, 90, 120, 180, 240, 300 and
  600 second options.
- `client_type: raspberry_pi`
- Stable device ID prefix `djconnect-raspberry-pi-`
- Pair/status/command calls to the Home Assistant DJConnect API
- Pair/status/command payloads include `client_type: raspberry_pi`; command
  payloads must not regress to command-only bodies because HA validates the
  client family.
- Separate `djconnect-pi-api` daemon for HA -> Pi pairing, command, forget and
  text DJ response
- HA initiated `/api/device/command` calls are queued by the API daemon in a
  local command-event file and executed by the UI process. This keeps the API
  daemon responsive while allowing playback commands such as previous/next to
  affect the live touch client.
- The local API daemon reloads shared config before serving info/pairing-info
  and before local pairing, so reset-pairing code rotation is immediately
  visible to HA mDNS discovery/config-flow.
- Local API pairing stops mDNS immediately; local API forget/reset clears the
  token, marks the device unpaired, rotates the pairing code and allows mDNS
  rediscovery again.
- `_djconnect._tcp` mDNS advertisement from `djconnect-api.service` only while
  the Pi is not paired. After successful pairing the local API keeps running,
  but discovery is stopped so the device no longer appears as a pairing
  candidate in Home Assistant.
- Full-screen startup splash with DJConnect banner and spinner
- Blocking first-run pairing screen with Client API URL and pairing code input
- Blocking Home Assistant version-mismatch screen. For example, client `3.1.z`
  accepts HA `>=3.1.0` and `<3.2.0`; mismatch triggers
  `djconnect-updater.service` once.
- Backend-driven notification toast for short user/action feedback. Textual DJ
  responses from HA are shown as an auto-dismissing 10-second toast, not as a
  blocking dialog.
- Touch-only local games matching the Apple app set: Paddle Rally, Meteor Run,
  Sky Dash and Maze Chase.
- Maze Chase includes a slower ghost, a large power pellet and a temporary
  blinking edible ghost state.
- The Games main screen consumes touch input across its full background so
  underlying Speelt nu controls cannot be activated through transparent or
  empty game areas.
- Separate GitHub release updater
- Separate apt maintenance command
- Persistent rotating file logging with sensitive-message redaction
- Startup Raspberry Pi system-info logging for UI and API daemon
- Debug logging around HA/API calls, HTTP status codes, JSON parse failures,
  exceptions and touch user actions
- HA calls and backend workers log elapsed time for pair/status/command,
  refresh, playback commands, queue loads, playlist loads and artwork caching
  so Pi responsiveness regressions can be traced from persistent logs.
- Home Assistant 401 responses are parsed as authentication failures instead of
  showing raw JSON on the kiosk screen. The user gets a concise toast/status and
  the connection dot turns red until a successful refresh restores backend
  health.
- Home Assistant `success:false` with `backend_available:false` is treated as a
  music-backend-unavailable state and shown as a short translated status/toast.
- Configurable screen blanking from the touch settings panel. Default is 120
  seconds and tap wakes the rendered screen.
- When the screen wakes from the blanked state, the DJConnect startup splash is
  shown briefly again before returning to the kiosk UI.
- Previous/next track actions wake the rendered screen for 10 seconds, also
  when they arrive from Home Assistant through `/api/device/command`.
- Configurable app-level brightness from the touch settings panel
- Settings shows "Instellingen", uses label/value rows for read-only values
  such as Device ID and Home Assistant URL, has a red "Opnieuw koppelen" action
  with a confirmation screen, a "Logs" button, no local Close button and a
  reboot/shutdown buttons with confirmation.
- The reboot/shutdown buttons and the manual update-check action use the
  installer-created narrow passwordless sudoers rule and try absolute systemctl
  paths first from the `djconnect` runtime user.
- Bediening has a local-only "Geen" output device option; it never sends that
  placeholder to Home Assistant.
- Full-screen QML overlays consume touch input so underlying controls cannot be
  activated through logs/about/pairing/version/confirmation screens.
- Logs, Over and Instellingen are opaque full-screen views, not translucent
  overlays on top of Speelt nu.
- Queue and playlist screens are opaque full main screens, not translucent
  overlays over Speelt nu.
- Real Home Assistant empty queue/playlist responses stay empty and show
  "Geen wachtrij" or "Geen afspeellijsten"; demo queue/playlist samples are
  only shown while local demo mode is active.
- Queue loading follows the shared HA contract and requests at most 100 items:
  `command:"queue"` with `limit:100`.
- Bediening exposes the HA-provided playback output-device list and dispatches
  output selection with `command:"set_output"`. If the HA status response omits
  the list, the client asks HA for `command:"devices"` as a fallback.
- Output-device changes are validated live against the HA response. Rejected
  output selections roll back to the previous device and are logged.
- Wachtrij and Afspeellijsten emit HA-provided row data immediately after the
  HA response and cache album art afterward on a background worker. Blocking
  network or disk work in media-list delegates, or before list emission, caused
  touch UI hangs on Pi Zero 2 W.
- The Logs screen reads a bounded tail of the persistent log file before compact
  formatting, so a large rotated log cannot freeze the kiosk UI.
- Wachtrij and Afspeellijsten use explicit artwork/text/play-button geometry
  instead of a delegate `RowLayout` or cross-item anchors; this avoids missing
  titles, subtitles and play icons on the HyperPixel runtime.
- Queue/playlist load requests are deduplicated while a matching request is in
  flight, so repeated navigation taps cannot flood Home Assistant or the QML
  thread.
- `GET /api/debug/screenshot` on the local API asks the QML UI process to save
  a PNG of the live scenegraph. Once paired, the endpoint requires the device
  bearer token for LAN callers, but loopback callers are allowed for SSH-based
  diagnostics and receive `content_base64`.
- `GET /api/debug/screen?screen=<name>` is loopback-only and queues a local
  debug screen event so release verification can capture Now Playing, Queue,
  Playlists, Games, Settings, Logs and About after deploy.
- The web portal is served by `djconnect-api.service`, so it is installed with
  the normal release bundle and starts automatically on boot/update with the
  local API daemon.
- The web portal Diagnostics block shows live Home Assistant API, local API,
  pairing and DJConnect systemd service/timer status as running, stopped,
  failed or unknown.
- The web portal playback controls follow the ESP portal style with large
  purple icon buttons, active shuffle/repeat states and a visible volume
  percentage.
- Local language setting. First value comes from Raspberry Pi OS locale, not
  Home Assistant pairing provisioning.
- Dutch/English translations are kept in `src/djconnect_pi/i18n.py`; tests
  assert key parity. QML game titles use translation keys, not hardcoded
  display strings.
- Local demo mode before pairing. It must not store a bearer token or send HA
  traffic.
- Stable/beta client update channel setting
- App updates default to the public distribution repo
  `pcvantol/djconnect-pi-releases`.
- GitHub Actions workflow publishes tagged release assets from this source repo
  to the public distribution repo. It requires the source repo secret
  `DJCONNECT_PI_RELEASES_TOKEN`.
- Release bundles include `docs/`, `systemd/`, `scripts/install.sh` and a
  prebuilt wheel under `wheels/`. They do not include the loose app source tree,
  so a Pi can install the DJConnect app from the public distribution tarball
  without cloning the private source repo.
- Repo-only OS bootstrap helper `scripts/bootstrap_raspberry_pi_os.sh` handles
  root filesystem expansion, persistent 1GB swapfile setup, automatic
  boot-time filesystem repair checks, timezone Amsterdam, NTP time
  synchronization, SSH, apt full-upgrade, Raspberry Pi Connect, console boot,
  minimal X11/Qt runtime dependencies and HyperPixel setup. It is
  intentionally excluded from release tarballs and from the app release cycle.
- systemd unit/timer templates
- release and cleanup scripts
- Standard release closeout should also run
  `./cleanup_old_releases.sh --keep 1 --public --execute` to clean old private
  and public releases/tags plus completed tag workflow runs.
- Product-level ideas, killer features, production must-haves and premium
  candidates are tracked only in canonical
  `pcvantol/djconnect/PRODUCT_ROADMAP.md`. Do not add a local copy in this
  repo; make a follow-up change/commit in `pcvantol/djconnect` when roadmap
  changes start from the Pi repo.
- Install script targets a prepared Raspberry Pi OS 64-bit image, creates the
  runtime user, downloads the public release, installs the bundled wheel and
  dependencies inside the release venv, starts the local API daemon, and starts
  the Qt frontend automatically through `xinit`.
- Install script does not provision Wi-Fi or run OS bootstrap tasks. Hostname,
  Wi-Fi and locale are expected to be configured with Raspberry Pi Imager before
  first boot; the repo-only bootstrap helper covers the remaining OS setup.
- Install script is intended to be re-runnable for manual software updates. It
  keeps existing config, refreshes release files and systemd units, and restarts
  `djconnect-api.service` plus `djconnect-client.service`.
- Install script writes `/etc/sudoers.d/djconnect-reboot` with a narrow
  passwordless rule for the runtime user to run only reboot, poweroff and
  `systemctl start djconnect-updater.service`, used by the touch UI power and
  update-check buttons.
- The unattended updater now mirrors the release installer path for public
  tarballs: it strips the top-level archive directory, installs the bundled
  wheel into `.venv`, validates all `djconnect-pi-*` console entrypoints and
  only then repoints `/opt/djconnect/current`.
- After a successful unattended install, the updater cleans
  `/opt/djconnect/releases` and keeps only the active release plus one rollback
  release. Hidden temporary unpack directories are removed as well.
- The unattended updater now also uses `/var/cache/djconnect-pip` and
  `/var/cache/djconnect-pip/tmp` for pip cache and temporary files, matching the
  public installer behavior during large PySide6 dependency installs.
- Install script is resumable across reboot/interruption. It stores markers in
  `/opt/djconnect/install-state/<version>/` for `release_unpacked` and
  `venv_ready`, uses `/var/cache/djconnect-pip` so large PySide6 downloads do
  not have to restart from zero, removes incomplete `.venv` directories before
  retrying, and uses a cache-local pip temp directory.
- Manual production update path is: download the current public
  `djconnect-pi-<version>.tar.gz`, extract it, run
  `sudo ./scripts/install.sh`. `git pull --ff-only` is only for
  development checkouts on the Pi.

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
- Keep release cleanup as a default post-release action, not an optional extra,
  unless the user explicitly asks to keep old releases.
- Keep `docs/TECHNICAL_DESIGN_DECISIONS.md` current for every release that
  changes code structure, design patterns, dependencies, OS packages, service
  boundaries or release/deploy flow.
- Keep the local Client API separate from the UI process. The UI must not host
  the HTTP API or mDNS service; `djconnect-api.service` owns that.
- Keep HA initiated `/api/device/command` execution bridged through the local
  command-event queue so the UI process, not the API daemon, applies playback
  actions.
- Keep unattended updates atomic under `/opt/djconnect/releases`.
- Manual production updates should use the public release tarball and rerun the
  installer; use `git pull --ff-only` only on development checkouts.
- If the Pi overheats/freezes during dependency install, reboot and rerun the
  same release installer command; do not delete `/opt/djconnect/install-state`
  or `/var/cache/djconnect-pip`.
- If dependency install fails with no space left, rerun the repo-only bootstrap
  so `raspi-config nonint do_expand_rootfs` can grow the root filesystem, reboot
  if needed, and rerun the same release installer command.
- If dependency install fails with missing/low swap, rerun the repo-only
  bootstrap so it can create and activate `/swapfile`, then rerun the same
  release installer command.
- Keep source and distribution repos separate unless the product decision
  changes: source is `pcvantol/djconnect-pi`, public release assets are in
  `pcvantol/djconnect-pi-releases`.
- Keep the Client API app-like. Do not add ESP OTA routes.
- `POST /api/device/dj_response` is accepted by the API daemon, written to the
  local DJ-response event file, displayed by the UI, and reports
  `audio_played:false` unless real Pi audio support is explicitly added later.
- Keep logs free of bearer tokens, HA tokens, Spotify secrets and Wi-Fi
  passwords. `logging_config.py` redacts obviously sensitive messages.
- Do not reintroduce Wi-Fi provisioning into the DJConnect installer; that
  belongs in Raspberry Pi Imager setup.
- Do not reintroduce OS bootstrap into the DJConnect app installer or release
  tarball. Keep timezone, SSH, apt full-upgrade, Raspberry Pi Connect,
  minimal X11/Qt runtime dependencies and HyperPixel setup in
  `scripts/bootstrap_raspberry_pi_os.sh`. Target Raspberry Pi OS Lite 64-bit,
  not the Desktop/GUI image.
- Keep language client-owned for Raspberry Pi, just like iOS/macOS. Only ESP
  should consume HA language provisioning.
- When adding user-facing text, add both Dutch and English translations and
  avoid hardcoded display strings in QML except brand names and icon-like
  controls such as `x`.
- Keep local games client-only. They must not require HA pairing, keyboard input
  or backend traffic.
- Screen blanking is implemented in the QML layer as a black wake-on-tap
  overlay; OS-level DPMS control is not yet wired.
- Brightness is implemented as QML dimming; hardware backlight control still
  needs HyperPixel validation before using sysfs or DRM controls.
- Performance follow-up candidates: reduce HA polling when idle, avoid
  unnecessary Canvas repaints, add a nonblocking background artwork pre-cache,
  cap log rendering size for the touch viewer, and profile PySide6 memory/CPU
  on the Pi Zero 2 W.
- When changing protocol behavior, update canonical
  `pcvantol/djconnect/SYNC_PROMPTS.md`. Do not add a local copy in this repo;
  make a follow-up change/commit in `pcvantol/djconnect` when the change starts
  from the Pi repo.
- When changing product roadmap scope, update canonical
  `pcvantol/djconnect/PRODUCT_ROADMAP.md`. Do not add a local copy in this
  repo.

## Verification So Far

- `python3 -m compileall src tests` passes.
- `bash -n scripts/install.sh scripts/bootstrap_raspberry_pi_os.sh cleanup_old_releases.sh release.sh`
  passes.
- Installer/release contract tests cover public release tarball examples,
  service restarts on rerun, release bundle contents, repo-only OS bootstrap
  separation, technical design documentation presence and cleanup of old
  Actions runs.
- `QT_QPA_PLATFORM=offscreen python3 -m djconnect_pi.app --windowed --exit-after-ms 1500`
  loads the QML scene and exits cleanly.
- `python3 -m pytest` passes with the expanded suite; socket-bound Client API
  tests may skip in sandboxes that deny local bind.
