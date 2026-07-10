# DJConnect Pi

Version: `3.2.20`

Raspberry Pi Zero 2 W touch-display client for DJConnect. This client uses
Qt Quick/QML with a PySide6 backend and is meant for a Pimoroni HyperPixel 4.0
Square Touch style kiosk remote: pairing, status, now playing and touch
playback control, Ask DJ history display with structured touch actions,
server-backed Music DNA and Music Discovery.

The Raspberry Pi is the canonical DJConnect Ambient Client. Its default
Profile Platform behavior is shared: Household, room, guest, kids or party
profiles are the safe default for a wall or countertop screen. A personal
profile is used only when Home Assistant resolves the paired Pi device to one
or when an explicit profile selection is configured; the Pi never infers a
personal identity locally.

It intentionally does not implement PTT, microphone upload, local DJ response
audio, a Pi-local DJ response endpoint, ESP firmware OTA, ESP battery sensors
or Wi-Fi RSSI sensors. It does run a small local Client API daemon for Home
Assistant pairing, commands and diagnostics. `_djconnect._tcp` mDNS discovery
is advertised only while the Pi is not yet paired.

Shared spoken intent examples for website/docs alignment live in
`examples/voice_intents.json`. They document the HA/ESP post-STT intent model;
the Raspberry Pi client does not implement local voice capture. The
`current_track` examples, such as `Welk nummer draait er nu?` / `What song is
playing?`, and the `playback_control` examples, such as `Stop muziek`, `Start
muziek`, `Zet harder`, `Zet zachter`, `Volgende nummer` and `Vorig nummer`,
are handled by Home Assistant. They do not require Spotify credentials, Spotify
Web API calls or a playback backend inside this Pi client.

The same local API daemon serves the Raspberry Pi web portal at the Pi web
address, so the portal is installed with the app release and starts
automatically on boot through `djconnect-api.service`.

The 3.2 Pi contract focuses on stable wall-device behavior: local-only
pairing, `_djconnect._tcp` mDNS while unpaired, `/api/device/pairing-info` for
explicit Home Assistant pairing, capability reporting that keeps voice/audio
off, kiosk-safe screen behavior and update/diagnostics surfaces that keep
running separately from the touch UI.

## Client Contract

- `client_type`: `raspberry_pi`
- Device ID: `djconnect-raspberry-pi-XXXXXXXXXXXX`
- Protocol: `3.2.x`
- Transport: local only. Pairing stores and uses only `ha_local_url`; the Pi
  ignores any accidental `ha_remote_url`/Nabu Casa URL fields.
- HTTP is the canonical fallback. The native Home Assistant `/api/websocket`
  fast path is enabled by default for the Pi's local Home Assistant connection.
  The Pi bootstraps a short-lived websocket token through DJConnect bearer auth,
  checks `djconnect/capabilities` and only uses websocket when HA advertises the
  needed `djconnect/*` command. HTTP remains the one-shot fallback for every
  websocket failure or missing capability.
- Music backend selection is Home Assistant-side. The Pi displays the backend
  summary returned by HA and does not store Spotify credentials or assume
  Spotify Direct over Music Assistant.
- Ask DJ is `readonly_actions`. The Pi polls server-side history, displays
  assistant/system/status/user bubbles and sends only Home Assistant-provided
  structured action payloads through `/api/djconnect/v1/command`. Chat history
  clear is server-side only: the touch UI asks for confirmation, calls
  `djconnect/ask_dj/history/clear` or
  `POST /api/djconnect/v1/ask_dj/history/clear`, and clears local bubbles only
  after HA confirms. It reports `ask_dj_voice_supported:false` plus
  `ask_dj_audio_response_supported:false` and does not expose local message
  input, voice/PTT, TTS or local audio playback. DJ announcements can be
  rendered as text only, or spoken by Home Assistant server-side through the
  HA speaker configured in DJConnect options. The Pi only chooses
  `dj_announcement_output` (`text_only` or supported `ha_speaker`) and never
  configures a speaker entity or plays `audio_url` locally.
- Track Insight is server-side in Home Assistant. The Pi posts current track
  metadata, language/locale, optional mood and optional Music DNA key to
  `/api/djconnect/v1/track_insight`, renders direct or wrapped
  `track`/`analysis` responses, clears old analysis on track changes and never
  shows BPM/key/model fields. The Track Insight visualizer uses only the same
  HA response, preferring backend `visualisation`/`visualization`/`visualizer`
  bars and colors and falling back to a visual-only bar model from existing
  response fields without extra network calls or local analysis.
