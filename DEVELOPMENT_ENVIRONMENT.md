# Development Environment

This document describes the local development setup for the DJConnect Raspberry
Pi client repository.

DJConnect Pi is an app-like Raspberry Pi client. It is not ESP firmware. The
canonical client contract is:

- `client_type`: `raspberry_pi`
- Device IDs: `djconnect-raspberry-pi-XXXXXXXXXXXX`
- Python: 3.11 or newer
- UI runtime: PySide6 / Qt Quick / QML

Do not add PTT, microphone upload, local DJ response audio or ESP firmware OTA
behavior here unless the product decision changes.

## Repository Layout

- `src/djconnect_pi/`: Python application, local Client API, updater and
  maintenance daemons.
- `src/djconnect_pi/qml/`: touch UI screens and bundled QML assets.
- `scripts/install.sh`: production app installer for prepared Raspberry Pis.
- `scripts/bootstrap_raspberry_pi_os.sh`: maintainer bootstrap for Raspberry Pi
  OS setup; this is intentionally separate from app releases.
- `systemd/`: service and timer units installed on the Pi.
- `tests/`: Python and contract tests for UI, API, installer, updater and
  release behavior.
- `docs/`: architecture, bootstrap, security/performance and design notes.
- `examples/voice_intents.json`: shared spoken intent examples for docs and
  website alignment only. `current_track` and `playback_control` are handled by
  Home Assistant; the Pi client does not implement local voice capture, local
  Spotify credentials, Spotify Web API calls or playback backend logic.

## Local Setup

Create a virtual environment and install the package with development
dependencies:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e '.[dev]'
```

Run the desktop development client:

```sh
djconnect-pi-client --windowed
```

Run a headless smoke test:

```sh
QT_QPA_PLATFORM=offscreen djconnect-pi-client --windowed --exit-after-ms 1500
```

The default runtime config path is:

```text
~/.config/djconnect-pi/config.json
```

Use `--config <path>` when you want an isolated local config file for testing.

## Tests

Run the full test suite:

```sh
python3 -m pytest
```

Run the main smoke checks:

```sh
python3 -m compileall src tests
QT_QPA_PLATFORM=offscreen python3 -m djconnect_pi.app --windowed --exit-after-ms 1500
```

Run the installer and updater contract tests when touching packaging,
bootstrap, systemd, release or updater behavior:

```sh
python3 -m pytest tests/test_installation_contract.py tests/test_updater.py -q
```

See `TESTS.md` for the full coverage map.

## Raspberry Pi Development

Use Raspberry Pi OS Lite 64-bit for target hardware. Bootstrap OS-level
dependencies from a checkout on the Pi:

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

Install a production release on a prepared Pi from the public distribution
repository:

```sh
mkdir -p ~/djconnect-install
cd ~/djconnect-install
curl -fsSL https://github.com/pcvantol/djconnect-pi-releases/releases/latest/download/djconnect-pi-3.2.0.tar.gz -o djconnect-pi.tar.gz
tar -xzf djconnect-pi.tar.gz
cd djconnect-pi-3.2.0
sudo ./scripts/install.sh
```

The installer writes releases under:

```text
/opt/djconnect/releases/<version>
/opt/djconnect/current -> /opt/djconnect/releases/<version>
/opt/djconnect/config/client.json
```

The app install path, OS bootstrap, updater and touch UI should remain separate
concerns.

## Systemd Services

The Pi runtime is split across separate units:

- `djconnect-api.service`: local Client API and web portal.
- `djconnect-client.service`: fullscreen touch client.
- `djconnect-updater.service`: app updater.
- `djconnect-updater.timer`: unattended update checks.
- `djconnect-maintenance.service` / `.timer`: OS maintenance.
- `djconnect-nightly-reboot.timer`: nightly wall-device freshness reboot.

Useful checks:

```sh
systemctl is-active djconnect-api.service
systemctl is-active djconnect-client.service
systemctl is-active djconnect-updater.timer
systemctl is-active djconnect-nightly-reboot.timer
journalctl -u djconnect-api.service -n 80 --no-pager
journalctl -u djconnect-client.service -n 80 --no-pager
```

## Local API And Debugging

The local Client API listens on the Pi and exposes device, pairing, command,
portal and diagnostic routes. The loopback-only screen and screenshot routes are
useful for visual verification:

```sh
curl -fsS 'http://127.0.0.1:18080/api/debug/screen?screen=now'
curl -fsS 'http://127.0.0.1:18080/api/debug/screenshot'
```

Supported debug screen names are:

```text
now control queue playlists games settings logs about askdj discover musicdna
```

When running these from another machine, execute the curl command through SSH so
the API still sees a loopback request:

```sh
ssh -o BatchMode=yes pi@rbpi-djconnect.local "curl -fsS 'http://127.0.0.1:18080/api/device/info'"
```

## Release Workflow

Dry-run the release flow before making a real release:

```sh
./release.sh X.Y.Z --dry-run
```

Use the next semantic version for real releases:

```sh
./release.sh X.Y.Z
```

The release script updates version metadata, builds the distribution tarball,
writes checksums, commits, tags, pushes and creates the source GitHub release.
The source release workflow publishes public install artifacts to
`pcvantol/djconnect-pi-releases`.

As part of release preparation, refresh third-party dependencies and tooling
deliberately:

- review Python package constraints in `pyproject.toml` and installer/updater
  pip steps for PySide6, requests, websocket-client, zeroconf, pytest and build
  tooling
- upgrade local/CI packaging tools with `python -m pip install --upgrade pip
  setuptools wheel` before building wheels
- review GitHub Actions tool versions such as `actions/checkout`,
  `actions/setup-python`, `actions/setup-node` and the `newman` CLI used by the
  Postman contract test
- review Raspberry Pi OS/bootstrap package lists when runtime libraries or
  device tooling change
- update `docs/TECHNICAL_DESIGN_DECISIONS.md` dependency inventory whenever
  constraints, observed versions, tools or OS packages change

After a successful release or install, update repo hygiene docs when relevant,
including:

- `CHANGELOG.md`
- `README.md`
- `TESTS.md`
- `HANDOFF.md`
- `CHAT_BOOTSTRAP.md`
- related files in `docs/`

For release visual hygiene, remove stale files from `screenshots/` before
capturing the new release set. Regenerate the representative 720x720 screens
after a successful install or UI validation so the directory contains only
current-release screenshots.

Keep the next-chat/bootstrap prompt current so a fresh Codex session starts
from the latest release, validation status and expected next action.

## Cross-Repo Coordination

Do not keep local copies of `SYNC_PROMPTS.md` or `PRODUCT_ROADMAP.md` in this
repository. The canonical files live in `pcvantol/djconnect`.

Coordinate with `pcvantol/djconnect` when changing:

- Home Assistant endpoints or payload contracts.
- Pairing, device identity or mDNS behavior.
- Updater behavior that affects the HA integration or user documentation.
- Shared terminology, branding or product roadmap.
- Assist/STT/TTS expectations.

For cross-repo contract changes originating here, make the follow-up
change/commit in `pcvantol/djconnect`.

## Hygiene Checklist

Before handing off a change:

1. Run the relevant tests.
2. Check `git status --short`.
3. Confirm no secrets, tokens, private URLs or user data were added.
4. Update docs and examples for behavior changes.
5. For release/update changes, validate the installer/updater path on a Pi or
   clearly document why that was not run.
6. For UI changes, capture or verify representative screens when possible.
