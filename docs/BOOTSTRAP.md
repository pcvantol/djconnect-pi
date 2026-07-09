# Bootstrap Raspberry Pi Zero 2 W + HyperPixel

This guide starts from a blank Raspberry Pi Zero 2 W with a Pimoroni HyperPixel
4.0 Square Touch display.

## Requirements

Hardware:

- Raspberry Pi Zero 2 W
- Pimoroni HyperPixel 4.0 Square Touch
- quality 5V power supply, preferably 2A or better
- microSD card, 16 GB minimum, 32 GB or larger recommended
- Wi-Fi network with access to Home Assistant
- Home Assistant with the DJConnect integration installed
- A DJConnect music backend configured in Home Assistant, such as Music
  Assistant or Spotify Direct. Spotify credentials, when used, stay in Home
  Assistant and are never stored on the Pi.

Software:

- Raspberry Pi OS Lite 64-bit, Bookworm recommended
- Python 3.11 or newer
- PySide6 / Qt Quick runtime
- Git
- GitHub CLI only if releases are managed from the Pi itself
- systemd
- Minimal X11/kiosk runtime installed by the bootstrap script; no desktop/GUI
  image is required
- Localhost-only x11vnc screen sharing on port `5901`, installed by the
  bootstrap script for SSH-tunneled remote viewing
- 1GB active swapfile configured by the bootstrap script
- Automatic filesystem repair checks configured by the bootstrap script, so
  the Pi asks Linux to repair filesystems on boot after unsafe power loss
- Automatic NTP time synchronization enabled by the bootstrap script for stable
  logs, TLS/GitHub downloads and Home Assistant communication
- Nightly reboot timer enabled by default at 04:30

Network:

- The Pi must reach Home Assistant on the local URL, for example
  `http://homeassistant.local:8123`.
- Home Assistant must be able to pair a `raspberry_pi` client.
- Internet access is required for unattended GitHub release updates and apt
  maintenance.
- The Pi should have enough free disk space for logs, release bundles and one
  rollback release. A 32 GB or larger SD card is strongly preferred.

## Flash Raspberry Pi OS

Use Raspberry Pi Imager:

1. Choose Raspberry Pi Zero 2 W.
2. Choose Raspberry Pi OS Lite 64-bit Bookworm.
3. Configure hostname, Wi-Fi, SSH and locale before flashing.
4. Boot the Pi and SSH into it.

DJConnect does not provision Wi-Fi. Network, hostname, SSH and locale should be
configured with Raspberry Pi Imager before first boot.