- Music DNA is Home Assistant authoritative. The Pi can call profile, settings
  and clear endpoints over HTTP or the advertised websocket fast path, but it
  does not calculate, store or replay Music DNA as a local source of truth.
  The rendered Music DNA is scoped to the backend-resolved DJConnect Profile:
  household/room/guest profiles show shared Music DNA, and personal profiles
  show personal Music DNA only after explicit profile resolution.
- Music Discovery is Home Assistant authoritative and gated behind Music DNA
  consent. The Pi renders backend `sections[].items[]` in order, treats section
  IDs as opaque backend values, renders backend quality/reason fields directly,
  sends refresh/play/feedback requests and posts Play Now selections back to HA
  as Music Discovery interactions. It does not fabricate recommendations,
  reasons, quality scores, based-on lists or items from recent listening
  history locally. Discover defaults to household/shared recommendations unless
  the backend resolves an explicit personal profile.
- Profile-aware requests send canonical `device_id`, `client_type`,
  `request_source` and optional explicit `profile_id`/`private_session` fields.
  The Pi consumes `djconnect/capabilities` fields for Profile Platform support
  and `profile_context` contract versions instead of guessing from Home
  Assistant versions.
- Profile-scoped touch caches are isolated. When the backend-resolved profile
  changes, Ask DJ history, Music DNA, Discover and Track Insight view state are
  cleared before rendering the new profile's data.
- Home Assistant WebSocket fast path is enabled by default for the Pi's local HA
  connection. The client bootstraps a short-lived HA websocket token with
  `POST /api/djconnect/v1/websocket/session` using the paired DJConnect bearer
  token, authenticates to `/api/websocket`, checks `djconnect/capabilities`,
  uses only advertised `djconnect/*` routes and falls back once to HTTP on
  websocket failures or missing capabilities. Short-lived websocket tokens are
  cached only in memory and are never logged or exported.
- Home Assistant endpoints:
  - `POST /api/djconnect/v1/pair`
  - `POST /api/djconnect/v1/status`
  - `POST /api/djconnect/v1/command`
  - `POST /api/djconnect/v1/event`
  - `POST /api/djconnect/v1/voice` (fixture-only compatibility coverage;
    the Pi client does not advertise voice/PTT)
  - `POST /api/djconnect/v1/websocket/session`
  - `POST /api/djconnect/v1/track_insight`
  - `POST /api/djconnect/v1/music_dna/profile`
  - `POST /api/djconnect/v1/music_dna/settings`
  - `POST /api/djconnect/v1/music_dna/clear`
  - `POST /api/djconnect/v1/music_dna/export`
  - `POST /api/djconnect/v1/music_dna/import`
  - `GET /api/djconnect/v1/music_discovery`
  - `POST /api/djconnect/v1/music_discovery/refresh`
  - `POST /api/djconnect/v1/music_discovery/play`
  - `POST /api/djconnect/v1/music_discovery/feedback`
  - `POST /api/djconnect/v1/ask_dj` (fixture-only compatibility coverage;
    the Pi client uses message/history routes)
  - `POST /api/djconnect/v1/ask_dj/message`
  - `POST /api/djconnect/v1/ask_dj/clear` (fixture-only compatibility
    coverage; the Pi client clears server-side history)
  - `POST /api/djconnect/v1/ask_dj/idle_suggestion`
  - `GET /api/djconnect/v1/ask_dj/history?since_revision=<revision>`
  - `POST /api/djconnect/v1/ask_dj/history/clear`
  - `POST /api/djconnect/v1/ask_dj/history/export`
  - `POST /api/djconnect/v1/ask_dj/history_state`
  - `GET /api/djconnect/v1/vibecast`
  - `GET /api/djconnect/v1/tts/{token}.{extension}`
  - `GET /api/djconnect/v1/image_proxy/{token}`
  - `GET /api/djconnect/v1/debug/last_voice.wav` (fixture-only compatibility
    coverage; the Pi client does not expose local DJ-response audio)
