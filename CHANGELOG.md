# Changelog

## 3.1.46

- Locked the Pi queue request to the shared HA contract limit:
  `command:"queue"` is sent with `limit:100`.
- Added backend contract coverage for the queue limit and fixed the GitHub
  Actions debug-screen test expectation so public release publishing can pass.

## 3.1.45

- Added loopback-only debug automation for deployed Pi screenshots:
  `GET /api/debug/screen?screen=<name>` switches the UI screen through the
  local command-event bridge, and `GET /api/debug/screenshot` may be called
  from `127.0.0.1` without exposing the device bearer token over LAN.
- The screenshot response now includes `content_base64` for SSH-based
  diagnostic capture so release deploy verification can attach actual PNGs.
- Added backend, local API and QML tests for the debug screen/screenshot path.

## 3.1.44

- Fixed Wachtrij/Afspeellijsten media-row rendering by replacing the delegate
  `RowLayout` with explicit anchored artwork, text and fixed-size play button
  positioning.
- Removed the unsupported speaker emoji from Speelt nu and kept the
  output-device selector functional with a fallback HA `devices` command when
  status does not include the device list.
- Made Instellingen, Over and Logs opaque full-screen views instead of
  translucent overlays, and disabled horizontal scrolling in Instellingen and
  Over.
- Changed the Home Assistant URL in Instellingen to a label/value row, made the
  Device ID row consistent, removed the no-voice explanatory text and changed
  the save toast to "Instellingen opgeslagen".
- Added an Apparaat herstarten confirmation dialog and kept the actual reboot
  action behind the existing narrow systemctl sudoers rule.
- Replays the DJConnect splash briefly when the screen wakes from the blanked
  state.
- Aligned the Speelt nu refresh button with the Wachtrij/Afspeellijsten refresh
  buttons and expanded tests for the updated QML and HA device-list behavior.

## 3.1.43

- Added `docs/TECHNICAL_DESIGN_DECISIONS.md` with reverse-engineered design
  patterns, language-specific coding conventions and dependency/license/source
  inventory, and made it part of the release documentation checklist.

## 3.1.42

- Added a local debug screenshot flow for the HyperPixel UI:
  `GET /api/debug/screenshot` asks the QML UI process to capture the live
  scenegraph with `grabToImage` and save it to the configured screenshot path.
- Documented the screenshot endpoint in the local API/Postman docs and added
  API, daemon and QML contract tests for the request/event/capture path.
- Kept the endpoint protected with the device bearer token once the client is
  paired, while still allowing bring-up diagnostics before pairing.
- Fixed a queue/playlist responsiveness regression by moving album-art caching
  into the backend worker path instead of QML row delegates.
- Restored visible cached artwork in Queue and Playlists and replaced the
  malformed row play canvas with a fixed-size media play icon button.
- Made the selected bottom navigation item more obvious with a stronger
  gradient, thicker border and top active indicator.
- Removed the dark lower overlay from the Now Playing album art, replaced the
  separate output-device label with a compact selector row and gave playback
  controls more vertical space.
- Expanded Maze Chase to four vertical rows of white pellets.

## 3.1.41

- Made the bottom navigation bar one-third taller and added simple tab icons
  for touch-friendly kiosk navigation.
- Improved Maze Chase by slowing the ghost, adding a large power pellet and
  making the ghost temporarily edible with a blinking blue/white vulnerable
  state.

## 3.1.40

- Fixed Games screen touch pass-through so empty/transparent game areas no
  longer activate underlying Speelt nu playback controls.
- Moved Games to the right of Afspeellijsten in the bottom navigation bar.
- Kept real HA empty queue/playlist responses empty and show "Geen wachtrij" or
  "Geen afspeellijsten"; demo media is now only loaded when demo mode is
  explicitly active.
- Fixed remaining game-canvas QML mouse-handler warnings by using explicit
  signal parameters.

## 3.1.40

- Keep the touch screen awake for 10 seconds when previous/next track starts,
  including HA initiated previous/next commands received through the local
  Client API command-event bridge.

## 3.1.40

- Routed Home Assistant initiated `/api/device/command` calls from the separate
  local API daemon to the touch UI through a small persisted command-event
  queue, so HA entity actions such as previous/next are actually executed by
  the UI process.
- Added an output-device selector to the Speelt nu screen. It reads device
  lists from HA status/command responses and sends `command:"set_output"` with
  the selected value.