Run the repo-only OS bootstrap helper from a source checkout when you are
preparing the Pi as maintainer/admin:

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
sudo reboot
```

The bootstrap helper configures the running system to boot to console
(`multi-user.target`), expands the root filesystem to fill the SD card, sets
timezone to `Europe/Amsterdam`, configures a persistent 1GB swapfile at
`/swapfile`, enables automatic boot-time filesystem repair with
`fsck.repair=yes`, removes any `fsck.mode=skip`, sets the root filesystem check
pass to `1` in `/etc/fstab`, enables periodic ext filesystem checks with
`tune2fs`, enables NTP with `timedatectl set-ntp true` and
`systemd-timesyncd.service` when present, enables SSH, runs an optional apt
full-upgrade, installs minimal X11/kiosk dependencies, Qt runtime libraries,
generates `en_GB.UTF-8`, `nl_NL.UTF-8`, `de_DE.UTF-8`, `fr_FR.UTF-8` and
`es_ES.UTF-8` locales, attempts Raspberry Pi
Connect, installs a localhost-only `x11vnc` screen-sharing service, configures
the nightly reboot timer and configures HyperPixel. It is intentionally not
included in DJConnect Pi release tarballs and is not part of the app release
cycle.

The VNC service is installed as `djconnect-vnc.service` and binds to
`127.0.0.1:5901` by default. Open it from your Mac with an SSH tunnel:

```sh
ssh -L 5901:127.0.0.1:5901 pi@rbpi-djconnect.local
```

Then connect your VNC client to `localhost:5901`. This avoids exposing an
unauthenticated VNC port on the LAN. To disable this bootstrap step, run with
`DJCONNECT_ENABLE_VNC=0`; to expose the VNC port directly on a trusted network,
set `DJCONNECT_VNC_LOCALHOST_ONLY=0`.

These filesystem checks are intended for a wall-mounted device where power can
occasionally be removed. They do not replace a good SD card or clean shutdowns,
but they keep the normal Linux boot repair path enabled instead of silently
skipping checks.

If an earlier bootstrap attempt left apt/dpkg half-configured, repair the
package state once and rerun the bootstrap:

```sh
sudo apt-get -f install -y
cd "$HOME/djconnect-pi"
git pull --ff-only
sudo ./scripts/bootstrap_raspberry_pi_os.sh
```

The DJConnect app installer starts the Qt frontend automatically through
`djconnect-client.service` using `xinit`. A full desktop session is not started
after boot.

## Install HyperPixel Support

Modern Raspberry Pi OS 64-bit images should use the KMS DPI overlay method from
Pimoroni's HyperPixel 4 notice instead of the legacy installer. HyperPixel uses
the GPIO header directly, so disable I2C and SPI before enabling the overlay:

```sh
sudo apt-get update
sudo raspi-config nonint do_i2c 1
sudo raspi-config nonint do_spi 1
sudo systemctl disable --now hyperpixel4-init.service 2>/dev/null || true
```

Edit `/boot/firmware/config.txt` on Bookworm, or `/boot/config.txt` on older
images, and add exactly one overlay line:

```ini
# HyperPixel 4 Square
dtoverlay=vc4-kms-dpi-hyperpixel4sq