- Home Assistant websocket commands covered by CI:
  - `djconnect/command`
  - `djconnect/ask_dj/message`
  - `djconnect/ask_dj/history`
  - `djconnect/ask_dj/history/clear`
  - `djconnect/ask_dj/history/state`
  - `djconnect/ask_dj/idle_suggestion`
  - `djconnect/track_insight`
  - `djconnect/music_dna/profile`
  - `djconnect/music_dna/settings`
  - `djconnect/music_dna/clear`
  - `djconnect/music_dna/import`
  - `djconnect/music_dna/export`
  - `djconnect/music_discovery/feed`
  - `djconnect/music_discovery/refresh`
  - `djconnect/music_discovery/play`
  - `djconnect/music_discovery/feedback`
- VibeCast is HTTP-only in the current Home Assistant contract. The Pi must not
  request or assume a `djconnect/vibecast` websocket command unless HA starts
  advertising one.
- Local Client API endpoints:
  - `GET /api/device/info`
  - `GET /api/device/pairing-info`
  - `POST /api/device/pair`
  - `POST /api/device/command`
  - `POST /api/device/forget`
  - `POST /api/device/restart`
  - `POST /api/device/shutdown`
  - `GET /api/debug/screenshot`
  - `GET /api/debug/screen?screen=<name>` (loopback-only diagnostic route)
  - `GET /api/portal/state`
  - `POST /api/portal/command`
- Postman collection:
  - `docs/postman/DJConnect Pi Local Client API.postman_collection.json`
- Autonomous HA contract fixture:
  - `node Tools/http_e2e_contract.js`
  - `node Tools/websocket_e2e_contract.js`
  - `node Tools/validate_ha_contract_fixture_security.js`
  - Source-of-truth files are the Home Assistant `pcvantol/djconnect`
    contract files: `custom_components/djconnect/const.py`,
    `custom_components/djconnect/http.py`,
    `custom_components/djconnect/api_handlers.py`,
    `custom_components/djconnect/websocket_api.py` and the relevant tests in
    that repo.
- mDNS service:
  - `_djconnect._tcp` while unpaired only
  - TXT: `name`, `device_name`, `device_id`, `client_type=raspberry_pi`,
    `version`, `firmware`, `app_version`, `paired`, `api=/api/device`,
    `local_url`, `pair_code`, `pairing_code`, `pairing_path`, `pair_path` and
    `model=raspberry_pi`
  - no Home Assistant local or remote URL is advertised through mDNS
  - `POST /api/device/pair` validates the temporary pairing code before
    storing the per-device token and HA local URL
- Supported commands:
  - `status`
  - `play`
  - `pause`
  - `next`
  - `previous`
  - `set_volume`
  - `set_shuffle`
  - `set_repeat`
  - `queue` with `limit=100`
  - `playlists` with `limit=100`
  - `play_context_at` for queue rows, with nested `value.uri`
  - `start_playlist` for playlist rows
  - `ask_dj_action` for HA-provided structured Ask DJ action buttons
- Version compatibility:
  - client `3.2.z` works with DJConnect HA `>=3.2.0` and `<3.3.0`
  - HA responses may include `ha_version` or `ha_major_minor`
  - incompatible HA versions show a blocking screen and trigger
    `djconnect-updater.service` without clearing the pairing token

## UI Shape

The app is a 720x720 fullscreen touch remote:

- full-screen DJConnect startup splash with spinner
- dark DJConnect visual theme with blue/purple gradient backgrounds
- blocking first-run pairing screen until the client is paired
- blocking version-mismatch screen when HA and Pi versions are incompatible
- pairing screen shows the local Client adres and pairing code
- Speelt nu display screen with refresh, a compact mood selector, large
  unobstructed album art and title/artist overlay. The selected mood is stored
  locally and sent to Home Assistant with status, command, Ask DJ, Track
  Insight and Music DNA requests.
- macOS-style gradient toast notifications for short action/backend feedback
- HA-provided album art on Now Playing, Queue and Playlists, loaded
  asynchronously; Now Playing artwork is cached locally before QML renders it,
  while Queue and Playlist background caching is limited to the first visible
  batch to keep Pi Zero 2 W CPU, memory and I/O load low
- Queue and Playlist rows use fixed explicit artwork/text/play-button geometry
  so album art, titles and play icons stay in the correct columns on the
  HyperPixel display
- separate Bediening screen with enlarged previous, play/pause, next,
  progress, volume, output-device, shuffle and repeat controls
