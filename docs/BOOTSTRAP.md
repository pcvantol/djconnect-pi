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
- Spotify Premium configured in the DJConnect Home Assistant integration

Software:

- Raspberry Pi OS Desktop/GUI 64-bit, Bookworm recommended
- Python 3.11 or newer
- PySide6 / Qt Quick runtime
- Git
- GitHub CLI only if releases are managed from the Pi itself
- systemd
- X11 or another kiosk-compatible graphical session for the first UI version

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
2. Choose Raspberry Pi OS Desktop/GUI 64-bit Bookworm.
3. Configure hostname, Wi-Fi, SSH and locale before flashing.
4. Boot the Pi and SSH into it.

Update the base system:

```sh
sudo apt-get update
sudo apt-get -y upgrade
sudo reboot
```

The installer configures the running system to boot to console
(`multi-user.target`) and starts the DJConnect Qt frontend automatically through
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

The DJConnect installer performs this configuration automatically by default
with `DJCONNECT_HYPERPIXEL_MODEL=square`. For the rectangular display, run it
with:

```sh
sudo DJCONNECT_HYPERPIXEL_MODEL=rectangular ./scripts/install_raspberry_pi.sh
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
require access to the private source repository:

```sh
mkdir -p ~/djconnect-install
cd ~/djconnect-install
curl -fsSL https://github.com/pcvantol/djconnect-pi-releases/releases/latest/download/djconnect-pi-3.1.13.tar.gz -o djconnect-pi.tar.gz
tar -xzf djconnect-pi.tar.gz
cd djconnect-pi-3.1.13
sudo ./scripts/install_raspberry_pi.sh
```

The installer prints its DJConnect Pi target version in `--help` and at startup:

```sh
./scripts/install_raspberry_pi.sh --help
sudo ./scripts/install_raspberry_pi.sh
```

## Manual Software Update

For a wall-mounted production Pi, update from the public release tarball. You do
not need `git pull` on the Pi unless you are intentionally running from a
development checkout:

```sh
mkdir -p ~/djconnect-install
cd ~/djconnect-install
rm -rf djconnect-pi-* djconnect-pi.tar.gz
curl -fsSL https://github.com/pcvantol/djconnect-pi-releases/releases/latest/download/djconnect-pi-3.1.13.tar.gz -o djconnect-pi.tar.gz
tar -xzf djconnect-pi.tar.gz
cd djconnect-pi-3.1.13
sudo ./scripts/install_raspberry_pi.sh
```

The installer is safe to run over an earlier DJConnect install:

- keeps an existing `/opt/djconnect/config/client.json`
- downloads and verifies the selected public release
- replaces `/opt/djconnect/releases/<version>` for that version
- repoints `/opt/djconnect/current`
- updates systemd unit files
- restarts `djconnect-api.service` and `djconnect-client.service`
- leaves updater, maintenance and screen timers enabled

For a development checkout on the Pi, update the checkout first and then run the
installer from that checkout:

```sh
cd ~/djconnect-pi
git pull --ff-only
sudo ./scripts/install_raspberry_pi.sh
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
5. Confirm the Pi reports `client_type: raspberry_pi`.

The Pi should then show now-playing status and basic playback controls.

## Wall-Mount Settings

Open `Setup` on the touch screen and configure:

- `Screen off`: seconds of inactivity before the UI blanks to black. Use `0` to
  disable blanking. The default is 120 seconds; tap the screen to wake it.
- `Brightness`: app-level visual brightness from 10% to 100%.
- `Language`: Nederlands or English. The first value is read from Raspberry Pi
  OS locale and is not provisioned by Home Assistant.
- `Updates`: `stable` for normal GitHub releases, `beta` to allow prereleases.
- `Client API URL`: enter this in the Home Assistant pairing flow when HA asks
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