- Added manual refresh buttons to Speelt nu, Wachtrij and Afspeellijsten.
- Made Wachtrij and Afspeellijsten opaque full main screens so Speelt nu no
  longer shows through.
- Changed incoming textual DJ responses to a toast that disappears after 10
  seconds instead of a blocking overlay with a Close button.
- Disabled horizontal scrolling in Over and Instellingen and kept destructive
  reset-pairing buttons visually consistent with the other square Pi buttons.
- Fixed QML modal-handler warnings by using explicit signal parameters.
- Expanded tests for command-event routing, output-device parsing/dispatch,
  DJ-response toast behavior and the updated QML kiosk layout.

## 3.1.40

- Fixed Home Assistant command payloads to always include the stable
  `device_id` and `client_type=raspberry_pi`, resolving HA `invalid_client_type`
  responses during refresh/status commands.
- Fixed stale pairing-code behavior after "Opnieuw koppelen" by making the
  local API daemon reload shared config before info/pairing-info and local
  pairing requests.
- Added a macOS-style confirmation screen for "Opnieuw koppelen" and made the
  settings reset-pairing action red.
- Renamed the settings title to "Instellingen", renamed "Logs bekijken" to
  "Logs" and removed the settings Close button.
- Made full-screen overlays consume touch input so controls on underlying
  screens cannot be tapped through logs, about, pairing, version mismatch or
  confirmation screens.
- Made the touch reboot action fall back to `sudo -n systemctl reboot` and made
  the installer write a narrow sudoers rule for only `systemctl reboot`.
- Updated the About screen to use the full available width and show
  `https://djconnect.dev` in white.
- Extended release cleanup tooling so normal release closeout can also clean
  old public distribution releases/tags with `--public`.
- Updated the touch UI kiosk branding to show `DJConnect` everywhere, use the
  real bundled app icon, remove visible close buttons and ignore stale persisted
  config versions in favor of the runtime package version.
- Tightened the Pi media screens with fixed-size play buttons, compact
  `HH:MM:SS INF/WRN/DBG/ERR` log prefixes, Apple-aligned demo queue/playlist
  samples and HA queue/playlist artwork alias support with a 24-hour local
  image cache.
- Fixed unattended updater installs from public tarballs by stripping the
  top-level bundle directory, installing the bundled wheel into the release
  venv, validating all console entrypoints and only then switching
  `/opt/djconnect/current`.
- Made the unattended updater clean old Pi release directories after a
  successful install, keeping the active release plus one rollback release and
  removing stale temporary unpack directories.
- Made unattended updater dependency installs use the same cache-local pip
  temp directory as the installer, avoiding `/tmp` pressure during large
  PySide6 wheel installs on Raspberry Pi Zero 2 W.
- Initial Raspberry Pi display-remote scaffold with Qt Quick/QML, fullscreen
  720x720 touch UI, playback controls and app-like DJConnect pairing, status
  and command client contract.
- Split the local Client API into `djconnect-pi-api` and
  `djconnect-api.service`; the Qt touch UI no longer hosts the API itself.
- Added full-screen startup splash and blocking first-run pairing screen with
  Client API URL and pairing code input.
- Added Home Assistant version compatibility guard. A `3.1.z` Pi client accepts
  HA `>=3.1.0` and `<3.2.0`; mismatches show a blocking screen and trigger
  `djconnect-updater.service`.
- Added local demo mode before pairing and a "Demomodus stoppen" action that
  returns to the blocking pairing flow.
- Added touch-only local games matching the Apple app set: Paddle Rally, Meteor
  Run, Sky Dash and Maze Chase.
- Set default touch screen blanking to 2 minutes with tap-to-wake and a
  configurable timeout in settings.
- Added unattended GitHub release updater, apt maintenance service, systemd
  units, release scripts and bootstrap documentation.
- Added persistent rotating file logging, configurable screen blanking,
  stable/beta update channel selection and expanded tests.
- Added startup Raspberry Pi system-info logging for both UI and API daemon.
- Hardened config writes with private file permissions and atomic replacement.
- Added Client API request size limiting and expanded regression, monkey,
  installer contract and QML tests.
- Switched unattended app updates to the public release repository
  `pcvantol/djconnect-pi-releases` and added a GitHub Actions publish workflow.