- volume controls are capped at HA value 60 and display that as 100%
- bottom navigation and Meer menu icons are drawn as consistent QML Canvas
  outline icons, matching the macOS-style menu language without depending on
  platform-specific Unicode glyph rendering
- Ask DJ screen that displays the shared Home Assistant conversation feed,
  decodes assistant, system, status and other-client user messages, and renders
  HA-provided structured action buttons without free prompt input, voice, PTT,
  TTS or local audio path. The chat clear button is a confirmed server-side
  operation and keeps local history intact if HA returns an error.
- Track Insight screen that refreshes the current-track analysis from Home
  Assistant, shows title/artist/artwork, summary, genre/subgenre, energy,
  danceability, intensity, confidence, production/instrumentation/arrangement
  notes, a lightweight visualizer sourced from the same response and clean
  retry states for no-track/rate-limit responses
- Ontdek screen that works only after Music DNA consent, renders HA-provided
  track, album, artist and playlist recommendations as one large row per item,
  opens backend reason text in a full-screen Waarom details view and sends
  Play Now through `/api/djconnect/v1/music_discovery/play` with `section_id`
  and `discovery_item_id`; negative feedback controls appear only when HA
  advertises feedback support
- Music DNA screen for server-backed opt-in, disable, clear and compact profile
  display; optional dashboard blocks are hidden when absent or ineligible
- Profile adoption is ambient-first: shared profile content may appear on the
  wall display, but personal Ask DJ history, personal recommendations and
  personal Music DNA appear only when the backend resolves an explicit personal
  DJConnect Profile for this Pi.
- fixed bottom menu bar for Speelt nu, Wachtrij, Ask DJ, Track Insight, Ontdek
  and Meer; Meer contains Bediening, Afspeellijsten, Music DNA, Games,
  Instellingen, Logs and Over
- settings for screen blanking, automatic return-to-Speelt-nu timeout
  (`30`, `60`, `120` seconds or `Uit`), brightness, language, logs, pairing
  reset, Home Assistant WebSocket fast path, update checks, reboot/shutdown
  with confirmation and stable/beta update channel
- Device ID and Home Assistant URL are shown on Over, not duplicated in
  Instellingen
- settings save immediately when changed; there is no explicit save button on
  the touch UI or web portal
- output-device selector on Bediening that can switch HA-provided playback
  devices with `set_output`, plus a local-only "Geen" option so the UI does
  not pick the first HA device implicitly
- default screen blanking after 2 minutes, with tap-to-wake; waking from the
  blanked state refreshes playback immediately. Automatic return to Speelt nu
  defaults to 60 seconds and can be disabled, in which case wake keeps the
  current screen.
- touch-only local games: Paddle Rally, Meteor Run, Sky Dash and Maze Chase
- English, Dutch, German, French and Spanish user-facing text, including game
  labels and fallback playback text
- visible Client adres for Home Assistant pairing
- DJ response text overlay
- logs viewer
- web portal with Diagnostics for Home Assistant API, local API, pairing and
  DJConnect systemd service/timer status, including the touch UI, separate
  update progress UI, updater, maintenance, watchdog, screen schedule and
  nightly reboot units
- web portal settings use save-on-change, refresh actions show busy feedback,
  logs scroll to the newest line after refresh and log copy confirms via toast
- web portal playback controls use the ESP-style large purple icon buttons
  with visible shuffle/repeat state and volume percentage
- local demo mode before pairing
- persistent rotating client log
- Logs, Over and Instellingen are opaque full-screen views; modal overlays
  consume touch input so controls behind logs, about, pairing and confirmation
  screens cannot be accidentally activated
- separate nightly reboot timer at 04:30 for wall-device freshness

The initial language is detected from the Raspberry Pi OS locale and then stored
locally. Supported UI languages are `en`, `nl`, `de`, `fr` and `es`; unsupported
locales fall back to English. Home Assistant does not provision UI language for
Raspberry Pi clients; only ESP clients use HA language provisioning.

Queue row playback follows the app/HACS contract. A row is playable when Home
Assistant provides a backend item reference. Spotify Direct rows may use
Spotify URIs; Music Assistant rows may use MA item/player references. The Pi
sends the structured value back to Home Assistant and does not call
Spotify-specific fallback endpoints.

## Quick Start

