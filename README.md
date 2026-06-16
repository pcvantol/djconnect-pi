# DJConnect Pi

Version: `3.1.63`

Raspberry Pi Zero 2 W touch-display client for DJConnect. This client uses
Qt Quick/QML with a PySide6 backend and is meant for a Pimoroni HyperPixel 4.0
Square Touch style kiosk remote: pairing, status, now playing and touch
playback control only.

It intentionally does not implement PTT, microphone upload, local DJ response
audio, ESP firmware OTA, ESP battery sensors or Wi-Fi RSSI sensors. It does
run a small local Client API daemon for Home Assistant pairing, commands,
diagnostics and text-only DJ responses. `_djconnect._tcp` mDNS discovery is
advertised only while the Pi is not yet paired.

Shared spoken intent examples for website/docs alignment live in
`examples/voice_intents.json`. They document the HA/ESP post-STT intent model;
the Raspberry Pi client does not implement local voice capture.

The same local API daemon serves the Raspberry Pi web portal at the Pi web
address, so the portal is installed with the app release and starts
automatically on boot through `djconnect-api.service`.

## Client Contract

- `client_type`: `raspberry_pi`
- Device ID: `djconnect-raspberry-pi-XXXXXXXXXXXX`
- Home Assistant endpoints:
  - `POST /api/djconnect/pair`
  - `POST /api/djconnect/status`
  - `POST /api/djconnect/command`
- Local Client API endpoints:
  - `GET /api/device/info`
  - `GET /api/device/pairing-info`
  - `POST /api/device/pair`
  - `POST /api/device/command`
  - `POST /api/device/dj_response`
  - `POST /api/device/forget`
  - `POST /api/device/restart`
  - `POST /api/device/shutdown`
  - `GET /api/debug/screenshot`
  - `GET /api/debug/screen?screen=<name>` (loopback-only diagnostic route)
  - `GET /api/portal/state`
  - `POST /api/portal/command`
- Postman collection:
  - `docs/postman/DJConnect Pi Local Client API.postman_collection.json`
- mDNS service:
  - `_djconnect._tcp` while unpaired only
  - TXT: `device_id`, `client_type=raspberry_pi`, `version`, `app_version`,
    `device_name`, `local_url`, `pair_code`, `paired`
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
- Version compatibility:
  - client `3.1.z` works with DJConnect HA `>=3.1.0` and `<3.2.0`
  - HA responses may include `ha_version` or `ha_major_minor`
  - incompatible HA versions show a blocking screen and trigger
    `djconnect-updater.service`

## UI Shape

The app is a 720x720 fullscreen touch remote:

- full-screen DJConnect startup splash with spinner
- dark DJConnect visual theme with blue/purple gradient backgrounds
- blocking first-run pairing screen until the client is paired
- blocking version-mismatch screen when HA and Pi versions are incompatible
- pairing screen shows the local Client API URL and pairing code
- Speelt nu display screen with status, refresh, large album art and title
- HA-provided album art on Now Playing, Queue and Playlists, loaded
  asynchronously so media-list navigation stays responsive on Pi Zero 2 W
- Queue and Playlist rows use fixed explicit artwork/text/play-button geometry
  so album art, titles and play icons stay in the correct columns on the
  HyperPixel display
- separate Bediening screen with enlarged previous, play/pause, next,
  progress, volume, output-device, shuffle and repeat controls
- volume controls are capped at HA value 60 and display that as 100%
- fixed bottom menu bar for Speelt nu, Bediening, Wachtrij, Afspeellijsten,
  Games and Instellingen
- compact HA/pairing/backend status
- settings for screen blanking, brightness, language, logs, pairing reset,
  update checks, reboot/shutdown with confirmation and stable/beta update
  channel
- output-device selector on Bediening that can switch HA-provided playback
  devices with `set_output`, plus a local-only "Geen" option so the UI does
  not pick the first HA device implicitly
- default screen blanking after 2 minutes, with tap-to-wake
- touch-only local games: Paddle Rally, Meteor Run, Sky Dash and Maze Chase
- Dutch/English user-facing text, including game labels and fallback playback
  text