- Added complete release bundles with `docs/`, `scripts/`, `src/` and
  `systemd/` so production Pi installs can run from the public release tarball.
- Added modern HyperPixel 4 KMS DPI overlay setup, Raspberry Pi OS Lite 64-bit
  bootstrap with minimal X11/Qt runtime dependencies and installer version
  output.
- Added dark DJConnect blue/purple gradient styling across the touch UI.
- Updated the cross-repo sync prompt with full HA-side Raspberry Pi mDNS
  autodiscovery requirements.
- Documented manual production updates from the public release tarball and made
  the installer restart API/UI services when rerun over an existing install.
- Reviewed Dutch/English translations, moved game titles behind i18n keys and
  fixed the playback fallback so "nothing playing" is translated by the UI.
- Removed Wi-Fi provisioning from the installer; Wi-Fi/hostname/SSH/locale are
  handled by Raspberry Pi Imager before first boot.
- Split general Raspberry Pi OS bootstrap into repo-only
  `scripts/bootstrap_raspberry_pi_os.sh` and excluded it from release tarballs.
  The DJConnect app installer no longer performs timezone, SSH, apt
  full-upgrade, Raspberry Pi Connect, minimal X11/Qt runtime or
  HyperPixel setup.
- Fixed public release install checksum verification so the installer compares
  SHA256 hash values instead of relying on the filename stored in the `.sha256`
  asset.
- Removed third-party system monitoring setup from all bootstrap scripts and
  documentation; monitoring is no longer installed or managed by DJConnect Pi.
- Made the public release installer resumable across reboot, power loss or
  thermal freezes. Release unpack and Python dependency install steps now use
  markers under `/opt/djconnect/install-state/<version>/`, and pip downloads
  are cached under `/var/cache/djconnect-pip`.
- Moved the pip cache outside `/opt/djconnect` so pip can use it while the
  installer runs as root without ownership warnings.
- Added root filesystem expansion to the repo-only Raspberry Pi bootstrap and
  an early free-space check to the release installer so large PySide6 downloads
  fail with a clear recovery message instead of filling the SD card mid-install.
- Added persistent 1GB swapfile setup to the repo-only bootstrap and an early
  active-swap requirement check to the release installer.
- Renamed the public app installer to `scripts/install.sh`, added resource
  snapshots around major install steps, and added prerequisite checks for
  architecture, Python version, writable paths, GitHub release access and
  Raspberry Pi thermal/throttling status.
- Changed public release tarballs to install from a bundled wheel under
  `wheels/` and stop shipping the loose `src/` app source tree.
- Increased the installer free-space requirement to 3GB, added inode reporting,
  cleaned incomplete `.venv` directories before dependency retries, and moved
  pip temporary files under `/var/cache/djconnect-pip/tmp`.
- Hardened installer recovery for partial venv installs by requiring all
  DJConnect console entrypoints before marking dependencies complete.
- Configured `/etc/X11/Xwrapper.config` with `allowed_users=anybody` during
  install so the systemd-managed touch client can start Xorg on Raspberry Pi OS
  Lite.
- Added `needs_root_rights=yes` to the Xwrapper install step so Xorg can open
  `/dev/tty0` when launched by the systemd-managed touch client.
- Changed installer dependency installation to invoke pip through
  `.venv/bin/python -m pip` so a broken generated `pip` wrapper cannot abort
  recovery installs.
- Added a generated six-digit Pi pairing code, exposed it on the blocking
  pairing screen and `/api/device/pairing-info`, and rotate it on pairing reset.
- Refined touch UI controls with transparent rounded purple/blue buttons,
  larger readable logs, copy/clear log actions, scrollable settings, an About
  screen, and queue/playlist screens.
- Fixed the games selector labels by translating each game `titleKey` instead
  of reading a missing `title` field.
- Fixed local Client API request logging so `GET /api/device/pairing-info`
  returns JSON instead of an empty reply, allowing HA mDNS discovery to prefill
  the Pi pairing code.
- Aligned the Pi pairing screen order and labels with the macOS pairing screen,
  removed the logs button from that first-run flow and kept demo mode as the
  only local action.
- Added a Postman collection for the local Pi Client API under `docs/postman/`.
- Added now-playing track progress, font-independent playback icons, larger
  full-width settings controls, logs autoscroll on refresh and richer Maze
  Chase Pac-Man/ghost rendering.