Fresh Pi setup is split into two steps. General Raspberry Pi OS preparation is
repo-only maintainer bootstrap work and is not part of the DJConnect app release
tarball. Flash **Raspberry Pi OS Lite 64-bit** with Raspberry Pi Imager; the
bootstrap installs only the minimal X11/Qt runtime required for the fullscreen
touch UI, expands the root filesystem, configures 1GB swap and enables
boot-time filesystem repair checks plus NTP time synchronization. It also
installs a localhost-only `x11vnc` screen-sharing service on port `5901` for
SSH-tunneled remote viewing:

```sh
sudo apt-get update
sudo apt-get install -y git
if [ -d "$HOME/djconnect-pi/.git" ]; then
  cd "$HOME/djconnect-pi"
  git pull --ff-only
else
  git clone https://github.com/pcvantol/djconnect-pi.git "$HOME/djconnect-pi"
  cd "$HOME/djconnect-pi"
fi
sudo ./scripts/bootstrap_raspberry_pi_os.sh
```

Production app install on a prepared Pi uses the public distribution release,
not a private source clone:

```sh
mkdir -p ~/djconnect-install
cd ~/djconnect-install
curl -fsSL https://github.com/pcvantol/djconnect-pi-releases/releases/latest/download/djconnect-pi-3.2.20.tar.gz -o djconnect-pi.tar.gz
tar -xzf djconnect-pi.tar.gz
cd djconnect-pi-3.2.20
sudo ./scripts/install.sh
```

Development install from a checkout:

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

On first launch, the app blocks normal playback controls until pairing is done.
Use the Client adres shown on the Pi in the Home Assistant pairing flow, then
enter the pairing code on the Pi. The client stores config under
`~/.config/djconnect-pi/config.json` unless `--config` is provided.

## Unattended Updates

The local Client API, updater, updater progress UI and OS maintenance are
separate processes from the UI app. The Client API runs as
`djconnect-api.service`; the touch UI runs as `djconnect-client.service`; the
temporary update progress screen runs as `djconnect-update-ui.service`.

The updater checks GitHub Releases in the public distribution repository
`pcvantol/djconnect-pi-releases`,
downloads a tarball asset and optional `.sha256`, installs into:

```text
/opt/djconnect/releases/<version>
/opt/djconnect/current -> /opt/djconnect/releases/<version>
```

After a newer release is detected, the updater stops the normal touch UI, local
API, maintenance and watchdog services before install work, then starts the
separate updater UI so the screen can show progress without running the main
client. It then restarts `djconnect-api.service` and `djconnect-client.service`.
App updates are atomic at the symlink level and preserve config outside the
release directory.

Set the updater channel in the touch settings to `stable` for normal releases
or `beta` to allow GitHub prereleases. The systemd updater reads
`/opt/djconnect/config/client.json`, so the touchscreen setting controls the
unattended update channel.

Release assets are published from this source repository to
`pcvantol/djconnect-pi-releases` by `.github/workflows/publish-release.yml` on
`vX.Y.Z` tags. Configure the source repo secret `DJCONNECT_PI_RELEASES_TOKEN` with
permission to create releases in the public distribution repo.

Release bundles include `docs/`, `systemd/`, `scripts/install.sh` and a
prebuilt wheel under `wheels/`. They do not include the loose app source tree,
so the Pi can install the app from the public tarball without cloning the
private source repo. Repo-only OS bootstrap helpers, including
`scripts/bootstrap_raspberry_pi_os.sh`, are excluded from release tarballs by
design.

Cross-repo contract changes are documented only in canonical
`pcvantol/djconnect/SYNC_PROMPTS.md`. Product roadmap changes are tracked only
in canonical `pcvantol/djconnect/PRODUCT_ROADMAP.md`. This Raspberry Pi repo
must not keep local copies of either file; changes that start here need a
follow-up commit in the Home Assistant integration repo.

OS maintenance is also separate. The maintenance command can run apt update,
upgrade and reboot only when `/var/run/reboot-required` exists, optionally
inside a configured maintenance window.
The nightly reboot timer is separate from OS maintenance and reboots the wall
Pi every night at 04:30.