- visible Client API URL for Home Assistant pairing
- DJ response text overlay
- logs viewer
- web portal with Diagnostics for Home Assistant API, local API, pairing and
  DJConnect systemd service/timer status
- web portal playback controls use the ESP-style large purple icon buttons
  with visible shuffle/repeat state and volume percentage
- local demo mode before pairing
- persistent rotating client log
- Logs, Over and Instellingen are opaque full-screen views; modal overlays
  consume touch input so controls behind logs, about, pairing and confirmation
  screens cannot be accidentally activated

The initial language is detected from the Raspberry Pi OS locale and then stored
locally. Home Assistant does not provision UI language for Raspberry Pi clients;
only ESP clients use HA language provisioning.

## Quick Start

Fresh Pi setup is split into two steps. General Raspberry Pi OS preparation is
repo-only maintainer bootstrap work and is not part of the DJConnect app release
tarball. Flash **Raspberry Pi OS Lite 64-bit** with Raspberry Pi Imager; the
bootstrap installs only the minimal X11/Qt runtime required for the fullscreen
touch UI, expands the root filesystem, configures 1GB swap and enables
boot-time filesystem repair checks plus NTP time synchronization:

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
curl -fsSL https://github.com/pcvantol/djconnect-pi-releases/releases/latest/download/djconnect-pi-3.1.63.tar.gz -o djconnect-pi.tar.gz
tar -xzf djconnect-pi.tar.gz
cd djconnect-pi-3.1.63
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
Use the Client API URL shown on the Pi in the Home Assistant pairing flow, then
enter the pairing code on the Pi. The client stores config under
`~/.config/djconnect-pi/config.json` unless `--config` is provided.

## Unattended Updates

The local Client API, updater and OS maintenance are separate processes from the
UI app. The Client API runs as `djconnect-api.service`; the touch UI runs as
`djconnect-client.service`.

The updater checks GitHub Releases in the public distribution repository
`pcvantol/djconnect-pi-releases`,
downloads a tarball asset and optional `.sha256`, installs into:

```text
/opt/djconnect/releases/<version>
/opt/djconnect/current -> /opt/djconnect/releases/<version>
```

It then restarts `djconnect-api.service` and `djconnect-client.service`. App
updates are atomic at the symlink level and preserve config outside the release
directory.

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

The touch UI reboot/shutdown buttons and the manual "Controleer op updates"
action use narrow systemctl commands and sudo fallbacks. The installer writes a
narrow sudoers rule for the dedicated `djconnect` runtime user that only
permits reboot, poweroff and starting `djconnect-updater.service`.

After each release, clean old source and public distribution releases/tags plus
completed tag workflow runs:

```sh
./cleanup_old_releases.sh --keep 1 --public --execute
```

See `systemd/` for service and timer templates.

## Manual Pi Software Update

For a production Pi, update from the public release tarball and rerun the
installer:

```sh
mkdir -p ~/djconnect-install
cd ~/djconnect-install
rm -rf djconnect-pi-* djconnect-pi.tar.gz
curl -fsSL https://github.com/pcvantol/djconnect-pi-releases/releases/latest/download/djconnect-pi-3.1.63.tar.gz -o djconnect-pi.tar.gz
tar -xzf djconnect-pi.tar.gz
cd djconnect-pi-3.1.63
sudo ./scripts/install.sh
```

The installer preserves existing config, updates `/opt/djconnect/current`,
refreshes systemd units, and restarts `djconnect-api.service` and
`djconnect-client.service`. It does not run OS bootstrap tasks such as timezone,
SSH, apt full-upgrade, Raspberry Pi Connect or HyperPixel setup. Use
`git pull --ff-only` first only when the Pi is running from a development
checkout.

The public release tarball installs from its bundled wheel in `wheels/`; it does
not contain the loose `src/` app source tree.

The installer is resumable. If the Pi freezes, overheats, loses power or is
rebooted during the heavy Python/PySide6 dependency step, run the same public
release install command again. Completed steps are tracked under
`/opt/djconnect/install-state/<version>/`, and Python downloads are cached under
`/var/cache/djconnect-pip`. If the venv step did not complete, the next run
removes the incomplete `.venv` before retrying.

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