# HyperPixel 4 Rectangular, use this instead for the rectangular display
# dtoverlay=vc4-kms-dpi-hyperpixel4
```

For fixed boot-time rotation, add `rotate=90`, `rotate=180` or `rotate=270` to
the same line:

```ini
dtoverlay=vc4-kms-dpi-hyperpixel4sq,rotate=90
```

The repo-only OS bootstrap helper performs this configuration automatically by
default with `DJCONNECT_HYPERPIXEL_MODEL=square`. For the rectangular display,
run it with:

```sh
sudo DJCONNECT_HYPERPIXEL_MODEL=rectangular ./scripts/bootstrap_raspberry_pi_os.sh
```

After reboot, confirm:

- display output is 720x720
- touch input follows the display rotation
- the desktop or X session starts on the HyperPixel

If touch is rotated or mirrored, fix rotation at the OS/display layer before
debugging DJConnect. For HyperPixel 4 Square, Pimoroni notes that touch rotation
may need Xorg transformation settings for some orientations.

## Create the Runtime User

```sh
sudo useradd --system --create-home --groups video,input,render djconnect
sudo mkdir -p /opt/djconnect/config /opt/djconnect/releases
sudo chown -R djconnect:djconnect /opt/djconnect
```

## Install the Client Manually

For a production Pi, install from the public release bundle. This does not
require access to the private source repository once the OS bootstrap has been
completed:

```sh
mkdir -p ~/djconnect-install
cd ~/djconnect-install
curl -fsSL https://github.com/pcvantol/djconnect-pi-releases/releases/latest/download/djconnect-pi-3.2.15.tar.gz -o djconnect-pi.tar.gz
tar -xzf djconnect-pi.tar.gz
cd djconnect-pi-3.2.15
sudo ./scripts/install.sh
```

The installer prints its DJConnect Pi target version in `--help` and at startup:

```sh
./scripts/install.sh --help
sudo ./scripts/install.sh
```

The public release bundle installs from its bundled wheel in `wheels/`. It does
not contain the loose `src/` app source tree from the private source repository.
It also writes a narrow `/etc/sudoers.d/djconnect-reboot` rule so the dedicated
`djconnect` runtime user can run only absolute-path `systemctl` reboot,
poweroff and `start djconnect-updater.service` commands from the touchscreen
and web UI. The installer validates that sudoers fragment with `visudo -cf`.

## Manual Software Update

For a wall-mounted production Pi, update from the public release tarball. You do
not need `git pull` on the Pi unless you are intentionally running from a
development checkout:

```sh
mkdir -p ~/djconnect-install
cd ~/djconnect-install
rm -rf djconnect-pi-* djconnect-pi.tar.gz
curl -fsSL https://github.com/pcvantol/djconnect-pi-releases/releases/latest/download/djconnect-pi-3.2.15.tar.gz -o djconnect-pi.tar.gz
tar -xzf djconnect-pi.tar.gz
cd djconnect-pi-3.2.15
sudo ./scripts/install.sh
```

The installer is safe to run over an earlier DJConnect install:

- keeps an existing `/opt/djconnect/config/client.json`
- downloads and verifies the selected public release
- replaces `/opt/djconnect/releases/<version>` for that version
- repoints `/opt/djconnect/current`
- updates systemd unit files
- updates the narrow sudoers rule for the touchscreen reboot, shutdown and
  update-check actions
- configures `/etc/X11/Xwrapper.config` with `allowed_users=anybody` and
  `needs_root_rights=yes` so the systemd-managed touch client can start Xorg on
  Raspberry Pi OS Lite
- restarts `djconnect-api.service` and `djconnect-client.service`
- leaves updater, maintenance and screen timers enabled
- leaves the nightly reboot timer enabled
- does not run OS bootstrap tasks such as timezone, SSH, apt full-upgrade,
  Raspberry Pi Connect, VNC or HyperPixel setup
- resumes completed install steps after interruption or reboot using markers in
  `/opt/djconnect/install-state/<version>/`
- reuses Python package downloads from `/var/cache/djconnect-pip`
- removes an incomplete `.venv` automatically before retrying the Python
  dependency step

If the Pi freezes, overheats, loses power or is rebooted during the heavy
Python/PySide6 dependency install step, wait for it to boot and run the same
public release install command again. The installer skips the completed release
unpack step and continues from per-package dependency markers under
`/opt/djconnect/releases/<version>/.install-state/`. If the venv step did not
complete, the next run removes the incomplete `.venv` before retrying.

If logs show `Unable to locate executable
/opt/djconnect/current/bin/djconnect-pi-api`, rerun the latest public installer.
The installer verifies all DJConnect console entrypoints before it considers the
Python venv complete.

If this started immediately after an unattended update and
`readlink -f /opt/djconnect/current` points at a release directory that has no
`VERSION` file or no `bin/` directory, remove that broken release and rerun the
latest public installer:

```sh
version="$(basename "$(readlink -f /opt/djconnect/current)")"
sudo systemctl stop djconnect-api.service djconnect-client.service djconnect-updater.service
sudo rm -rf "/opt/djconnect/releases/${version}"
sudo rm -f "/opt/djconnect/install-state/${version}/release_unpacked.done" \
  "/opt/djconnect/install-state/${version}/venv_ready.done"
cd ~/djconnect-install/djconnect-pi-${version}
sudo ./scripts/install.sh
```

Newer updater versions install the bundled wheel and validate all console
entrypoints before switching `/opt/djconnect/current`, so the same failure
should not repeat after the fixed release is installed.

For responsiveness triage after an update, confirm the Pi reports the expected
release and low UI load:

```sh
cat /opt/djconnect/current/VERSION
systemctl is-active djconnect-client.service djconnect-api.service
ps -o pid,pcpu,pmem,comm -C djconnect-pi-client -C Xorg --sort=-pcpu
free -m
```

DJConnect Pi `3.1.70` and newer limit media-list artwork cache work to the
first visible batch and skip duplicate cache workers. If CPU remains high,
compare `top`, `vmstat 1 5`, `vcgencmd measure_temp` and
`vcgencmd get_throttled` before changing polling or UI code.

If logs show `Only console users are allowed to run the X server` or
`parse_vt_settings: Cannot open /dev/tty0 (Permission denied)`, rerun the latest
public installer. It updates `/etc/X11/Xwrapper.config` for the systemd-managed
kiosk service.

If the installer reports `No space left on device` or stops with a free-space
message, check `df -h /` and rerun the repo-only bootstrap, reboot if root
filesystem expansion asks for it, and then rerun the same public release
install command. The release installer requires at least 3GB free space before
the PySide6 dependency step starts.

If the installer stops with a swap requirement message, rerun the repo-only
bootstrap so it can create and activate `/swapfile`, then rerun the same public
release install command.

For a development checkout on the Pi, update the checkout first and then run the
installer from that checkout. If you need to re-apply OS bootstrap work, run the
repo-only bootstrap helper separately:

```sh
cd ~/djconnect-pi
git pull --ff-only
sudo ./scripts/bootstrap_raspberry_pi_os.sh
sudo ./scripts/install.sh
```

The unattended app updater uses the same release layout under
`/opt/djconnect/releases` and is still the preferred normal update path once the
device is installed.

From a development checkout:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
djconnect-pi-client --ha-url http://homeassistant.local:8123
```