The touch UI reboot/shutdown buttons and the manual "Controleer op updates"
action use narrow systemctl commands and sudo fallbacks. The installer writes a
narrow sudoers rule for the dedicated `djconnect` runtime user that only
permits reboot, poweroff and starting `djconnect-updater.service`.
The repo-only OS bootstrap and the app installer both write a separate narrow
sudoers rule for the install user, `pi` by default, so
`sudo -n ./scripts/install.sh` can be rerun from
`~/djconnect-install/djconnect-pi-*/scripts/install.sh` or
`~/djconnect-pi/scripts/install.sh` without an interactive password after one
manual sudo install.

After each release, clean old source and public distribution releases/tags plus
completed tag workflow runs:

```sh
./cleanup_old_releases.sh --keep 1 --public --execute
```

The normal `Validate` CI workflow also removes older completed GitHub Actions
runs on `main` and manual dispatches, keeping the newest 2 runs per workflow.

Also update `CHAT_BOOTSTRAP.md` after each release so the next Codex session
has the current release number, validation status, public asset status and next
expected action.

Before each release, deliberately refresh and review third-party dependencies
and tools: Python package constraints in `pyproject.toml`, installer/updater pip
steps, `pip`/`setuptools`/`wheel`, GitHub Actions versions, Node/Newman tooling
and Raspberry Pi OS/bootstrap package lists. Update
`docs/TECHNICAL_DESIGN_DECISIONS.md` when dependency constraints, observed
versions or tool choices change.

See `systemd/` for service and timer templates.

## Manual Pi Software Update

For a production Pi, update from the public release tarball and rerun the
installer:

```sh
mkdir -p ~/djconnect-install
cd ~/djconnect-install
rm -rf djconnect-pi-* djconnect-pi.tar.gz
curl -fsSL https://github.com/pcvantol/djconnect-pi-releases/releases/latest/download/djconnect-pi-3.2.20.tar.gz -o djconnect-pi.tar.gz
tar -xzf djconnect-pi.tar.gz
cd djconnect-pi-3.2.20
sudo ./scripts/install.sh
```

The installer preserves existing config, updates `/opt/djconnect/current`,
refreshes systemd units, and restarts `djconnect-api.service` and `djconnect-client.service`.
It does not run OS bootstrap tasks such as timezone, SSH, apt full-upgrade,
Raspberry Pi Connect, VNC or HyperPixel setup. Use
`git pull --ff-only` first only when the Pi is running from a development
checkout.

The public release tarball installs from its bundled wheel in `wheels/`; it does
not contain the loose `src/` app source tree.

The installer is resumable. If the Pi freezes, overheats, loses power or is
rebooted during the heavy Python/PySide6 dependency step, run the same public
release install command again. Release-level steps are tracked under
`/opt/djconnect/install-state/<version>/`; per-package dependency steps are
tracked under `/opt/djconnect/releases/<version>/.install-state/`. Python
downloads are cached under `/var/cache/djconnect-pip`. If the venv step did not
complete, the next run removes the incomplete `.venv` before retrying.

The repo-only bootstrap expands the root filesystem to fill the SD card. The
bootstrap also configures a persistent 1GB swapfile. The app installer checks
free space and active swap before downloading PySide6. It requires 3GB free
space so a too-small root partition or missing swap fails early with a clear
message.

During install, the script prints resource snapshots around major steps:
available memory, swap, disk usage and inode usage. It also checks CPU
architecture, Python version, writable install paths, GitHub release
reachability and Raspberry Pi thermal/throttling status when `vcgencmd` is
available.

## Continuous Integration

This repo uses the shared DJConnect CI baseline from
`pcvantol/djconnect/.github/workflows/`: `validate.yml` calls the reusable
Python workflow with `source-path: src`, `test-path: tests` and
`test-command: python -m pytest`; `codeql.yml` runs shared CodeQL for Python;
`semgrep.yml` runs the shared DJConnect Semgrep rules as an advisory check.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Bootstrap a Pi Zero 2 W + HyperPixel](docs/BOOTSTRAP.md)
- [Performance and Security Review](docs/PERFORMANCE_SECURITY.md)
- [Technical Design Decisions](docs/TECHNICAL_DESIGN_DECISIONS.md)
- [Handoff](HANDOFF.md)
- [Changelog](CHANGELOG.md)
- [Issues](ISSUES.md)
- [Todo](TODO.md)
- [Tests](TESTS.md)

## License

DJConnect Pi is released under the MIT License. See [LICENSE](LICENSE).
