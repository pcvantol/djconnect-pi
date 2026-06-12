# DJConnect Pi Handoff

## Current State

This repo contains the initial Raspberry Pi Zero 2 W DJConnect client scaffold.
It is designed as a touch-only display remote for HyperPixel 4.0 Square Touch.

Implemented:

- Python package `djconnect-pi`
- Qt Quick/QML fullscreen 720x720 kiosk UI with PySide6 backend
- Dark DJConnect touch UI with blue/purple gradient backgrounds across the main
  screens, splash, games, logs and blocking overlays
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
- Release bundles include `docs/`, `src/`, `systemd/` and only
  `scripts/install_raspberry_pi.sh`, so a Pi can install the DJConnect app from
  the public distribution tarball without cloning the private source repo.
- Repo-only OS bootstrap helper `scripts/bootstrap_raspberry_pi_os.sh` handles
  timezone Amsterdam, SSH, apt full-upgrade, glances, Raspberry Pi Connect,
  Raspberry Pi OS dark-mode fallback, console boot and HyperPixel setup. It is
  intentionally excluded from release tarballs and from the app release cycle.
- The bootstrap helper configures Glances as a boot-started web UI on port
  `61208` using a dedicated `/opt/djconnect-glances` venv and
  `glances-web.service`. Do not use the distro `glances.service` for web mode;
  some Raspberry Pi OS package variants miss the required static web assets.
- systemd unit/timer templates
- release and cleanup scripts
- Install script targets a prepared Raspberry Pi OS 64-bit image, creates the
  runtime user, downloads the public release, installs dependencies inside the
  release venv, starts the local API daemon, and starts the Qt frontend
  automatically through `xinit`.
- Install script does not provision Wi-Fi or run OS bootstrap tasks. Hostname,
  Wi-Fi and locale are expected to be configured with Raspberry Pi Imager before
  first boot; the repo-only bootstrap helper covers the remaining OS setup.
- Install script is intended to be re-runnable for manual software updates. It
  keeps existing config, refreshes release files and systemd units, and restarts
  `djconnect-api.service` plus `djconnect-client.service`.
- Manual production update path is: download the current public
  `djconnect-pi-<version>.tar.gz`, extract it, run
  `sudo ./scripts/install_raspberry_pi.sh`. `git pull --ff-only` is only for
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
- Keep the local Client API separate from the UI process. The UI must not host
  the HTTP API or mDNS service; `djconnect-api.service` owns that.
- Keep unattended updates atomic under `/opt/djconnect/releases`.
- Manual production updates should use the public release tarball and rerun the
  installer; use `git pull --ff-only` only on development checkouts.
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
  tarball. Keep timezone, SSH, apt full-upgrade, glances, Raspberry Pi Connect,
  Raspberry Pi OS dark-mode fallback and HyperPixel setup in
  `scripts/bootstrap_raspberry_pi_os.sh`.
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
- When changing protocol behavior, sync `SYNC_PROMPTS.md` across all five repos.

## Verification So Far

- `python3 -m compileall src tests` passes.
- `bash -n scripts/install_raspberry_pi.sh scripts/bootstrap_raspberry_pi_os.sh cleanup_old_releases.sh release.sh`
  passes.
- Installer/release contract tests cover public release tarball examples,
  service restarts on rerun, release bundle contents, repo-only OS bootstrap
  separation and cleanup of old Actions runs.
- `QT_QPA_PLATFORM=offscreen python3 -m djconnect_pi.app --windowed --exit-after-ms 1500`
  loads the QML scene and exits cleanly.
- `python3 -m pytest` passes with the expanded suite; socket-bound Client API
  tests may skip in sandboxes that deny local bind.