For a local window during development, use:

```sh
djconnect-pi-client --windowed --ha-url http://homeassistant.local:8123
```

## Enable systemd Services

Copy units:

```sh
sudo cp systemd/djconnect-*.service systemd/djconnect-*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now djconnect-api.service
sudo systemctl enable --now djconnect-client.service
sudo systemctl enable --now djconnect-updater.timer
sudo systemctl enable --now djconnect-maintenance.timer
```

Start the local API and UI:

```sh
sudo systemctl start djconnect-api.service
sudo systemctl start djconnect-client.service
```

Check logs:

```sh
journalctl -u djconnect-api.service -f
journalctl -u djconnect-client.service -f
```

## Pair With Home Assistant

1. Open the DJConnect integration in Home Assistant.
2. Start pairing for a Raspberry Pi/client device.
3. On the Pi screen, enter the Home Assistant URL if prompted.
4. Enter the pairing code.
5. Confirm the Pi validates the pairing code and reports
   `client_type: raspberry_pi`.
6. Confirm `/api/device/info` reports `transport:"local_only"` and only the
   local Home Assistant URL (`ha_local_url`), not any remote/Nabu Casa URL.
7. Confirm `/api/device/info` reports Ask DJ as `readonly_actions`, with
   `ask_dj_free_input_supported:false`, `ask_dj_actions_supported:true`,
   `ask_dj_voice_supported:false`, `ask_dj_audio_response_supported:false`,
   `voice_supported:false`, `tts_supported:false` and
   `local_audio_supported:false`.
8. Confirm the music backend summary shows the HA backend name, target player,
   availability/error and compact capabilities.

The Pi should then show now-playing status and basic playback controls.

## Wall-Mount Settings

Open `Setup` on the touch screen and configure:

- `Screen off`: seconds of inactivity before the UI blanks to black. Use `0` to
  disable blanking. The default is 120 seconds; tap the screen to wake it.
- `Brightness`: app-level visual brightness from 10% to 100%.
- `Language`: English, Nederlands, Deutsch, Français or Español. The first
  value is read from Raspberry Pi OS locale and is not provisioned by Home
  Assistant.
- `Updates`: `stable` for normal GitHub releases, `beta` to allow prereleases.
- `Client adres`: enter this in the Home Assistant pairing flow when HA asks
  for it. HA may also discover the Pi through `_djconnect._tcp` mDNS.
- `Log`: read-only path to the persistent rotating client log.

## Operational Notes

- Do not power-cut the Pi during apt upgrades or app updates.
- Prefer a read-quality SD card; unattended updates create regular writes.
- Keep OS maintenance in a quiet window, for example `03:00-04:00`.
- Keep the client update channel on `stable` unless you are actively testing a
  prerelease.
- If a release fails to start, repoint `/opt/djconnect/current` to the previous
  directory in `/opt/djconnect/releases`.
- This client has no microphone or local DJ audio response path by design.
  Shared `current_track` and `playback_control` voice examples are Home
  Assistant behavior and do not require Spotify credentials or playback backend
  logic on the Pi.
- Ask DJ on the Pi displays the shared Home Assistant feed with optional
  structured touch action buttons supplied by Home Assistant. It does not
  expose free prompt input, local history clear, push-to-talk, wake word, TTS
  or local Ask DJ audio playback.
