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

- Raspberry Pi OS Lite or Desktop, Bookworm recommended
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
2. Choose Raspberry Pi OS Bookworm.
3. Configure hostname, Wi-Fi, SSH and locale before flashing.
4. Boot the Pi and SSH into it.

Update the base system:

```sh
sudo apt-get update
sudo apt-get -y upgrade
sudo reboot
```

## Install HyperPixel Support

Follow Pimoroni's current HyperPixel setup instructions for the exact display
revision. For a typical Bookworm install, start with:

```sh
sudo apt-get update
sudo apt-get install -y git curl python3-venv python3-pip xserver-xorg xinit openbox
```

Then install the HyperPixel overlay/support package from Pimoroni's documented
source for your model. After reboot, confirm:

- display output is 720x720
- touch input follows the display rotation
- the desktop or X session starts on the HyperPixel

If touch is rotated or mirrored, fix rotation at the OS/display layer before
debugging DJConnect.

## Create the Runtime User

```sh
sudo useradd --system --create-home --groups video,input,render djconnect
sudo mkdir -p /opt/djconnect/config /opt/djconnect/releases
sudo chown -R djconnect:djconnect /opt/djconnect
```

## Install the Client Manually

From a checkout:

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

For `/opt/djconnect` style installs, build a release bundle:

```sh
./scripts/build_release.sh 0.1.0
```

Extract it into `/opt/djconnect/releases/0.1.0`, create the `current` symlink
and install the systemd unit files.

## Enable systemd Services

Copy units:

```sh
sudo cp systemd/djconnect-*.service systemd/djconnect-*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable djconnect-client.service
sudo systemctl enable --now djconnect-updater.timer
sudo systemctl enable --now djconnect-maintenance.timer
```

Start the UI:

```sh
sudo systemctl start djconnect-client.service
```

Check logs:

```sh
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
  disable blanking.
- `Updates`: `stable` for normal GitHub releases, `beta` to allow prereleases.
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
